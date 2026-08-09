from fastapi import APIRouter
from backend.models.schemas import SettingsSchema
from backend.config.settings import settings

router = APIRouter(prefix="/settings", tags=["Application Settings"])

current_settings = SettingsSchema(
    default_model=settings.DEFAULT_LLM_MODEL,
    embedding_model=settings.EMBEDDING_MODEL,
    top_k=settings.DEFAULT_TOP_K,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
    chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP,
    temperature=settings.DEFAULT_TEMPERATURE,
    theme="github-dark"
)

@router.get("", response_model=SettingsSchema)
async def get_settings():
    return current_settings

@router.post("", response_model=SettingsSchema)
async def update_settings(new_settings: SettingsSchema):
    global current_settings
    current_settings = new_settings
    settings.DEFAULT_LLM_MODEL = new_settings.default_model
    settings.DEFAULT_TOP_K = new_settings.top_k
    settings.DEFAULT_CHUNK_SIZE = new_settings.chunk_size
    settings.DEFAULT_CHUNK_OVERLAP = new_settings.chunk_overlap
    settings.DEFAULT_TEMPERATURE = new_settings.temperature
    return current_settings
