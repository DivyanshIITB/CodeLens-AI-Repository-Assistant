import React, { useEffect, useState } from 'react';
import { FileText, Copy, Download, RefreshCw, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

export const ReadmePanel: React.FC = () => {
  const { activeRepo } = useAppStore();
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const fetchReadme = () => {
    if (activeRepo) {
      setLoading(true);
      api.getReadme(activeRepo.id)
        .then(res => setContent(res.markdown_content))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  };

  useEffect(() => {
    fetchReadme();
  }, [activeRepo]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `README_${activeRepo?.name || 'project'}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!activeRepo) return null;

  return (
    <div className="flex-1 bg-github-dark p-6 overflow-y-auto space-y-4">
      <div className="flex items-center justify-between border-b border-github-border pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <FileText className="w-5 h-5 text-github-accent" />
            <span>Automatic README.md Generator</span>
          </h1>
          <p className="text-xs text-github-muted mt-1">
            Auto-generated project documentation covering installation, tech stack, architecture, and usage.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchReadme}
            disabled={loading}
            className="p-2 bg-github-panel border border-github-border hover:bg-github-hover text-white rounded-lg transition"
            title="Regenerate README"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-github-panel border border-github-border hover:bg-github-hover text-white text-xs font-medium rounded-lg transition"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied!' : 'Copy Markdown'}</span>
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-github-green hover:bg-green-700 text-white text-xs font-medium rounded-lg transition shadow"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download .md</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-github-muted space-x-2">
          <RefreshCw className="w-5 h-5 animate-spin text-github-accent" />
          <span>Synthesizing repository AST to generate README.md...</span>
        </div>
      ) : (
        <div className="bg-github-panel border border-github-border rounded-xl p-8 shadow-md">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            className="prose prose-invert max-w-none text-sm space-y-4 text-github-text"
          >
            {content}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
};
