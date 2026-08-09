import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.retriever.hybrid_retriever import HybridRetriever
from backend.llm.ollama_client import ollama_client
from backend.llm.prompt_builder import SYSTEM_RAG_PROMPT, build_rag_prompt

async def run_evaluation_suite(db: AsyncSession, repo_id: str, sample_size: int = 15) -> Dict[str, Any]:
    dataset_path = Path(__file__).parent / "eval_dataset.json"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        questions: List[Dict[str, Any]] = json.load(f)

    subset = questions[:sample_size]
    retriever = HybridRetriever(db)

    total_queries = len(subset)
    hit_count = 0
    citation_count = 0
    total_latency_ms = 0.0
    successful_generations = 0

    results_detail = []

    for item in subset:
        q_id = item["id"]
        query = item["query"]
        expected_kws = item.get("expected_keywords", [])

        start_t = time.time()
        retrieved = await retriever.search(repo_id=repo_id, query=query, top_k=5)
        retrieval_ms = (time.time() - start_t) * 1000

        hit = False
        retrieved_text = " ".join([c["content"].lower() for c in retrieved])
        if any(kw in retrieved_text for kw in expected_kws):
            hit = True
            hit_count += 1

        answer = ""
        has_citation = False
        if retrieved and await ollama_client.check_health():
            prompt = build_rag_prompt(query=query, retrieved_chunks=retrieved)
            gen_start = time.time()
            async for token in ollama_client.generate_stream(
                prompt=prompt,
                system_prompt=SYSTEM_RAG_PROMPT,
                temperature=0.2
            ):
                answer += token
            
            gen_ms = (time.time() - gen_start) * 1000
            total_latency_ms += (retrieval_ms + gen_ms)
            successful_generations += 1

            if ":" in answer and ("Lines" in answer or "lines" in answer or ".py" in answer or ".js" in answer):
                has_citation = True
                citation_count += 1
        else:
            total_latency_ms += retrieval_ms

        results_detail.append({
            "id": q_id,
            "query": query,
            "retrieved_count": len(retrieved),
            "retrieval_hit": hit,
            "has_citation": has_citation,
            "latency_ms": round(retrieval_ms, 1)
        })

    retrieval_accuracy = (hit_count / total_queries) * 100 if total_queries > 0 else 0
    citation_accuracy = (citation_count / max(1, successful_generations)) * 100
    avg_latency_ms = total_latency_ms / max(1, total_queries)

    return {
        "repo_id": repo_id,
        "total_eval_queries": total_queries,
        "retrieval_hit_rate": round(retrieval_accuracy, 1),
        "citation_accuracy": round(citation_accuracy, 1),
        "avg_latency_ms": round(avg_latency_ms, 1),
        "success_rate": round((successful_generations / max(1, total_queries)) * 100, 1),
        "details": results_detail
    }
