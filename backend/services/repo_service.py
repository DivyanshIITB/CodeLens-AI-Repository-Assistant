import uuid
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import settings
from backend.config.logger import logger
from backend.database.models import RepositoryDB, FileIndexDB, CodeChunkDB
from backend.indexer.incremental_indexer import IncrementalIndexer
from backend.indexer.faiss_store import FAISSVectorStore
from backend.utils.cloner import RepoCloner
from backend.utils.file_utils import build_file_tree, get_file_content

class RepoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.indexer = IncrementalIndexer(db)

    async def import_from_url(self, repo_url: str) -> RepositoryDB:
        clean_url = repo_url.rstrip("/").removesuffix(".git")
        repo_name = clean_url.split("/")[-1]

        # Check if repository URL was already imported before
        stmt_existing = select(RepositoryDB).where(RepositoryDB.url == repo_url)
        res_existing = await self.db.execute(stmt_existing)
        existing = res_existing.scalars().first()


        if existing and Path(existing.path).exists():
            logger.info(f"Repository {repo_name} already exists ({existing.id}). Running fast SHA-256 incremental check...")
            await self.indexer.index_repository(existing.id)
            await self.db.refresh(existing)
            return existing

        repo_id = str(uuid.uuid4())[:8]
        target_dir = settings.REPOS_DIR / f"{repo_name}_{repo_id}"

        repo_db = RepositoryDB(
            id=repo_id,
            name=repo_name,
            url=repo_url,
            path=str(target_dir),
            is_local=False,
            status="cloning"
        )
        self.db.add(repo_db)
        await self.db.commit()

        try:
            RepoCloner.clone_or_download(repo_url, target_dir)
            await self.indexer.index_repository(repo_id)
            await self.db.refresh(repo_db)
            return repo_db
        except Exception as e:
            repo_db.status = "error"
            repo_db.error_message = str(e)
            await self.db.commit()
            logger.error(f"Failed importing repository from URL {repo_url}: {e}")
            raise e


    async def import_from_zip(self, zip_bytes: bytes, filename: str) -> RepositoryDB:
        clean_name = Path(filename).stem
        repo_id = str(uuid.uuid4())[:8]
        target_dir = settings.REPOS_DIR / f"{clean_name}_{repo_id}"

        repo_db = RepositoryDB(
            id=repo_id,
            name=clean_name,
            url=None,
            path=str(target_dir),
            is_local=True,
            status="extracting"
        )
        self.db.add(repo_db)
        await self.db.commit()

        try:
            RepoCloner.extract_zip(zip_bytes, target_dir)
            await self.indexer.index_repository(repo_id)
            await self.db.refresh(repo_db)
            return repo_db
        except Exception as e:
            repo_db.status = "error"
            repo_db.error_message = str(e)
            await self.db.commit()
            logger.error(f"Failed importing repository from uploaded zip {filename}: {e}")
            raise e

    async def list_repositories(self) -> List[RepositoryDB]:
        stmt = select(RepositoryDB).order_by(RepositoryDB.created_at.desc())
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_repository(self, repo_id: str) -> Optional[RepositoryDB]:
        stmt = select(RepositoryDB).where(RepositoryDB.id == repo_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_tree(self, repo_id: str) -> List[Dict[str, Any]]:
        repo = await self.get_repository(repo_id)
        if not repo:
            raise ValueError(f"Repository {repo_id} not found.")
        return build_file_tree(Path(repo.path))

    async def read_file(self, repo_id: str, relative_path: str) -> str:
        repo = await self.get_repository(repo_id)
        if not repo:
            raise ValueError(f"Repository {repo_id} not found.")
        return get_file_content(Path(repo.path), relative_path)

    async def delete_repository(self, repo_id: str) -> bool:
        repo = await self.get_repository(repo_id)
        if not repo:
            return False

        faiss_store = FAISSVectorStore(repo_id)
        faiss_store.delete_index()

        repo_path = Path(repo.path)
        if repo_path.exists():
            shutil.rmtree(repo_path, ignore_errors=True)

        await self.db.execute(delete(CodeChunkDB).where(CodeChunkDB.repository_id == repo_id))
        await self.db.execute(delete(FileIndexDB).where(FileIndexDB.repository_id == repo_id))
        await self.db.execute(delete(RepositoryDB).where(RepositoryDB.id == repo_id))
        await self.db.commit()
        return True
