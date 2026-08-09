from typing import List
from backend.parser.ast_parser import ASTParser, RawChunk
from backend.config.settings import settings

class CodeChunker:
    def __init__(self):
        self.parser = ASTParser()

    def create_chunks(
        self,
        content: str,
        file_path: str,
        language: str,
        repo_name: str,
        chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = settings.DEFAULT_CHUNK_OVERLAP
    ) -> List[dict]:
        raw_chunks = self.parser.parse_file(content, file_path, language)
        final_chunks: List[dict] = []

        if not raw_chunks:
            raw_chunks = [RawChunk(
                chunk_type="file",
                name=file_path.split("/")[-1],
                start_line=1,
                end_line=len(content.splitlines()),
                parent_scope=None,
                content=content
            )]

        for raw in raw_chunks:
            sub_blocks = self._split_if_oversized(raw.content, chunk_size, chunk_overlap)
            
            line_offset = 0
            for idx, block in enumerate(sub_blocks):
                block_lines = len(block.splitlines())
                start_l = raw.start_line + line_offset
                end_l = min(raw.end_line, start_l + block_lines - 1)
                line_offset += max(1, block_lines - (chunk_overlap // 10))

                header = (
                    f"// Repository: {repo_name}\n"
                    f"// File: {file_path}\n"
                    f"// Language: {language}\n"
                    f"// Type: {raw.chunk_type.upper()}\n"
                )
                if raw.name:
                    header += f"// Name: {raw.name}\n"
                if raw.parent_scope:
                    header += f"// Parent Scope: {raw.parent_scope}\n"
                header += f"// Lines: {start_l}-{end_l}\n\n"

                enriched_content = header + block

                final_chunks.append({
                    "file_path": file_path,
                    "chunk_type": raw.chunk_type,
                    "name": raw.name or file_path.split("/")[-1],
                    "start_line": start_l,
                    "end_line": end_l,
                    "parent_scope": raw.parent_scope,
                    "content": enriched_content,
                    "raw_code": block,
                    "language": language
                })

        return final_chunks

    def _split_if_oversized(self, content: str, max_chars: int, overlap_chars: int) -> List[str]:
        limit = max_chars * 4
        if len(content) <= limit:
            return [content]

        lines = content.splitlines(keepends=True)
        chunks = []
        current = ""

        for line in lines:
            if len(current) + len(line) > limit and current:
                chunks.append(current)
                overlap_lines = current.splitlines(keepends=True)[-5:]
                current = "".join(overlap_lines) + line
            else:
                current += line

        if current.strip():
            chunks.append(current)

        return chunks
