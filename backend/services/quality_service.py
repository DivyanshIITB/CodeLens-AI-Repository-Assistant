import re
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import CodeChunkDB
from backend.models.schemas import CodeSmellItem

class QualityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_code_smells(self, repo_id: str) -> List[CodeSmellItem]:
        stmt = select(CodeChunkDB).where(CodeChunkDB.repository_id == repo_id)
        res = await self.db.execute(stmt)
        chunks = res.scalars().all()

        smells: List[CodeSmellItem] = []

        for chunk in chunks:
            line_count = chunk.end_line - chunk.start_line + 1

            if chunk.chunk_type in ("function", "method") and line_count > 45:
                smells.append(CodeSmellItem(
                    file_path=chunk.file_path,
                    line_number=chunk.start_line,
                    smell_type="Long Function/Method",
                    severity="high" if line_count > 80 else "medium",
                    description=f"Function '{chunk.name or 'unnamed'}' spans {line_count} lines, exceeding recommended threshold (45 lines).",
                    recommendation="Consider breaking this function into smaller, single-responsibility helper functions."
                ))
            elif chunk.chunk_type == "class" and line_count > 250:
                smells.append(CodeSmellItem(
                    file_path=chunk.file_path,
                    line_number=chunk.start_line,
                    smell_type="Large Class (God Object)",
                    severity="high",
                    description=f"Class '{chunk.name or 'unnamed'}' spans {line_count} lines.",
                    recommendation="Refactor using composition or sub-modules to adhere to the Single Responsibility Principle."
                ))

            todo_matches = re.finditer(r'(TODO|FIXME|HACK|XXX):?\s*(.*)', chunk.content, re.IGNORECASE)
            for m in todo_matches:
                tag = m.group(1).upper()
                text = m.group(2).strip()
                smells.append(CodeSmellItem(
                    file_path=chunk.file_path,
                    line_number=chunk.start_line,
                    smell_type=f"Pending {tag} Comment",
                    severity="low",
                    description=f"Unresolved {tag}: {text[:60]}",
                    recommendation="Address or track this pending technical debt in your issue tracker."
                ))

            if chunk.chunk_type in ("function", "class", "method") and chunk.name and not chunk.name.startswith("_"):
                if '"""' not in chunk.content and "/*" not in chunk.content and "//" not in chunk.content[:150]:
                    smells.append(CodeSmellItem(
                        file_path=chunk.file_path,
                        line_number=chunk.start_line,
                        smell_type="Missing Documentation",
                        severity="low",
                        description=f"Public {chunk.chunk_type} '{chunk.name}' lacks a docstring or explanatory block comment.",
                        recommendation="Add clear docstring explaining arguments, return types, and exceptions."
                    ))

        return smells[:60]
