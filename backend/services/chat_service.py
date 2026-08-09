import re
import json
import time
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import settings
from backend.config.logger import logger
from backend.retriever.hybrid_retriever import HybridRetriever
from backend.llm.ollama_client import ollama_client
from backend.llm.prompt_builder import SYSTEM_RAG_PROMPT, build_rag_prompt
from backend.llm.context_compressor import context_compressor

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retriever = HybridRetriever(db)

    def _calculate_confidence(self, query: str, chunks: List[Dict[str, Any]]) -> Tuple[int, str]:
        if not chunks:
            return 0, "Low"

        avg_score = sum(c.get("score", 0.0) for c in chunks) / len(chunks)
        rrf_norm = min(1.0, avg_score / 0.025)

        stopwords = {"the", "a", "an", "is", "where", "how", "what", "can", "you", "list", "all", "in", "to", "for", "on", "of", "and"}
        query_words = set(re.findall(r'\w+', query.lower())) - stopwords

        if not query_words:
            density = 0.5
        else:
            found_count = 0
            all_content = " ".join([c.get("content", "").lower() for c in chunks])
            for qw in query_words:
                if qw in all_content:
                    found_count += 1
            density = found_count / len(query_words)

        raw_score = int(round((0.6 * rrf_norm + 0.4 * density) * 100))
        confidence_score = max(15, min(98, raw_score))

        if confidence_score >= 80:
            level = "High"
        elif confidence_score >= 60:
            level = "Moderate"
        else:
            level = "Low"

        return confidence_score, level

    async def stream_chat(
        self,
        repo_id: str,
        message: str,
        model: Optional[str] = None,
        top_k: int = settings.DEFAULT_TOP_K,
        temperature: float = settings.DEFAULT_TEMPERATURE
    ) -> AsyncGenerator[str, None]:
        start_time = time.time()

        chunks = await self.retriever.search(repo_id=repo_id, query=message, top_k=top_k)

        compressed_chunks = context_compressor.compress_if_needed(chunks, message)

        confidence_score, confidence_level = self._calculate_confidence(message, compressed_chunks)

        citations = []
        for c in compressed_chunks:
            snippet_lines = c["content"].splitlines()
            code_snippet = "\n".join(snippet_lines[:10]) if len(snippet_lines) > 10 else c["content"]
            citations.append({
                "file_path": c["file_path"],
                "start_line": c["start_line"],
                "end_line": c["end_line"],
                "chunk_type": c["chunk_type"],
                "name": c.get("name"),
                "parent_scope": c.get("parent_scope"),
                "snippet": code_snippet,
                "score": c.get("score", 0.0)
            })

        meta_event = {
            "event": "metadata",
            "citations": citations,
            "chunk_count": len(compressed_chunks),
            "confidence_score": confidence_score,
            "confidence_level": confidence_level
        }
        yield f"data: {json.dumps(meta_event)}\n\n"

        if not compressed_chunks:
            no_ctx_msg = (
                "Based on the retrieved repository code, no relevant code chunks were found for your query. "
                "Please make sure the repository is fully indexed or try rephrasing your search terms."
            )
            yield f"data: {json.dumps({'event': 'token', 'token': no_ctx_msg})}\n\n"
            yield f"data: {json.dumps({'event': 'done', 'duration_ms': (time.time() - start_time) * 1000})}\n\n"
            return

        prompt = build_rag_prompt(query=message, retrieved_chunks=compressed_chunks)

        selected_model = model or settings.DEFAULT_LLM_MODEL
        async for token in ollama_client.generate_stream(
            prompt=prompt,
            system_prompt=SYSTEM_RAG_PROMPT,
            model=selected_model,
            temperature=temperature
        ):
            token_event = {"event": "token", "token": token}
            yield f"data: {json.dumps(token_event)}\n\n"

        duration_ms = (time.time() - start_time) * 1000
        done_event = {"event": "done", "duration_ms": duration_ms}
        yield f"data: {json.dumps(done_event)}\n\n"
