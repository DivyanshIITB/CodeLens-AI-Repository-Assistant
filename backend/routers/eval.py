from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import get_db
from backend.evaluation.run_eval import run_evaluation_suite

router = APIRouter(prefix="/eval", tags=["Evaluation Benchmark"])

@router.post("/{repo_id}", response_model=Dict[str, Any])
async def run_benchmark(repo_id: str, sample_size: int = 10, db: AsyncSession = Depends(get_db)):
    try:
        results = await run_evaluation_suite(db, repo_id, sample_size=sample_size)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
