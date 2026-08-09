import hashlib
import uuid
import time
from pathlib import Path
from typing import List, Dict, Tuple
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import settings
from backend.config.logger import logger
from backend.database.models import RepositoryDB, FileIndexDB, CodeChunkDB
from backend.parser.chunker import CodeChunker
from backend.embeddings.embedder import embedder
from backend.indexer.faiss_store import FAISSVectorStore

class IncrementalIndexer:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunker = CodeChunker()

    async def index_repository(self, repo_id: str, progress_callback=None) -> Tuple[int, int]:
        start_time = time.time()
        
        stmt = select(RepositoryDB).where(RepositoryDB.id == repo_id)
        res = await self.db.execute(stmt)
        repo = res.scalar_one_or_none()
        if not repo:
            raise ValueError(f"Repository {repo_id} not found.")

        repo_path = Path(repo.path)
        if not repo_path.exists():
            raise ValueError(f"Repository directory does not exist: {repo_path}")

        repo.status = "indexing"
        await self.db.commit()

        faiss_store = FAISSVectorStore(repo_id)

        stmt_files = select(FileIndexDB).where(FileIndexDB.repository_id == repo_id)
        existing_files_res = await self.db.execute(stmt_files)
        existing_files: Dict[str, FileIndexDB] = {
            f.relative_path: f for f in existing_files_res.scalars().all()
        }

        current_files: Dict[str, Tuple[Path, str, str]] = {}
        total_loc = 0

        for file_path in repo_path.rglob("*"):
            if file_path.is_file() and not any(part in settings.EXCLUDED_DIRS for part in file_path.parts):
                if file_path.suffix.lower() in settings.SUPPORTED_EXTENSIONS or file_path.name.lower() in ("dockerfile", "makefile"):
                    rel_path = file_path.relative_to(repo_path).as_posix()
                    try:
                        content_bytes = file_path.read_bytes()
                        sha256 = hashlib.sha256(content_bytes).hexdigest()
                        lang = self._detect_language(file_path)
                        
                        try:
                            lines_count = len(content_bytes.decode('utf-8', errors='ignore').splitlines())
                        except Exception:
                            lines_count = 0
                            
                        total_loc += lines_count
                        current_files[rel_path] = (file_path, sha256, lang)
                    except Exception as e:
                        logger.warning(f"Error reading file {file_path}: {e}")

        new_files = [rel for rel in current_files if rel not in existing_files]
        deleted_files = [rel for rel in existing_files if rel not in current_files]
        modified_files = [
            rel for rel in current_files
            if rel in existing_files and current_files[rel][1] != existing_files[rel].sha256_hash
        ]

        logger.info(
            f"Indexing summary for {repo.name}: "
            f"{len(new_files)} new, {len(modified_files)} modified, {len(deleted_files)} deleted."
        )

        files_to_purge = deleted_files + modified_files
        if files_to_purge:
            stmt_chunks = select(CodeChunkDB).where(
                CodeChunkDB.repository_id == repo_id,
                CodeChunkDB.file_path.in_(files_to_purge)
            )
            old_chunks_res = await self.db.execute(stmt_chunks)
            old_chunks = old_chunks_res.scalars().all()
            
            vector_ids_to_remove = [c.vector_id for c in old_chunks]
            if vector_ids_to_remove:
                faiss_store.remove_vectors(vector_ids_to_remove)
            
            await self.db.execute(
                delete(CodeChunkDB).where(
                    CodeChunkDB.repository_id == repo_id,
                    CodeChunkDB.file_path.in_(files_to_purge)
                )
            )
            await self.db.execute(
                delete(FileIndexDB).where(
                    FileIndexDB.repository_id == repo_id,
                    FileIndexDB.relative_path.in_(files_to_purge)
                )
            )
            await self.db.commit()

        files_to_process = new_files + modified_files
        processed_count = 0
        vector_id_counter = int(time.time() * 1000) % 1000000000

        for rel_path in files_to_process:
            file_path, sha256_hash, lang = current_files[rel_path]
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                chunks = self.chunker.create_chunks(
                    content=content,
                    file_path=rel_path,
                    language=lang,
                    repo_name=repo.name
                )

                if chunks:
                    texts = [c["content"] for c in chunks]
                    embeddings = embedder.embed_texts(texts)

                    vector_ids = []
                    db_chunk_objects = []

                    for idx, chunk in enumerate(chunks):
                        v_id = vector_id_counter + idx
                        vector_ids.append(v_id)

                        db_chunk_objects.append(CodeChunkDB(
                            id=str(uuid.uuid4()),
                            repository_id=repo_id,
                            file_path=rel_path,
                            chunk_type=chunk["chunk_type"],
                            name=chunk["name"],
                            start_line=chunk["start_line"],
                            end_line=chunk["end_line"],
                            parent_scope=chunk["parent_scope"],
                            content=chunk["content"],
                            vector_id=v_id
                        ))

                    vector_id_counter += len(chunks)

                    faiss_store.add_vectors(embeddings, vector_ids)
                    self.db.add_all(db_chunk_objects)

                lines_count = len(content.splitlines())
                self.db.add(FileIndexDB(
                    id=str(uuid.uuid4()),
                    repository_id=repo_id,
                    relative_path=rel_path,
                    sha256_hash=sha256_hash,
                    language=lang,
                    total_lines=lines_count,
                    size_bytes=len(content.encode("utf-8"))
                ))
                await self.db.commit()

                processed_count += 1
                if progress_callback:
                    await progress_callback(processed_count, len(files_to_process))

            except Exception as e:
                logger.error(f"Error processing file {rel_path}: {e}")

        repo.file_count = len(current_files)
        repo.total_loc = total_loc
        repo.primary_language = self._get_primary_language(current_files)
        repo.status = "ready"
        await self.db.commit()

        duration = time.time() - start_time
        logger.info(f"Indexing completed for {repo.name} in {duration:.2f}s.")
        return len(current_files), total_loc

    def _detect_language(self, path: Path) -> str:
        ext = path.suffix.lower()
        mapping = {
            ".py": "python", ".js": "javascript", ".jsx": "javascript", ".ts": "typescript",
            ".tsx": "typescript", ".java": "java", ".go": "go", ".rs": "rust", ".c": "c",
            ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".html": "html", ".css": "css",
            ".json": "json", ".md": "markdown", ".sql": "sql", ".sh": "bash", ".yml": "yaml",
            ".yaml": "yaml"
        }
        return mapping.get(ext, "code")

    def _get_primary_language(self, current_files: Dict[str, Tuple[Path, str, str]]) -> str:
        counts: Dict[str, int] = {}
        for _, _, lang in current_files.values():
            counts[lang] = counts.get(lang, 0) + 1
        if not counts:
            return "Unknown"
        return max(counts, key=counts.get)
