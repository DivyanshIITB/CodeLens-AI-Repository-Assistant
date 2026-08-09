import React from 'react';
import { X, FileCode, Copy, Check, Sparkles } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useAppStore } from '../store/useAppStore';

export const CodeViewerPanel: React.FC = () => {
  const { activeFile, setActiveFile, activeCitations } = useAppStore();
  const [copied, setCopied] = React.useState<boolean>(false);

  if (!activeFile) {
    return (
      <div className="w-80 lg:w-96 bg-github-panel border-l border-github-border flex flex-col items-center justify-center p-6 text-center text-github-muted h-[calc(100vh-3.5rem)] select-none">
        <FileCode className="w-12 h-12 mb-3 text-github-border" />
        <h3 className="text-sm font-semibold text-white mb-1">Code Inspector</h3>
        <p className="text-xs">
          Click any file in the left explorer or a citation reference link in the chat to open and inspect source code.
        </p>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(activeFile.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getLanguage = (path: string): string => {
    const ext = path.split('.').pop()?.toLowerCase();
    const map: Record<string, string> = {
      py: 'python', js: 'javascript', jsx: 'jsx', ts: 'typescript', tsx: 'tsx',
      java: 'java', go: 'go', rs: 'rust', c: 'c', cpp: 'cpp', html: 'html',
      css: 'css', json: 'json', md: 'markdown', sql: 'sql', sh: 'bash'
    };
    return map[ext || ''] || 'text';
  };

  return (
    <aside className="w-80 lg:w-96 bg-github-panel border-l border-github-border flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden shadow-xl">
      <div className="px-3.5 py-2.5 border-b border-github-border flex items-center justify-between bg-github-dark">
        <div className="flex items-center space-x-2 font-mono text-xs text-github-accent truncate">
          <FileCode className="w-4 h-4 shrink-0" />
          <span className="truncate font-semibold">{activeFile.path}</span>
        </div>

        <div className="flex items-center space-x-1">
          <button
            onClick={handleCopy}
            className="p-1 text-github-muted hover:text-white hover:bg-github-hover rounded transition"
            title="Copy Source Code"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => setActiveFile(null)}
            className="p-1 text-github-muted hover:text-white hover:bg-github-hover rounded transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {activeFile.highlightLines && (
        <div className="px-3.5 py-1.5 bg-blue-950/60 border-b border-blue-800/50 text-[11px] text-blue-300 flex items-center justify-between">
          <span className="flex items-center space-x-1 font-mono">
            <Sparkles className="w-3 h-3 text-blue-400" />
            <span>Retrieved Lines: {activeFile.highlightLines[0]} - {activeFile.highlightLines[1]}</span>
          </span>
          <span className="text-[10px] bg-blue-900/60 px-1.5 py-0.2 rounded border border-blue-700 font-sans">AST Grounded</span>
        </div>
      )}

      <div className="flex-1 overflow-auto text-xs bg-[#1e1e1e]">
        <SyntaxHighlighter
          language={getLanguage(activeFile.path)}
          style={vscDarkPlus}
          showLineNumbers={true}
          wrapLines={true}
          lineProps={(lineNumber) => {
            const style: React.CSSProperties = { display: 'block' };
            if (
              activeFile.highlightLines &&
              lineNumber >= activeFile.highlightLines[0] &&
              lineNumber <= activeFile.highlightLines[1]
            ) {
              style.backgroundColor = 'rgba(56, 139, 253, 0.15)';
              style.borderLeft = '3px solid #58a6ff';
            }
            return { style };
          }}
          customStyle={{
            margin: 0,
            padding: '12px',
            fontSize: '11px',
            lineHeight: '1.5',
            background: 'transparent'
          }}
        >
          {activeFile.content}
        </SyntaxHighlighter>
      </div>

      {activeCitations.length > 0 && (
        <div className="p-3 border-t border-github-border bg-github-dark text-xs space-y-1">
          <div className="text-[11px] font-semibold text-github-muted uppercase tracking-wider">
            Context Vectors ({activeCitations.length})
          </div>
          <div className="space-y-1 max-h-24 overflow-y-auto">
            {activeCitations.map((c, i) => (
              <div key={i} className="text-[11px] font-mono text-github-text truncate flex justify-between">
                <span className="truncate">{c.file_path}</span>
                <span className="text-github-muted ml-2">L{c.start_line}-{c.end_line}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
};
