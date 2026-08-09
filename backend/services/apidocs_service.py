import re
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import CodeChunkDB
from backend.models.schemas import ApiDocItem

class ApiDocsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_api_docs(self, repo_id: str) -> List[ApiDocItem]:
        stmt = select(CodeChunkDB).where(CodeChunkDB.repository_id == repo_id)
        res = await self.db.execute(stmt)
        chunks = res.scalars().all()

        api_docs: List[ApiDocItem] = []
        route_patterns = [
            (r'@(?:router|app)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', "python/js"),
            (r'(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', "js"),
            (r'@(Get|Post|Put|Delete|Patch)Mapping\(\s*["\']([^"\']+)["\']', "java"),
            (r'path\(\s*["\']([^"\']+)["\']', "django")
        ]

        for chunk in chunks:
            content = chunk.content
            for pattern, lang_type in route_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for m in matches:
                    method = m.group(1).upper()
                    endpoint = m.group(2)
                    if not endpoint.startswith("/"):
                        endpoint = "/" + endpoint

                    params = []
                    lines = content.splitlines()
                    for line in lines:
                        if "def " in line or "function" in line or "async def" in line:
                            param_match = re.search(r'\((.*?)\)', line)
                            if param_match:
                                raw_params = param_match.group(1).split(",")
                                params = [p.strip() for p in raw_params if p.strip() and p.strip() != "self"]

                    summary = f"{method} endpoint for {endpoint} handled in {chunk.name or 'route handler'}"
                    
                    api_docs.append(ApiDocItem(
                        endpoint=endpoint,
                        method=method,
                        file_path=chunk.file_path,
                        start_line=chunk.start_line,
                        parameters=params[:5],
                        summary=summary,
                        response_type="JSON Response"
                    ))

        unique_docs = {}
        for item in api_docs:
            key = f"{item.method}:{item.endpoint}"
            if key not in unique_docs:
                unique_docs[key] = item

        return list(unique_docs.values())
