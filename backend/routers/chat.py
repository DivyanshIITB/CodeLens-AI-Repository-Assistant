from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.models.schemas import ChatRequest
from backend.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["AI Chat Engine"])

@router.post("/stream")
async def stream_rag_chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    service = ChatService(db)
    event_generator = service.stream_chat(
        repo_id=req.repo_id,
        message=req.message,
        model=req.model,
        top_k=req.top_k or 6,
        temperature=req.temperature or 0.2
    )
    return StreamingResponse(event_generator, media_type="text/event-stream")
