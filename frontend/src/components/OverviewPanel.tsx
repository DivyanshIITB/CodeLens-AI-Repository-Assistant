import React, { useEffect, useState } from 'react';
import { Layout, Server, Database, Box, Globe, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { OverviewData } from '../types';
import { api } from '../services/api';

export const OverviewPanel: React.FC = () => {
  const { activeRepo } = useAppStore();
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (activeRepo) {
      setLoading(true);
      api.getOverview(activeRepo.id)
        .then(res => setData(res))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [activeRepo]);

  if (!activeRepo) return null;

  if (loading) {
    return (
      <div className="flex-1 bg-github-dark flex items-center justify-center p-8 text-github-muted space-x-2">
        <RefreshCw className="w-5 h-5 animate-spin text-github-accent" />
        <span>Analyzing repository architecture & tech stack...</span>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="flex-1 bg-github-dark p-6 overflow-y-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">{data.repo_name} Overview</h1>
        <p className="text-xs text-github-muted">
          High-level repository architecture analysis, language breakdown, and tech stack detection.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StackCard title="Tech Stack" items={data.tech_stack} icon={Box} color="border-blue-500/40 text-blue-400" />
        <StackCard title="Frameworks" items={data.frameworks} icon={Server} color="border-purple-500/40 text-purple-400" />
        <StackCard title="Databases" items={data.databases} icon={Database} color="border-emerald-500/40 text-emerald-400" />
        <StackCard title="External APIs" items={data.external_apis} icon={Globe} color="border-amber-500/40 text-amber-400" />
      </div>

      <div className="bg-github-panel border border-github-border rounded-xl p-5 space-y-3 shadow-sm">
        <div className="flex items-center space-x-2 font-semibold text-white">
          <Layout className="w-5 h-5 text-github-accent" />
          <span>Architectural Summary</span>
        </div>
        <div className="text-sm leading-relaxed text-github-text whitespace-pre-line bg-github-dark p-4 rounded-lg border border-github-border/60">
          {data.architectural_summary}
        </div>
      </div>

      <div className="bg-github-panel border border-github-border rounded-xl p-5 space-y-4 shadow-sm">
        <h3 className="text-sm font-semibold text-white">Programming Language Breakdown</h3>
        <div className="space-y-3">
          {Object.entries(data.languages).map(([lang, count]) => {
            const pct = ((count / Math.max(1, data.total_files)) * 100).toFixed(1);
            return (
              <div key={lang} className="space-y-1">
                <div className="flex justify-between text-xs font-medium">
                  <span className="capitalize text-white">{lang}</span>
                  <span className="text-github-muted">{count} files ({pct}%)</span>
                </div>
                <div className="w-full bg-github-dark h-2 rounded-full overflow-hidden border border-github-border/40">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-full rounded-full"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const StackCard: React.FC<{ title: string; items: string[]; icon: any; color: string }> = ({
  title,
  items,
  icon: Icon,
  color
}) => (
  <div className={`bg-github-panel border ${color} rounded-xl p-4 space-y-2 shadow-sm`}>
    <div className="flex items-center space-x-2 font-medium text-xs text-github-muted">
      <Icon className="w-4 h-4" />
      <span>{title}</span>
    </div>
    <div className="flex flex-wrap gap-1.5 pt-1">
      {items.length === 0 ? (
        <span className="text-xs text-github-muted italic">Standard</span>
      ) : (
        items.map((item, i) => (
          <span key={i} className="bg-github-dark border border-github-border px-2 py-0.5 rounded text-xs text-white font-medium">
            {item}
          </span>
        ))
      )}
    </div>
  </div>
);
