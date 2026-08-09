from typing import List, Dict, Any
from backend.config.settings import settings
from backend.config.logger import logger

class ContextCompressor:
    def __init__(self, max_tokens: int = settings.MAX_CONTEXT_TOKENS):
        self.max_tokens = max_tokens

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def compress_if_needed(self, chunks: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        total_estimated = sum(self.estimate_tokens(c["content"]) for c in chunks)
        token_budget = self.max_tokens - 800

        if total_estimated <= token_budget:
            return chunks

        logger.info(f"Context size ({total_estimated} tokens) exceeds budget ({token_budget} tokens). Compressing chunks.")

        compressed_chunks = []
        accumulated_tokens = 0

        for chunk in chunks:
            raw_code = chunk.get("content", "")
            est = self.estimate_tokens(raw_code)

            if accumulated_tokens + est <= token_budget:
                compressed_chunks.append(chunk)
                accumulated_tokens += est
            else:
                remaining_tokens = token_budget - accumulated_tokens
                if remaining_tokens > 100:
                    truncated_chars = remaining_tokens * 4
                    lines = raw_code.splitlines()
                    truncated_content = "\n".join(lines[:15]) + f"\n... [Truncated {len(lines)-15} lines due to context length limit] ..."
                    
                    chunk_copy = dict(chunk)
                    chunk_copy["content"] = truncated_content
                    compressed_chunks.append(chunk_copy)
                    accumulated_tokens += self.estimate_tokens(truncated_content)
                break

        return compressed_chunks

context_compressor = ContextCompressor()
