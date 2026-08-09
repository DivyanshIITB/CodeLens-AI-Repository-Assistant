from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.models.schemas import RepoImportRequest, RepoResponse
from backend.services.repo_service import RepoService

router = APIRouter(prefix="/repos", tags=["Repositories"])

@router.post("/import", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
async def import_repository_url(req: RepoImportRequest, db: AsyncSession = Depends(get_db)):
    if not req.url:
        raise HTTPException(status_code=400, detail="Repository URL is required.")
    service = RepoService(db)
    try:
        repo = await service.import_from_url(req.url)
        return RepoResponse(
            id=repo.id,
            name=repo.name,
            url=repo.url,
            path=repo.path,
            is_local=repo.is_local,
            status=repo.status,
            file_count=repo.file_count,
            total_loc=repo.total_loc,
            primary_language=repo.primary_language,
            error_message=repo.error_message,
            created_at=repo.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
async def upload_repository_zip(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip repository archives are supported.")
    service = RepoService(db)
    try:
        content = await file.read()
        repo = await service.import_from_zip(content, file.filename)
        return RepoResponse(
            id=repo.id,
            name=repo.name,
            url=repo.url,
            path=repo.path,
            is_local=repo.is_local,
            status=repo.status,
            file_count=repo.file_count,
            total_loc=repo.total_loc,
            primary_language=repo.primary_language,
            error_message=repo.error_message,
            created_at=repo.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[RepoResponse])
async def list_repositories(db: AsyncSession = Depends(get_db)):
    service = RepoService(db)
    repos = await service.list_repositories()
    return [
        RepoResponse(
            id=r.id,
            name=r.name,
            url=r.url,
            path=r.path,
            is_local=r.is_local,
            status=r.status,
            file_count=r.file_count,
            total_loc=r.total_loc,
            primary_language=r.primary_language,
            error_message=r.error_message,
            created_at=r.created_at.isoformat()
        )
        for r in repos
    ]

@router.get("/{repo_id}", response_model=RepoResponse)
async def get_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    service = RepoService(db)
    repo = await service.get_repository(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found.")
    return RepoResponse(
        id=repo.id,
        name=repo.name,
        url=repo.url,
        path=repo.path,
        is_local=repo.is_local,
        status=repo.status,
        file_count=repo.file_count,
        total_loc=repo.total_loc,
        primary_language=repo.primary_language,
        error_message=repo.error_message,
        created_at=repo.created_at.isoformat()
    )

@router.get("/{repo_id}/tree", response_model=List[Dict[str, Any]])
async def get_repository_tree(repo_id: str, db: AsyncSession = Depends(get_db)):
    service = RepoService(db)
    try:
        return await service.get_tree(repo_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{repo_id}/file")
async def read_repository_file(repo_id: str, path: str, db: AsyncSession = Depends(get_db)):
    service = RepoService(db)
    try:
        content = await service.read_file(repo_id, path)
        return {"file_path": path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{repo_id}")
async def delete_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    service = RepoService(db)
    success = await service.delete_repository(repo_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found.")
    return {"status": "deleted", "repo_id": repo_id}
