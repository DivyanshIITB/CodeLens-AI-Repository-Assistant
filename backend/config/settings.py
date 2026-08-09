import os
from pathlib import Path
from dataclasses import dataclass, field

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REPOS_DIR = DATA_DIR / "repos"
VECTOR_DIR = DATA_DIR / "vectors"
DB_DIR = DATA_DIR / "db"

for directory in [DATA_DIR, REPOS_DIR, VECTOR_DIR, DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        @dataclass
        class BaseSettings:
            pass

class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeLens AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Storage Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    REPOS_DIR: Path = REPOS_DIR
    VECTOR_DIR: Path = VECTOR_DIR
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_DIR / 'codelens.db'}"
    
    # Ollama Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "qwen2.5-coder:1.5b")
    FALLBACK_MODELS: list = field(default_factory=lambda: ["qwen2.5-coder:1.5b", "qwen2.5-coder", "deepseek-coder", "llama3.1"])
    
    # Embeddings & FAISS
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    
    # RAG Search Settings
    DEFAULT_TOP_K: int = 4
    DEFAULT_CHUNK_SIZE: int = 512
    DEFAULT_CHUNK_OVERLAP: int = 64
    DEFAULT_TEMPERATURE: float = 0.2
    MAX_CONTEXT_TOKENS: int = 2048

    RRF_K: int = 60
    
    # Supported File Extensions
    SUPPORTED_EXTENSIONS: set = field(default_factory=lambda: {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".c", ".cpp", ".h", ".hpp",
        ".rs", ".html", ".css", ".json", ".md", ".yml", ".yaml", ".sql", ".sh", ".dockerfile"
    })
    
    # Excluded Directories
    EXCLUDED_DIRS: set = field(default_factory=lambda: {
        ".git", ".idea", ".vscode", "node_modules", "venv", ".venv", "__pycache__",
        "dist", "build", "target", ".next", "out", ".coverage", ".pytest_cache"
    })

settings = Settings()
