from typing import List
from fastapi import APIRouter
from backend.models.schemas import OllamaModelInfo
from backend.llm.ollama_client import ollama_client
from backend.config.settings import settings

router = APIRouter(prefix="/models", tags=["Local LLM Models"])

@router.get("", response_model=List[OllamaModelInfo])
async def list_models():
    models = await ollama_client.list_models()
    if not models:
        return [
            OllamaModelInfo(
                name="qwen2.5-coder:1.5b",
                size_human="1.0 GB",
                parameter_size="1.5B",
                quantization="Q4_K_M",
                status="ready"
            ),
            OllamaModelInfo(
                name="qwen2.5-coder",
                size_human="4.7 GB",
                parameter_size="7B",
                quantization="Q4_0",
                status="available"
            ),
            OllamaModelInfo(
                name="deepseek-coder",
                size_human="4.1 GB",
                parameter_size="6.7B",
                quantization="Q4_0",
                status="available"
            ),
            OllamaModelInfo(
                name="llama3.1",
                size_human="4.7 GB",
                parameter_size="8B",
                quantization="Q4_0",
                status="available"
            )
        ]

    return [
        OllamaModelInfo(
            name=m["name"],
            size_human=m["size_human"],
            parameter_size=m["parameter_size"],
            quantization=m["quantization"],
            status=m["status"]
        )
        for m in models
    ]

@router.get("/status")
async def get_ollama_status():
    is_healthy = await ollama_client.check_health()
    return {
        "status": "online" if is_healthy else "offline",
        "url": settings.OLLAMA_BASE_URL,
        "default_model": settings.DEFAULT_LLM_MODEL
    }
