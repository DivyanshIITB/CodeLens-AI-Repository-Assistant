from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import RepositoryDB, FileIndexDB
from backend.models.schemas import OverviewResponse
from backend.llm.ollama_client import ollama_client

class OverviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, repo_id: str) -> OverviewResponse:
        stmt = select(RepositoryDB).where(RepositoryDB.id == repo_id)
        res = await self.db.execute(stmt)
        repo = res.scalar_one_or_none()
        if not repo:
            raise ValueError(f"Repository {repo_id} not found.")

        stmt_files = select(FileIndexDB).where(FileIndexDB.repository_id == repo_id)
        files_res = await self.db.execute(stmt_files)
        files = files_res.scalars().all()

        languages: Dict[str, int] = {}
        file_paths = [f.relative_path for f in files]

        for f in files:
            languages[f.language] = languages.get(f.language, 0) + 1

        tech_stack = set()
        frameworks = set()
        databases = set()
        package_managers = set()
        external_apis = set()

        for fp in file_paths:
            fp_lower = fp.lower()
            if "package.json" in fp_lower:
                package_managers.add("npm / yarn / pnpm")
                tech_stack.add("Node.js")
            if "requirements.txt" in fp_lower or "pyproject.toml" in fp_lower:
                package_managers.add("pip / poetry")
                tech_stack.add("Python")
            if "cargo.toml" in fp_lower:
                package_managers.add("cargo")
                tech_stack.add("Rust")
            if "go.mod" in fp_lower:
                package_managers.add("go modules")
                tech_stack.add("Go")
            if "pom.xml" in fp_lower or "build.gradle" in fp_lower:
                package_managers.add("maven / gradle")
                tech_stack.add("Java")
            if "dockerfile" in fp_lower or "docker-compose" in fp_lower:
                tech_stack.add("Docker")
            
            if "react" in fp_lower or "vite" in fp_lower or "next" in fp_lower:
                frameworks.add("React")
            if "fastapi" in fp_lower:
                frameworks.add("FastAPI")
            if "django" in fp_lower:
                frameworks.add("Django")
            if "express" in fp_lower:
                frameworks.add("Express.js")
            if "spring" in fp_lower:
                frameworks.add("Spring Boot")
            if "sqlite" in fp_lower or "codelens.db" in fp_lower:
                databases.add("SQLite")
            if "postgres" in fp_lower or "psycopg" in fp_lower:
                databases.add("PostgreSQL")
            if "mongo" in fp_lower:
                databases.add("MongoDB")
            if "faiss" in fp_lower or "pinecone" in fp_lower or "chroma" in fp_lower:
                databases.add("FAISS Vector Database")
            if "stripe" in fp_lower:
                external_apis.add("Stripe API")
            if "github" in fp_lower or "octokit" in fp_lower:
                external_apis.add("GitHub API")

        top_files_str = "\n".join(file_paths[:30])
        prompt = (
            f"Repository Name: {repo.name}\n"
            f"Primary Language: {repo.primary_language}\n"
            f"File Count: {repo.file_count}, Total LOC: {repo.total_loc}\n"
            f"Detected Tech Stack: {', '.join(tech_stack) if tech_stack else 'Standard Project'}\n"
            f"Files Sample:\n{top_files_str}\n\n"
            f"Task: Provide a 3-paragraph high-level software architectural summary of this repository, "
            f"describing its purpose, architecture design, and component responsibilities."
        )

        arch_summary = ""
        try:
            if await ollama_client.check_health():
                async for token in ollama_client.generate_stream(
                    prompt=prompt,
                    system_prompt="You are an expert software architect. Be clear and technical.",
                    temperature=0.2
                ):
                    arch_summary += token
        except Exception:
            pass

        if not arch_summary.strip():
            arch_summary = (
                f"{repo.name} is a {repo.primary_language or 'multi-language'} codebase comprising {repo.file_count} files "
                f"and {repo.total_loc} lines of code. It follows a modular project structure using {', '.join(tech_stack) or 'standard conventions'}."
            )

        return OverviewResponse(
            repo_name=repo.name,
            languages=languages,
            total_files=repo.file_count,
            total_loc=repo.total_loc,
            tech_stack=list(tech_stack),
            frameworks=list(frameworks),
            databases=list(databases),
            package_managers=list(package_managers),
            external_apis=list(external_apis),
            architectural_summary=arch_summary
        )
