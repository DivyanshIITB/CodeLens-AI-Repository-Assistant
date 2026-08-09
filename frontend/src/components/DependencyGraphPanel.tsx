import React, { useEffect, useState } from 'react';
import { Network, RefreshCw, FileCode } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { DependencyGraph } from '../types';
import { api } from '../services/api';

export const DependencyGraphPanel: React.FC = () => {
  const { activeRepo, loadFileContent } = useAppStore();
  const [graph, setGraph] = useState<DependencyGraph | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (activeRepo) {
      setLoading(true);
      api.getGraph(activeRepo.id)
        .then(res => setGraph(res))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [activeRepo]);

  if (!activeRepo) return null;

  if (loading) {
    return (
      <div className="flex-1 bg-github-dark flex items-center justify-center p-8 text-github-muted space-x-2">
        <RefreshCw className="w-5 h-5 animate-spin text-github-accent" />
        <span>Parsing AST import definitions & constructing module dependency graph...</span>
      </div>
    );
  }

  if (!graph) return null;

  return (
    <div className="flex-1 bg-github-dark p-6 overflow-y-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white flex items-center space-x-2">
          <Network className="w-5 h-5 text-github-accent" />
          <span>Module Dependency Network</span>
        </h1>
        <p className="text-xs text-github-muted mt-1">
          Visual mapping of module imports and source file dependencies across the repository.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 bg-github-panel border border-github-border rounded-xl p-5 space-y-3 shadow-sm">
          <h3 className="text-sm font-semibold text-white">Repository Modules ({graph.nodes.length})</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-96 overflow-y-auto pr-1">
            {graph.nodes.map(node => (
              <div
                key={node.id}
                onClick={() => loadFileContent(activeRepo.id, node.id)}
                className="bg-github-dark hover:bg-github-hover border border-github-border rounded-lg p-2.5 cursor-pointer transition text-xs flex items-center justify-between group"
              >
                <div className="flex items-center space-x-2 truncate">
                  <FileCode className="w-3.5 h-3.5 text-github-accent shrink-0" />
                  <span className="font-mono text-github-text group-hover:text-white truncate">{node.label}</span>
                </div>
                <span className="text-[10px] uppercase bg-github-panel border border-github-border px-1.5 py-0.5 rounded text-github-muted">
                  {node.type}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-github-panel border border-github-border rounded-xl p-5 space-y-3 shadow-sm">
          <h3 className="text-sm font-semibold text-white">Import Connections ({graph.edges.length})</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {graph.edges.length === 0 ? (
              <p className="text-xs text-github-muted italic">No module imports detected.</p>
            ) : (
              graph.edges.map((edge, idx) => (
                <div key={idx} className="bg-github-dark border border-github-border/60 rounded-lg p-2 text-xs space-y-1">
                  <div className="font-mono text-github-accent font-semibold truncate">{edge.source.split('/').pop()}</div>
                  <div className="text-[11px] text-github-muted flex items-center space-x-1.5 pt-0.5">
                    <span className="text-github-muted">➔ imports</span>
                    <span className="font-mono text-purple-300 font-medium truncate">{edge.target.split('/').pop()}</span>
                  </div>

                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
