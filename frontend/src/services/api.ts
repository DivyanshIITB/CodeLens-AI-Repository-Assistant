import axios from 'axios';
import {
  Repository, TreeNode, OverviewData, ApiDocItem,
  OnboardingGuide, DependencyGraph, CodeSmell, RepoStats,
  OllamaModel, AppSettings
} from '../types';

const API_BASE = '/api/v1';

export const api = {
  async listRepos(): Promise<Repository[]> {
    const res = await axios.get(`${API_BASE}/repos`);
    return res.data;
  },

  async importRepoUrl(url: string): Promise<Repository> {
    const res = await axios.post(`${API_BASE}/repos/import`, { url });
    return res.data;
  },

  async uploadRepoZip(file: File): Promise<Repository> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await axios.post(`${API_BASE}/repos/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  async getRepoTree(repoId: string): Promise<TreeNode[]> {
    const res = await axios.get(`${API_BASE}/repos/${repoId}/tree`);
    return res.data;
  },

  async readRepoFile(repoId: string, path: string): Promise<{ file_path: string; content: string }> {
    const res = await axios.get(`${API_BASE}/repos/${repoId}/file`, { params: { path } });
    return res.data;
  },

  async deleteRepo(repoId: string): Promise<void> {
    await axios.delete(`${API_BASE}/repos/${repoId}`);
  },

  async getOverview(repoId: string): Promise<OverviewData> {
    const res = await axios.get(`${API_BASE}/analysis/${repoId}/overview`);
    return res.data;
  },

  async getReadme(repoId: string): Promise<{ markdown_content: string }> {
    const res = await axios.get(`${API_BASE}/analysis/${repoId}/readme`);
    return res.data;
  },

  async getApiDocs(repoId: string): Promise<ApiDocItem[]> {
    const res = await axios.get(`${API_BASE}/analysis/${repoId}/apidocs`);
    return res.data;
  },

  async getOnboarding(repoId: string): Promise<OnboardingGuide> {
    const res = await axios.get(`${API_BASE}/analysis/${repoId}/onboarding`);
    return res.data;
  },

  async getGraph(repoId: string): Promise<DependencyGraph> {
    const res = await axios.get(`${API_BASE}/analysis/${repoId}/graph`);
    return res.data;
  },

  async getCodeSmells(repoId: string): Promise<CodeSmell[]> {
    const res = await axios.get(`${API_BASE}/analysis/${repoId}/quality`);
    return res.data;
  },

  async getStats(repoId: string): Promise<RepoStats> {
    const res = await axios.get(`${API_BASE}/analysis/${repoId}/stats`);
    return res.data;
  },

  async listModels(): Promise<OllamaModel[]> {
    const res = await axios.get(`${API_BASE}/models`);
    return res.data;
  },

  async getSettings(): Promise<AppSettings> {
    const res = await axios.get(`${API_BASE}/settings`);
    return res.data;
  },

  async updateSettings(settings: AppSettings): Promise<AppSettings> {
    const res = await axios.post(`${API_BASE}/settings`, settings);
    return res.data;
  },

  async runBenchmark(repoId: string, sampleSize: number = 10): Promise<any> {
    const res = await axios.post(`${API_BASE}/eval/${repoId}?sample_size=${sampleSize}`);
    return res.data;
  }
};

export async function streamChat(
  payload: { repo_id: string; message: string; model?: string; top_k?: number; temperature?: number },
  onMetadata: (citations: any[], confidenceScore?: number, confidenceLevel?: string) => void,

  onToken: (token: string) => void,
  onDone: (durationMs: number) => void,
  onError: (err: any) => void,
  signal?: AbortSignal
) {
  try {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal
    });


    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.event === 'metadata') {
              onMetadata(data.citations || [], data.confidence_score, data.confidence_level);
            } else if (data.event === 'token') {

              onToken(data.token);
            } else if (data.event === 'done') {
              onDone(data.duration_ms);
            }
          } catch (e) {
            // ignore
          }
        }
      }
    }
  } catch (err) {
    onError(err);
  }
}
