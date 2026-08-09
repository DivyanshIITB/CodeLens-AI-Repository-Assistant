export interface Repository {
  id: string;
  name: string;
  url?: string;
  path: string;
  is_local: boolean;
  status: 'pending' | 'cloning' | 'indexing' | 'ready' | 'error';
  file_count: number;
  total_loc: number;
  primary_language?: string;
  error_message?: string;
  created_at: string;
}

export interface TreeNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: TreeNode[];
  size?: number;
}

export interface Citation {
  file_path: string;
  start_line: number;
  end_line: number;
  chunk_type: string;
  name?: string;
  parent_scope?: string;
  snippet: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  citations?: Citation[];
  isStreaming?: boolean;
  duration_ms?: number;
  confidence_score?: number;
  confidence_level?: string;
}


export interface OverviewData {
  repo_name: string;
  languages: Record<string, number>;
  total_files: number;
  total_loc: number;
  tech_stack: string[];
  frameworks: string[];
  databases: string[];
  package_managers: string[];
  external_apis: string[];
  architectural_summary: string;
}

export interface ApiDocItem {
  endpoint: string;
  method: string;
  file_path: string;
  start_line: number;
  parameters: string[];
  summary: string;
  response_type?: string;
}

export interface OnboardingGuide {
  learning_roadmap: Array<{ step: string; description: string }>;
  recommended_reading_order: string[];
  core_modules: Array<{ module: string; files: string }>;
  entry_points: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

export interface DependencyGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface CodeSmell {
  file_path: string;
  line_number: number;
  smell_type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  recommendation: string;
}

export interface RepoStats {
  repo_id: string;
  total_files: number;
  total_loc: number;
  avg_file_size_loc: number;
  languages: Record<string, number>;
  largest_files: Array<{ path: string; lines: number; size_kb: number }>;
  most_connected_modules: Array<{ path: string; lines: number; size_kb: number }>;
}

export interface OllamaModel {
  name: string;
  size_human: string;
  parameter_size?: string;
  quantization?: string;
  status: string;
}

export interface AppSettings {
  default_model: string;
  embedding_model: string;
  top_k: number;
  chunk_size: number;
  chunk_overlap: number;
  temperature: number;
  theme: string;
}
