from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import RepositoryDB, FileIndexDB
from backend.models.schemas import ReadmeResponse
from backend.llm.ollama_client import ollama_client

class ReadmeGeneratorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_readme(self, repo_id: str) -> ReadmeResponse:
        stmt = select(RepositoryDB).where(RepositoryDB.id == repo_id)
        res = await self.db.execute(stmt)
        repo = res.scalar_one_or_none()
        if not repo:
            raise ValueError(f"Repository {repo_id} not found.")

        stmt_files = select(FileIndexDB).where(FileIndexDB.repository_id == repo_id)
        files_res = await self.db.execute(stmt_files)
        files = files_res.scalars().all()
        file_tree_sample = [f.relative_path for f in files[:40]]
        tree_str = "\n".join(file_tree_sample)

        prompt = (
            f"Generate a professional, production-grade README.md for repository '{repo.name}'.\n"
            f"Primary Language: {repo.primary_language}\n"
            f"Files Count: {repo.file_count}\n"
            f"Key Files:\n{tree_str}\n\n"
            f"Include the following sections:\n"
            f"# {repo.name}\n"
            f"## Overview\n"
            f"## Features\n"
            f"## Tech Stack\n"
            f"## Folder Structure\n"
            f"## Installation & Setup\n"
            f"## Usage\n"
            f"## Contributing\n"
            f"## License\n"
        )

        content = ""
        try:
            if await ollama_client.check_health():
                async for token in ollama_client.generate_stream(
                    prompt=prompt,
                    system_prompt="You are a professional open-source documentation technical writer. Write clean, complete Markdown.",
                    temperature=0.2
                ):
                    content += token
        except Exception:
            pass

        if not content.strip():
            sample_str = "\n".join(file_tree_sample[:15])
            content = f"""# {repo.name}

AI-analyzed repository codebase built primarily with **{repo.primary_language}**.

## Overview
{repo.name} contains {repo.file_count} source files across {repo.total_loc} lines of code.

## Key Files
```
{sample_str}
```

## Setup & Running
1. Clone the repository locally.
2. Install required dependencies for {repo.primary_language}.
3. Run the application startup command.
"""

        return ReadmeResponse(markdown_content=content)
