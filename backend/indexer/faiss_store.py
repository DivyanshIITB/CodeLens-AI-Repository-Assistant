import os
import faiss
import numpy as np
from pathlib import Path
from typing import List, Tuple
from backend.config.settings import settings
from backend.config.logger import logger

class FAISSVectorStore:
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        self.index_path = settings.VECTOR_DIR / f"{repo_id}.faiss"
        self.dimension = settings.EMBEDDING_DIMENSION
        self.index = self._load_or_create_index()

    def _load_or_create_index(self) -> faiss.IndexIDMap:
        if self.index_path.exists():
            try:
                index = faiss.read_index(str(self.index_path))
                logger.info(f"Loaded existing FAISS index for repo {self.repo_id} with {index.ntotal} vectors.")
                return index
            except Exception as e:
                logger.error(f"Error reading FAISS index for {self.repo_id}: {e}. Creating new index.")

        sub_index = faiss.IndexFlatIP(self.dimension)
        index = faiss.IndexIDMap(sub_index)
        return index

    def add_vectors(self, vectors: np.ndarray, ids: List[int]):
        if vectors.shape[0] == 0:
            return
        
        ids_arr = np.array(ids, dtype=np.int64)
        self.index.add_with_ids(vectors, ids_arr)
        self.save()
        logger.info(f"Added {len(ids)} vectors to FAISS index for repo {self.repo_id}. Total: {self.index.ntotal}")

    def remove_vectors(self, ids: List[int]):
        if not ids:
            return
        ids_arr = np.array(ids, dtype=np.int64)
        self.index.remove_ids(ids_arr)
        self.save()
        logger.info(f"Removed {len(ids)} vectors from FAISS index for repo {self.repo_id}.")

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[int, float]]:
        if self.index.ntotal == 0:
            return []

        top_k = min(top_k, self.index.ntotal)
        distances, ids = self.index.search(query_vector, top_k)

        results = []
        for vec_id, score in zip(ids[0], distances[0]):
            if vec_id != -1:
                results.append((int(vec_id), float(score)))

        return results

    def save(self):
        settings.VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))

    def delete_index(self):
        if self.index_path.exists():
            os.remove(self.index_path)
            logger.info(f"Deleted FAISS index file for repo {self.repo_id}.")
