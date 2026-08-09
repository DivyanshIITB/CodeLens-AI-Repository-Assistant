from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database.db import get_db
from backend.database.models import RepositoryDB, FileIndexDB
from backend.models.schemas import (
    OverviewResponse, ReadmeResponse, ApiDocItem, OnboardingResponse,
    DependencyGraphResponse, CodeSmellItem, StatsResponse
)
from backend.services.overview_service import OverviewService
from backend.services.readme_generator import ReadmeGeneratorService
from backend.services.apidocs_service import ApiDocsService
from backend.services.onboarding_service import OnboardingService
from backend.services.graph_service import GraphService
from backend.services.quality_service import QualityService

router = APIRouter(prefix="/analysis", tags=["Repository Analysis"])

@router.get("/{repo_id}/overview", response_model=OverviewResponse)
async def get_overview(repo_id: str, db: AsyncSession = Depends(get_db)):
    service = OverviewService(db)
    try:
        return await service.get_overview(repo_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{repo_id}/readme", response_model=ReadmeResponse)
async def generate_readme(repo_id: str, db: AsyncSession = Depends(get_db)):
    service = ReadmeGeneratorService(db)
    try:
        return await service.generate_readme(repo_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{repo_id}/apidocs", response_model=List[ApiDocItem])
async def get_api_docs(repo_id: str, db: AsyncSession = Depends(get_db)):
    service = ApiDocsService(db)
    try:
        return await service.generate_api_docs(repo_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{repo_id}/onboarding", response_model=OnboardingResponse)
async def get_onboarding_guide(repo_id: str, db: AsyncSession = Depends(get_db)):
    service = OnboardingService(db)
    try:
        return await service.generate_onboarding_guide(repo_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{repo_id}/graph", response_model=DependencyGraphResponse)
async def get_dependency_graph(repo_id: str, db: AsyncSession = Depends(get_db)):
    service = GraphService(db)
    try:
        return await service.generate_dependency_graph(repo_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{repo_id}/quality", response_model=List[CodeSmellItem])
async def analyze_quality(repo_id: str, db: AsyncSession = Depends(get_db)):
    service = QualityService(db)
    try:
        return await service.analyze_code_smells(repo_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{repo_id}/stats", response_model=StatsResponse)
async def get_statistics(repo_id: str, db: AsyncSession = Depends(get_db)):
    stmt_repo = select(RepositoryDB).where(RepositoryDB.id == repo_id)
    repo_res = await db.execute(stmt_repo)
    repo = repo_res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found.")

    stmt_files = select(FileIndexDB).where(FileIndexDB.repository_id == repo_id).order_by(FileIndexDB.total_lines.desc())
    files_res = await db.execute(stmt_files)
    files = files_res.scalars().all()

    languages = {}
    largest_files = []
    total_loc = 0

    for f in files:
        languages[f.language] = languages.get(f.language, 0) + 1
        total_loc += f.total_lines
        if len(largest_files) < 5:
            largest_files.append({
                "path": f.relative_path,
                "lines": f.total_lines,
                "size_kb": round(f.size_bytes / 1024, 1)
            })

    avg_file_size = total_loc / max(1, len(files))

    return StatsResponse(
        repo_id=repo_id,
        total_files=len(files),
        total_loc=total_loc,
        avg_file_size_loc=round(avg_file_size, 1),
        languages=languages,
        largest_files=largest_files,
        most_connected_modules=largest_files[:3]
    )
