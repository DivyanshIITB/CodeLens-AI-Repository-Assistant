from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.db import Base

class RepositoryDB(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=True)
    path: Mapped[str] = mapped_column(String, nullable=False)
    is_local: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    total_loc: Mapped[int] = mapped_column(Integer, default=0)
    primary_language: Mapped[str] = mapped_column(String, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = relationship("FileIndexDB", back_populates="repository", cascade="all, delete-orphan")
    chunks = relationship("CodeChunkDB", back_populates="repository", cascade="all, delete-orphan")


class FileIndexDB(Base):
    __tablename__ = "file_indices"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    repository_id: Mapped[str] = mapped_column(String, ForeignKey("repositories.id"), nullable=False)
    relative_path: Mapped[str] = mapped_column(String, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False)
    total_lines: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    indexed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    repository = relationship("RepositoryDB", back_populates="files")


class CodeChunkDB(Base):
    __tablename__ = "code_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    repository_id: Mapped[str] = mapped_column(String, ForeignKey("repositories.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_scope: Mapped[str] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    vector_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    repository = relationship("RepositoryDB", back_populates="chunks")
