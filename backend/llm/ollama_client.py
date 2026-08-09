import json
import time
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional
from backend.config.settings import settings
from backend.config.logger import logger

class OllamaClient:
    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")

    async def list_models(self) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = data.get("models", [])
                    return [
                        {
                            "name": m.get("name"),
                            "size_human": f"{m.get('size', 0) / (1024**3):.1f} GB",
                            "parameter_size": m.get("details", {}).get("parameter_size", "N/A"),
                            "quantization": m.get("details", {}).get("quantization_level", "N/A"),
                            "status": "available"
                        }
                        for m in models
                    ]
        except Exception as e:
            logger.warning(f"Ollama server list_models error at {self.base_url}: {e}")
        return []

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                return res.status_code == 200
        except Exception:
            return False

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.2
    ) -> AsyncGenerator[str, None]:
        selected_model = model or settings.DEFAULT_LLM_MODEL
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_ctx": settings.MAX_CONTEXT_TOKENS
            }
        }

        start_time = time.time()
        token_count = 0

        try:
            timeout_config = httpx.Timeout(300.0, connect=10.0, read=300.0)
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        yield f"[Ollama Error {response.status_code}: Unable to generate response from model '{selected_model}']"
                        return

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                token = chunk.get("response", "")
                                if token:
                                    token_count += 1
                                    yield token
                                if chunk.get("done", False):
                                    duration = time.time() - start_time
                                    tps = token_count / duration if duration > 0 else 0
                                    logger.info(f"Ollama generation done: {token_count} tokens in {duration:.2f}s ({tps:.1f} t/s).")
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError:
            yield (
                "\n\n⚠️ **Ollama Local Service Unavailable**\n"
                "Unable to connect to Ollama at `http://localhost:11434`.\n"
                "Please make sure Ollama is running and you have pulled a local coding model:\n"
                "```bash\nollama pull qwen2.5-coder:1.5b\n```"
            )
        except Exception as e:
            logger.error(f"Error during Ollama stream: {e}")
            err_msg = str(e) if str(e) else repr(e)
            yield f"\n\n[Error generating AI response: {err_msg}]"


ollama_client = OllamaClient()
