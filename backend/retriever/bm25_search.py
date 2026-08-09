import re
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import CodeChunkDB

class BM25SearchEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r'\w+', text.lower())
        return [t for t in tokens if len(t) > 1]

    async def search(self, repo_id: str, query: str, top_k: int = 10) -> List[Tuple[CodeChunkDB, float]]:
        stmt = select(CodeChunkDB).where(CodeChunkDB.repository_id == repo_id)
        res = await self.db.execute(stmt)
        chunks = res.scalars().all()

        if not chunks:
            return []

        corpus = [self._tokenize(chunk.content) for chunk in chunks]
        tokenized_query = self._tokenize(query)

        if not tokenized_query or not corpus:
            return []

        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(tokenized_query)

        chunk_scores = list(zip(chunks, scores))
        chunk_scores.sort(key=lambda x: x[1], reverse=True)

        return chunk_scores[:top_k]
