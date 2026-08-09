import React, { useEffect, useState } from 'react';
import { Code2, Search, FileCode, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { ApiDocItem } from '../types';
import { api } from '../services/api';

export const ApiDocsPanel: React.FC = () => {
  const { activeRepo, loadFileContent } = useAppStore();
  const [docs, setDocs] = useState<ApiDocItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [search, setSearch] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<string>('ALL');

  useEffect(() => {
    if (activeRepo) {
      setLoading(true);
      api.getApiDocs(activeRepo.id)
        .then(res => setDocs(res))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [activeRepo]);

  if (!activeRepo) return null;

  const filteredDocs = docs.filter(item => {
    const matchesSearch = item.endpoint.toLowerCase().includes(search.toLowerCase()) ||
                          item.file_path.toLowerCase().includes(search.toLowerCase());
    const matchesMethod = selectedMethod === 'ALL' || item.method.toUpperCase() === selectedMethod;
    return matchesSearch && matchesMethod;
  });

  return (
    <div className="flex-1 bg-github-dark p-6 overflow-y-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-github-border pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <Code2 className="w-5 h-5 text-github-purple" />
            <span>Automatic REST API Documentation</span>
          </h1>
          <p className="text-xs text-github-muted mt-1">
            Auto-discovered HTTP REST endpoints, parameters, and route handlers.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-github-muted absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter endpoints..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-github-panel border border-github-border rounded-lg pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-github-accent placeholder-github-muted"
            />
          </div>

          <select
            value={selectedMethod}
            onChange={(e) => setSelectedMethod(e.target.value)}
            className="bg-github-panel border border-github-border rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
          >
            <option value="ALL">All Methods</option>
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-github-muted space-x-2">
          <RefreshCw className="w-5 h-5 animate-spin text-github-purple" />
          <span>Scanning route decorators across AST syntax trees...</span>
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="bg-github-panel border border-github-border rounded-xl p-8 text-center text-github-muted italic">
          No matching REST API endpoints found in this repository.
        </div>
      ) : (
        <div className="space-y-3">
          {filteredDocs.map((item, idx) => (
            <div
              key={idx}
              className="bg-github-panel border border-github-border rounded-xl p-4 space-y-3 hover:border-github-accent transition shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <MethodBadge method={item.method} />
                  <span className="font-mono text-sm font-semibold text-white tracking-wide">{item.endpoint}</span>
                </div>

                <button
                  onClick={() => loadFileContent(activeRepo.id, item.file_path, [item.start_line, item.start_line + 20])}
                  className="flex items-center space-x-1 text-xs text-github-accent hover:underline font-mono"
                >
                  <FileCode className="w-3.5 h-3.5" />
                  <span>{item.file_path}:{item.start_line}</span>
                </button>
              </div>

              <p className="text-xs text-github-text">{item.summary}</p>

              {item.parameters && item.parameters.length > 0 && (
                <div className="pt-2 border-t border-github-border/50 flex items-center space-x-2 text-xs">
                  <span className="text-github-muted font-medium">Parameters:</span>
                  <div className="flex flex-wrap gap-1">
                    {item.parameters.map((param, pIdx) => (
                      <span key={pIdx} className="bg-github-dark border border-github-border font-mono px-2 py-0.5 rounded text-[11px] text-github-accent">
                        {param}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const MethodBadge: React.FC<{ method: string }> = ({ method }) => {
  const m = method.toUpperCase();
  let colors = 'bg-blue-950 text-blue-400 border-blue-800';
  if (m === 'POST') colors = 'bg-emerald-950 text-emerald-400 border-emerald-800';
  if (m === 'PUT') colors = 'bg-amber-950 text-amber-400 border-amber-800';
  if (m === 'DELETE') colors = 'bg-red-950 text-red-400 border-red-800';

  return (
    <span className={`px-2.5 py-1 rounded text-xs font-bold font-mono border ${colors}`}>
      {m}
    </span>
  );
};
