import React from 'react';
import { Cpu, GitBranch, Plus, Settings as SettingsIcon, ShieldCheck, Terminal, Trash2 } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

export const Header: React.FC = () => {
  const {
    repos,
    activeRepo,
    setActiveRepo,
    models,
    selectedModel,
    setSelectedModel,
    setIsImportModalOpen,
    setIsSettingsModalOpen,
    refreshRepos
  } = useAppStore();

  const handleDeleteRepo = async () => {
    if (!activeRepo) return;
    if (window.confirm(`Are you sure you want to remove repository "${activeRepo.name}"? This will delete its vector index and source files.`)) {
      try {
        await api.deleteRepo(activeRepo.id);
        setActiveRepo(null);
        await refreshRepos();
      } catch (e) {
        console.error('Failed to delete repository', e);
      }
    }
  };

  return (
    <header className="h-14 bg-github-panel border-b border-github-border flex items-center justify-between px-4 text-sm z-20">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 font-semibold text-white tracking-wide">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center shadow-md">
            <Terminal className="w-5 h-5 text-white" />
          </div>
          <span className="text-base font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            CodeLens AI
          </span>
        </div>

        <div className="h-5 w-px bg-github-border" />

        <div className="flex items-center space-x-2">
          <GitBranch className="w-4 h-4 text-github-muted" />
          <select
            className="bg-github-dark border border-github-border rounded-md px-3 py-1 text-xs text-white focus:outline-none focus:border-github-accent"
            value={activeRepo?.id || ''}
            onChange={(e) => {
              const selected = repos.find((r) => r.id === e.target.value);
              if (selected) setActiveRepo(selected);
            }}
          >
            {repos.length === 0 && <option value="">No Repositories Indexed</option>}
            {repos.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.primary_language || 'Repo'}) — {r.file_count} files
              </option>
            ))}
          </select>

          {activeRepo && (
            <button
              onClick={handleDeleteRepo}
              className="p-1.5 text-github-muted hover:text-red-400 hover:bg-github-hover rounded-md transition"
              title="Delete Current Repository"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={() => setIsImportModalOpen(true)}
            className="flex items-center space-x-1.5 bg-github-green hover:bg-green-700 text-white px-2.5 py-1 rounded-md text-xs font-medium transition shadow"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Import Repo</span>
          </button>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2 bg-github-dark border border-github-border rounded-md px-2.5 py-1">
          <Cpu className="w-4 h-4 text-github-purple" />
          <span className="text-xs text-github-muted hidden sm:inline">Model:</span>
          <select
            className="bg-transparent text-xs text-white focus:outline-none cursor-pointer"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            {models.length === 0 && <option value="qwen2.5-coder:1.5b">qwen2.5-coder:1.5b</option>}
            {models.map((m) => (
              <option key={m.name} value={m.name} className="bg-github-panel">
                {m.name} ({m.size_human})
              </option>
            ))}
          </select>
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" title="Ollama Connected" />
        </div>

        <div className="hidden md:flex items-center space-x-1 px-2 py-0.5 rounded bg-blue-950/60 border border-blue-800/50 text-blue-300 text-xs">
          <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
          <span>100% Free & Local</span>
        </div>

        <button
          onClick={() => setIsSettingsModalOpen(true)}
          className="p-1.5 text-github-muted hover:text-white hover:bg-github-hover rounded-md transition"
          title="RAG & LLM Settings"
        >
          <SettingsIcon className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
