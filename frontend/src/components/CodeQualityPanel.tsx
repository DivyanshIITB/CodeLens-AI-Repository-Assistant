import React, { useEffect, useState } from 'react';
import { AlertTriangle, FileCode, CheckCircle2, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { CodeSmell } from '../types';
import { api } from '../services/api';

export const CodeQualityPanel: React.FC = () => {
  const { activeRepo, loadFileContent } = useAppStore();
  const [smells, setSmells] = useState<CodeSmell[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  useEffect(() => {
    if (activeRepo) {
      setLoading(true);
      api.getCodeSmells(activeRepo.id)
        .then(res => setSmells(res))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [activeRepo]);

  if (!activeRepo) return null;

  const filteredSmells = smells.filter(s => severityFilter === 'ALL' || s.severity === severityFilter.toLowerCase());

  return (
    <div className="flex-1 bg-github-dark p-6 overflow-y-auto space-y-6">
      <div className="flex items-center justify-between border-b border-github-border pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <span>Code Smells & Refactoring Suggestions</span>
          </h1>
          <p className="text-xs text-github-muted mt-1">
            Automated detection of long functions, large classes, missing docstrings, and pending TODO comments.
          </p>
        </div>

        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="bg-github-panel border border-github-border rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
        >
          <option value="ALL">All Severities</option>
          <option value="HIGH">High Severity</option>
          <option value="MEDIUM">Medium Severity</option>
          <option value="LOW">Low Severity</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-github-muted space-x-2">
          <RefreshCw className="w-5 h-5 animate-spin text-amber-400" />
          <span>Analyzing AST code complexity & documentation coverage...</span>
        </div>
      ) : filteredSmells.length === 0 ? (
        <div className="bg-github-panel border border-github-border rounded-xl p-8 text-center space-y-2">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
          <h3 className="text-sm font-semibold text-white">Clean Codebase!</h3>
          <p className="text-xs text-github-muted">No high-severity code smells or missing docstrings detected.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredSmells.map((smell, idx) => (
            <div
              key={idx}
              className="bg-github-panel border border-github-border rounded-xl p-4 space-y-2 hover:border-github-accent transition shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <SeverityBadge severity={smell.severity} />
                  <span className="text-sm font-semibold text-white">{smell.smell_type}</span>
                </div>

                <button
                  onClick={() => loadFileContent(activeRepo.id, smell.file_path, [smell.line_number, smell.line_number + 15])}
                  className="flex items-center space-x-1 text-xs text-github-accent hover:underline font-mono"
                >
                  <FileCode className="w-3.5 h-3.5" />
                  <span>{smell.file_path}:{smell.line_number}</span>
                </button>
              </div>

              <p className="text-xs text-github-text">{smell.description}</p>

              <div className="bg-github-dark border border-github-border/60 rounded-lg p-2.5 text-xs text-emerald-400 space-y-1">
                <span className="font-semibold text-white">Suggested Improvement:</span>
                <p className="text-github-muted">{smell.recommendation}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  let colors = 'bg-slate-900 text-slate-300 border-slate-700';
  if (severity === 'high') colors = 'bg-red-950 text-red-400 border-red-800';
  if (severity === 'medium') colors = 'bg-amber-950 text-amber-400 border-amber-800';
  if (severity === 'low') colors = 'bg-blue-950 text-blue-400 border-blue-800';

  return (
    <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${colors}`}>
      {severity}
    </span>
  );
};
