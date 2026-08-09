import React, { useState, useEffect } from 'react';
import {
  MessageSquare, Layout, FileText, Code2, Compass, Network,
  AlertTriangle, BarChart3, Folder, File, ChevronRight, ChevronDown,
  RefreshCw, CheckCircle2
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { TreeNode } from '../types';
import { api } from '../services/api';

const NAV_ITEMS = [
  { id: 'chat', label: 'AI Chat', icon: MessageSquare },
  { id: 'overview', label: 'Overview', icon: Layout },
  { id: 'readme', label: 'README Gen', icon: FileText },
  { id: 'apidocs', label: 'API Docs', icon: Code2 },
  { id: 'onboarding', label: 'Onboarding', icon: Compass },
  { id: 'graph', label: 'Dependencies', icon: Network },
  { id: 'quality', label: 'Code Smells', icon: AlertTriangle },
  { id: 'stats', label: 'Statistics', icon: BarChart3 }
];

export const Sidebar: React.FC = () => {
  const { activeRepo, activeTab, setActiveTab, loadFileContent } = useAppStore();
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [loadingTree, setLoadingTree] = useState<boolean>(false);

  useEffect(() => {
    if (activeRepo) {
      setLoadingTree(true);
      api.getRepoTree(activeRepo.id)
        .then(data => setTree(data))
        .catch(err => console.error(err))
        .finally(() => setLoadingTree(false));
    }
  }, [activeRepo]);

  return (
    <aside className="w-64 bg-github-panel border-r border-github-border flex flex-col h-[calc(100vh-3.5rem)] select-none">
      <div className="p-3 border-b border-github-border grid grid-cols-2 gap-1.5">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-2 px-2.5 py-1.5 rounded-md text-xs font-medium transition ${
                isActive
                  ? 'bg-github-subtle text-github-accent border border-github-border shadow-sm'
                  : 'text-github-muted hover:text-white hover:bg-github-hover'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </div>

      <div className="px-3 py-2 border-b border-github-border flex items-center justify-between text-xs font-semibold text-github-muted uppercase tracking-wider">
        <span>File Explorer</span>
        {activeRepo && (
          <span className="text-[10px] bg-github-dark px-1.5 py-0.5 rounded text-github-text border border-github-border">
            {activeRepo.file_count} files
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-2 text-xs">
        {!activeRepo ? (
          <div className="p-4 text-center text-github-muted italic">
            Import a repository to start exploring source code.
          </div>
        ) : loadingTree ? (
          <div className="flex items-center justify-center p-6 text-github-muted space-x-2">
            <RefreshCw className="w-4 h-4 animate-spin text-github-accent" />
            <span>Loading tree...</span>
          </div>
        ) : (
          <div className="space-y-0.5">
            {tree.map(node => (
              <FileTreeNode key={node.path} node={node} repoId={activeRepo.id} onSelect={loadFileContent} />
            ))}
          </div>
        )}
      </div>

      {activeRepo && (
        <div className="p-3 border-t border-github-border bg-github-dark text-xs space-y-1">
          <div className="flex items-center justify-between text-github-muted">
            <span>Primary Lang:</span>
            <span className="text-white font-medium">{activeRepo.primary_language || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between text-github-muted">
            <span>Total Lines:</span>
            <span className="text-github-purple font-mono">{activeRepo.total_loc.toLocaleString()} LOC</span>
          </div>
          <div className="flex items-center space-x-1 text-[11px] text-emerald-400 pt-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>FAISS Vector Index Synced</span>
          </div>
        </div>
      )}
    </aside>
  );
};

const FileTreeNode: React.FC<{
  node: TreeNode;
  repoId: string;
  onSelect: (repoId: string, path: string) => void;
}> = ({ node, repoId, onSelect }) => {
  const [expanded, setExpanded] = useState<boolean>(false);

  if (node.type === 'directory') {
    return (
      <div>
        <div
          onClick={() => setExpanded(!expanded)}
          className="flex items-center space-x-1.5 px-2 py-1 rounded hover:bg-github-hover cursor-pointer text-github-text hover:text-white"
        >
          {expanded ? <ChevronDown className="w-3.5 h-3.5 text-github-muted" /> : <ChevronRight className="w-3.5 h-3.5 text-github-muted" />}
          <Folder className="w-3.5 h-3.5 text-blue-400" />
          <span className="truncate">{node.name}</span>
        </div>
        {expanded && node.children && (
          <div className="pl-3.5 border-l border-github-border/60 ml-2.5 space-y-0.5 mt-0.5">
            {node.children.map(child => (
              <FileTreeNode key={child.path} node={child} repoId={repoId} onSelect={onSelect} />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      onClick={() => onSelect(repoId, node.path)}
      className="flex items-center space-x-1.5 px-2 py-1 rounded hover:bg-github-hover cursor-pointer text-github-muted hover:text-github-accent transition"
    >
      <File className="w-3.5 h-3.5 text-github-muted" />
      <span className="truncate">{node.name}</span>
    </div>
  );
};
