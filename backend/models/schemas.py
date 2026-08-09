from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class RepoImportRequest(BaseModel):
    url: Optional[str] = Field(None, description="GitHub repository HTTPS URL")
    repo_name: Optional[str] = Field(None, description="Custom name for local repo")

class RepoResponse(BaseModel):
    id: str
    name: str
    url: Optional[str]
    path: str
    is_local: bool
    status: str
    file_count: int
    total_loc: int
    primary_language: Optional[str]
    error_message: Optional[str] = None
    created_at: str

class CodeChunkMeta(BaseModel):
    id: str
    repo_id: str
    file_path: str
    chunk_type: str
    name: Optional[str] = None
    start_line: int
    end_line: int
    parent_scope: Optional[str] = None
    content: str
    vector_id: int
    score: Optional[float] = None

class Citation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str
    name: Optional[str] = None
    parent_scope: Optional[str] = None
    snippet: str
    score: float

class ChatRequest(BaseModel):
    repo_id: str
    message: str
    model: Optional[str] = None
    top_k: Optional[int] = 6
    temperature: Optional[float] = 0.2
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    duration_ms: float
    tokens_per_sec: Optional[float] = 0.0

class OverviewResponse(BaseModel):
    repo_name: str
    languages: Dict[str, int]
    total_files: int
    total_loc: int
    tech_stack: List[str]
    frameworks: List[str]
    databases: List[str]
    package_managers: List[str]
    external_apis: List[str]
    architectural_summary: str

class ReadmeResponse(BaseModel):
    markdown_content: str

class ApiDocItem(BaseModel):
    endpoint: str
    method: str
    file_path: str
    start_line: int
    parameters: List[str]
    summary: str
    response_type: Optional[str] = None

class OnboardingResponse(BaseModel):
    learning_roadmap: List[Dict[str, str]]
    recommended_reading_order: List[str]
    core_modules: List[Dict[str, str]]
    entry_points: List[str]

class GraphNode(BaseModel):
    id: str
    label: str
    type: str

class GraphEdge(BaseModel):
    source: str
    target: str
    weight: int

class DependencyGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class CodeSmellItem(BaseModel):
    file_path: str
    line_number: int
    smell_type: str
    severity: str
    description: str
    recommendation: str

class StatsResponse(BaseModel):
    repo_id: str
    total_files: int
    total_loc: int
    avg_file_size_loc: float
    languages: Dict[str, int]
    largest_files: List[Dict[str, Any]]
    most_connected_modules: List[Dict[str, Any]]

class OllamaModelInfo(BaseModel):
    name: str
    size_human: str
    parameter_size: Optional[str] = None
    quantization: Optional[str] = None
    status: str

class SettingsSchema(BaseModel):
    default_model: str
    embedding_model: str
    top_k: int
    chunk_size: int
    chunk_overlap: int
    temperature: float
    theme: str
