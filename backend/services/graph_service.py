import re
from typing import Dict, List, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import FileIndexDB, CodeChunkDB
from backend.models.schemas import DependencyGraphResponse, GraphNode, GraphEdge

class GraphService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_dependency_graph(self, repo_id: str) -> DependencyGraphResponse:
        stmt = select(FileIndexDB).where(FileIndexDB.repository_id == repo_id)
        res = await self.db.execute(stmt)
        files = res.scalars().all()

        file_paths = [f.relative_path for f in files]
        file_set = set(file_paths)

        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        edge_counts: Dict[str, int] = {}

        for fp in file_paths:
            node_type = "module"
            if any(k in fp.lower() for k in ("main.", "app.", "index.")):
                node_type = "entry"
            elif any(k in fp.lower() for k in ("config", "setting", "env")):
                node_type = "config"
            elif any(k in fp.lower() for k in ("model", "db", "schema")):
                node_type = "database"
            
            nodes.append(GraphNode(id=fp, label=fp.split("/")[-1], type=node_type))

        stmt_chunks = select(CodeChunkDB).where(CodeChunkDB.repository_id == repo_id)
        chunks_res = await self.db.execute(stmt_chunks)
        chunks = chunks_res.scalars().all()

        import_pattern = re.compile(
            r'(?:import|from|require)\s+["\']?([@\w\.\/\-_]+)["\']?',
            re.IGNORECASE
        )

        for chunk in chunks:
            source_file = chunk.file_path
            matches = import_pattern.findall(chunk.content)
            for raw_target in matches:
                target_clean = raw_target.replace(".", "/").strip("/")
                for target_file in file_set:
                    if target_file != source_file and target_clean in target_file:
                        edge_key = f"{source_file}->{target_file}"
                        edge_counts[edge_key] = edge_counts.get(edge_key, 0) + 1

        for edge_key, weight in edge_counts.items():
            src, tgt = edge_key.split("->")
            edges.append(GraphEdge(source=src, target=tgt, weight=weight))

        return DependencyGraphResponse(nodes=nodes[:100], edges=edges[:200])
