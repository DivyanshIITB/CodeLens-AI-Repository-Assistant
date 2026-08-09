import React from 'react';
import { useAppStore } from './store/useAppStore';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatPanel } from './components/ChatPanel';
import { OverviewPanel } from './components/OverviewPanel';
import { ReadmePanel } from './components/ReadmePanel';
import { ApiDocsPanel } from './components/ApiDocsPanel';
import { OnboardingPanel } from './components/OnboardingPanel';
import { DependencyGraphPanel } from './components/DependencyGraphPanel';
import { CodeQualityPanel } from './components/CodeQualityPanel';
import { CodeViewerPanel } from './components/CodeViewerPanel';
import { RepoImportModal } from './components/RepoImportModal';
import { SettingsModal } from './components/SettingsModal';
import { EvalPanel } from './components/EvalPanel';

export const AppContent: React.FC = () => {
  const { activeTab } = useAppStore();

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatPanel />;
      case 'overview':
        return <OverviewPanel />;
      case 'readme':
        return <ReadmePanel />;
      case 'apidocs':
        return <ApiDocsPanel />;
      case 'onboarding':
        return <OnboardingPanel />;
      case 'graph':
        return <DependencyGraphPanel />;
      case 'quality':
        return <CodeQualityPanel />;
      case 'stats':
        return <OverviewPanel />;
      case 'eval':
        return <EvalPanel />;
      default:
        return <ChatPanel />;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-github-dark overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 flex overflow-hidden">
          {renderActiveTab()}
          <CodeViewerPanel />
        </main>
      </div>

      <RepoImportModal />
      <SettingsModal />
    </div>
  );
};

export function App() {
  return <AppContent />;
}

export default App;
