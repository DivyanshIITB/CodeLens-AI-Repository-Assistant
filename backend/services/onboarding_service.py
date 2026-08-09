from typing import List, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import RepositoryDB, FileIndexDB
from backend.models.schemas import OnboardingResponse

class OnboardingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_onboarding_guide(self, repo_id: str) -> OnboardingResponse:
        stmt = select(RepositoryDB).where(RepositoryDB.id == repo_id)
        res = await self.db.execute(stmt)
        repo = res.scalar_one_or_none()
        if not repo:
            raise ValueError(f"Repository {repo_id} not found.")

        stmt_files = select(FileIndexDB).where(FileIndexDB.repository_id == repo_id)
        files_res = await self.db.execute(stmt_files)
        files = files_res.scalars().all()
        file_paths = [f.relative_path for f in files]

        entry_points = []
        config_files = []
        core_files = []

        for fp in file_paths:
            fp_lower = fp.lower()
            if any(k in fp_lower for k in ("main.", "app.", "index.", "server.", "manage.py")):
                entry_points.append(fp)
            elif any(k in fp_lower for k in ("config", "settings", "env", "docker", "package.json", "requirements")):
                config_files.append(fp)
            elif any(k in fp_lower for k in ("service", "controller", "model", "router", "api", "component", "store")):
                core_files.append(fp)

        reading_order = config_files[:3] + entry_points[:3] + core_files[:6]

        learning_roadmap = [
            {
                "step": "1. Configuration & Dependencies",
                "description": f"Review config files ({', '.join(config_files[:2]) or 'environment files'}) to understand dependencies and environment variables."
            },
            {
                "step": "2. Application Entry Points",
                "description": f"Examine entry points ({', '.join(entry_points[:2]) or 'main startup script'}) to trace application boot and route registration."
            },
            {
                "step": "3. Data Models & State",
                "description": "Understand core domain models, database schemas, and state management flow."
            },
            {
                "step": "4. Business Logic & Controllers",
                "description": "Explore services and business logic handlers responsible for key workflows."
            },
            {
                "step": "5. API Endpoints & UI Components",
                "description": "Inspect API routing and frontend user interface views."
            }
        ]

        core_modules = [
            {"module": "Entry Points", "files": ", ".join(entry_points[:3]) or "Main script"},
            {"module": "Configurations", "files": ", ".join(config_files[:3]) or "Settings module"},
            {"module": "Core Components", "files": ", ".join(core_files[:5]) or "Core modules"}
        ]

        return OnboardingResponse(
            learning_roadmap=learning_roadmap,
            recommended_reading_order=reading_order,
            core_modules=core_modules,
            entry_points=entry_points
        )
