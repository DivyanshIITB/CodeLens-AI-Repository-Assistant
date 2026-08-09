import time
from typing import List, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import settings
from backend.config.logger import logger
from backend.database.models import CodeChunkDB
from backend.embeddings.embedder import embedder
from backend.indexer.faiss_store import FAISSVectorStore
from backend.retriever.bm25_search import BM25SearchEngine

class HybridRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bm25_engine = BM25SearchEngine(db)

    async def search(
        self,
        repo_id: str,
        query: str,
        top_k: int = settings.DEFAULT_TOP_K,
        rrf_k: int = settings.RRF_K
    ) -> List[Dict[str, Any]]:
        start_time = time.time()

        faiss_store = FAISSVectorStore(repo_id)
        query_vector = embedder.embed_query(query)
        faiss_results = faiss_store.search(query_vector, top_k=top_k * 2)

        faiss_ranks: Dict[int, int] = {}
        for rank, (vec_id, _) in enumerate(faiss_results, 1):
            faiss_ranks[vec_id] = rank

        faiss_vec_ids = list(faiss_ranks.keys())
        faiss_chunks: Dict[int, CodeChunkDB] = {}
        if faiss_vec_ids:
            stmt = select(CodeChunkDB).where(
                CodeChunkDB.repository_id == repo_id,
                CodeChunkDB.vector_id.in_(faiss_vec_ids)
            )
            res = await self.db.execute(stmt)
            for chunk in res.scalars().all():
                faiss_chunks[chunk.vector_id] = chunk

        bm25_results = await self.bm25_engine.search(repo_id, query, top_k=top_k * 2)
        bm25_ranks: Dict[str, Tuple[CodeChunkDB, int]] = {}
        for rank, (chunk, score) in enumerate(bm25_results, 1):
            if score > 0:
                bm25_ranks[chunk.id] = (chunk, rank)

        rrf_scores: Dict[str, float] = {}
        chunks_map: Dict[str, CodeChunkDB] = {}

        for vec_id, rank in faiss_ranks.items():
            if vec_id in faiss_chunks:
                chunk = faiss_chunks[vec_id]
                chunks_map[chunk.id] = chunk
                rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (rrf_k + rank))

        for chunk_id, (chunk, rank) in bm25_ranks.items():
            chunks_map[chunk.id] = chunk
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (rrf_k + rank))

        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda c_id: rrf_scores[c_id], reverse=True)
        top_chunk_ids = sorted_chunk_ids[:top_k]

        results = []
        for c_id in top_chunk_ids:
            chunk = chunks_map[c_id]
            results.append({
                "chunk": chunk,
                "score": round(rrf_scores[c_id], 4),
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name,
                "parent_scope": chunk.parent_scope,
                "content": chunk.content
            })

        duration = (time.time() - start_time) * 1000
        logger.info(f"Hybrid search for query '{query[:30]}...' returned {len(results)} chunks in {duration:.1f}ms.")
        return results
