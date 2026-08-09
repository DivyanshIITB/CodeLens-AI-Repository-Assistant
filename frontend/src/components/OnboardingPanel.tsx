import React, { useEffect, useState } from 'react';
import { Compass, BookOpen, Layers, CheckCircle2, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { OnboardingGuide } from '../types';
import { api } from '../services/api';

export const OnboardingPanel: React.FC = () => {
  const { activeRepo, loadFileContent } = useAppStore();
  const [guide, setGuide] = useState<OnboardingGuide | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (activeRepo) {
      setLoading(true);
      api.getOnboarding(activeRepo.id)
        .then(res => setGuide(res))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [activeRepo]);

  if (!activeRepo) return null;

  if (loading) {
    return (
      <div className="flex-1 bg-github-dark flex items-center justify-center p-8 text-github-muted space-x-2">
        <RefreshCw className="w-5 h-5 animate-spin text-github-accent" />
        <span>Building developer onboarding roadmap...</span>
      </div>
    );
  }

  if (!guide) return null;

  return (
    <div className="flex-1 bg-github-dark p-6 overflow-y-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white flex items-center space-x-2">
          <Compass className="w-5 h-5 text-emerald-400" />
          <span>Developer Onboarding Assistant</span>
        </h1>
        <p className="text-xs text-github-muted mt-1">
          Guided learning roadmap, recommended reading order, and core module breakdown for new contributors.
        </p>
      </div>

      <div className="bg-github-panel border border-github-border rounded-xl p-5 space-y-3 shadow-sm">
        <div className="flex items-center space-x-2 font-semibold text-white text-sm">
          <BookOpen className="w-4 h-4 text-github-accent" />
          <span>Recommended Reading Order</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 pt-1">
          {guide.recommended_reading_order.map((filePath, idx) => (
            <div
              key={idx}
              onClick={() => loadFileContent(activeRepo.id, filePath)}
              className="bg-github-dark hover:bg-github-hover border border-github-border hover:border-github-accent rounded-lg p-2.5 cursor-pointer transition text-xs flex items-center space-x-2 group"
            >
              <span className="w-5 h-5 rounded-full bg-blue-950 text-blue-400 font-bold text-[10px] flex items-center justify-center border border-blue-800">
                {idx + 1}
              </span>
              <span className="font-mono text-github-text group-hover:text-white truncate">{filePath}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-github-panel border border-github-border rounded-xl p-5 space-y-4 shadow-sm">
        <div className="flex items-center space-x-2 font-semibold text-white text-sm">
          <Layers className="w-4 h-4 text-github-purple" />
          <span>Step-by-Step Learning Roadmap</span>
        </div>

        <div className="space-y-3">
          {guide.learning_roadmap.map((step, sIdx) => (
            <div key={sIdx} className="bg-github-dark border border-github-border rounded-lg p-4 space-y-1">
              <div className="flex items-center space-x-2 font-medium text-xs text-github-accent">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>{step.step}</span>
              </div>
              <p className="text-xs text-github-muted leading-relaxed pl-6">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
