import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from backend.config.settings import settings
from backend.config.logger import logger

class LocalEmbedder:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalEmbedder, cls).__new__(cls)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        logger.info(f"Loading local embedding model: {settings.EMBEDDING_MODEL}")
        try:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Local embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformer model {settings.EMBEDDING_MODEL}: {e}")
            raise e

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        if not texts:
            return np.empty((0, settings.EMBEDDING_DIMENSION), dtype=np.float32)
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return np.array(embeddings, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        instruction_query = f"Represent this sentence for searching relevant code: {query}"
        embedding = self.model.encode(
            [instruction_query],
            normalize_embeddings=True
        )
        return np.array(embedding, dtype=np.float32)

embedder = LocalEmbedder()
