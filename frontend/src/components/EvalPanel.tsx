import React, { useState } from 'react';
import { BarChart3, Play, CheckCircle2, Clock, Zap, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

export const EvalPanel: React.FC = () => {
  const { activeRepo } = useAppStore();
  const [results, setResults] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [sampleSize, setSampleSize] = useState<number>(10);

  if (!activeRepo) return null;

  const handleRunBenchmark = async () => {
    setLoading(true);
    try {
      const res = await api.runBenchmark(activeRepo.id, sampleSize);
      setResults(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 bg-github-dark p-6 overflow-y-auto space-y-6">
      <div className="flex items-center justify-between border-b border-github-border pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-github-accent" />
            <span>RAG Evaluation & Benchmark Suite</span>
          </h1>
          <p className="text-xs text-github-muted mt-1">
            Automated testing against 50 repository benchmark questions evaluating Retrieval Accuracy, Citation Grounding, and Latency.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={sampleSize}
            onChange={(e) => setSampleSize(parseInt(e.target.value))}
            className="bg-github-panel border border-github-border rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
          >
            <option value={5}>5 Questions Sample</option>
            <option value={10}>10 Questions Sample</option>
            <option value={20}>20 Questions Sample</option>
            <option value={50}>Full 50 Questions Benchmark</option>
          </select>

          <button
            onClick={handleRunBenchmark}
            disabled={loading}
            className="flex items-center space-x-1.5 bg-github-green hover:bg-green-700 disabled:opacity-50 text-white font-medium px-4 py-1.5 rounded-lg text-xs transition shadow"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            <span>{loading ? 'Running Benchmark...' : 'Run Evaluation'}</span>
          </button>
        </div>
      </div>

      {results && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard title="Retrieval Hit Rate" value={`${results.retrieval_hit_rate}%`} icon={CheckCircle2} color="text-emerald-400 border-emerald-500/40" />
          <MetricCard title="Citation Accuracy" value={`${results.citation_accuracy}%`} icon={Zap} color="text-blue-400 border-blue-500/40" />
          <MetricCard title="Avg Query Latency" value={`${results.avg_latency_ms} ms`} icon={Clock} color="text-purple-400 border-purple-500/40" />
          <MetricCard title="Total Evaluated" value={`${results.total_eval_queries} Queries`} icon={BarChart3} color="text-amber-400 border-amber-500/40" />
        </div>
      )}

      {results && results.details && (
        <div className="bg-github-panel border border-github-border rounded-xl p-5 space-y-3 shadow-sm">
          <h3 className="text-sm font-semibold text-white">Evaluation Detailed Breakdown</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {results.details.map((item: any) => (
              <div key={item.id} className="bg-github-dark border border-github-border/60 rounded-lg p-3 text-xs flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-semibold text-white">#{item.id} {item.query}</span>
                  <div className="text-[11px] text-github-muted">Chunks Retrieved: {item.retrieved_count}</div>
                </div>

                <div className="flex items-center space-x-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${item.retrieval_hit ? 'bg-emerald-950 text-emerald-400 border-emerald-800' : 'bg-red-950 text-red-400 border-red-800'}`}>
                    {item.retrieval_hit ? 'HIT' : 'MISS'}
                  </span>
                  <span className="font-mono text-github-muted">{item.latency_ms} ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const MetricCard: React.FC<{ title: string; value: string; icon: any; color: string }> = ({ title, value, icon: Icon, color }) => (
  <div className={`bg-github-panel border ${color} rounded-xl p-4 space-y-1 shadow-sm`}>
    <div className="flex items-center space-x-1.5 text-xs text-github-muted">
      <Icon className="w-4 h-4" />
      <span>{title}</span>
    </div>
    <div className="text-xl font-bold text-white font-mono">{value}</div>
  </div>
);
