import React, { createContext, useContext, useState, useEffect } from 'react';
import { Repository, TreeNode, ChatMessage, Citation, OllamaModel, AppSettings } from '../types';
import { api } from '../services/api';

interface AppContextType {
  repos: Repository[];
  activeRepo: Repository | null;
  setActiveRepo: (repo: Repository | null) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeFile: { path: string; content: string; highlightLines?: [number, number] } | null;
  setActiveFile: (file: { path: string; content: string; highlightLines?: [number, number] } | null) => void;
  chatMessages: ChatMessage[];
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  activeCitations: Citation[];
  setActiveCitations: (citations: Citation[]) => void;
  models: OllamaModel[];
  selectedModel: string;
  setSelectedModel: (model: string) => void;
  settings: AppSettings;
  setSettings: (settings: AppSettings) => void;
  isImportModalOpen: boolean;
  setIsImportModalOpen: (open: boolean) => void;
  isSettingsModalOpen: boolean;
  setIsSettingsModalOpen: (open: boolean) => void;
  refreshRepos: () => Promise<void>;
  loadFileContent: (repoId: string, path: string, highlightLines?: [number, number]) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [activeRepo, setActiveRepo] = useState<Repository | null>(null);
  const [activeTab, setActiveTab] = useState<string>('chat');
  const [activeFile, setActiveFile] = useState<{ path: string; content: string; highlightLines?: [number, number] } | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'ai',
      text: 'Hello! I am **CodeLens AI**, your intelligent GitHub repository assistant. Select or import a repository to ask questions, explore architecture, generate REST API docs, view dependency graphs, and inspect code smells.'
    }
  ]);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('qwen2.5-coder:1.5b');
  const [settings, setSettingsState] = useState<AppSettings>({
    default_model: 'qwen2.5-coder:1.5b',
    embedding_model: 'BAAI/bge-small-en-v1.5',
    top_k: 6,
    chunk_size: 512,
    chunk_overlap: 64,
    temperature: 0.2,
    theme: 'github-dark'
  });
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState<boolean>(false);

  const handleSetActiveRepo = (repo: Repository | null) => {
    setActiveRepo(repo);
    if (repo) {
      localStorage.setItem('codelens_active_repo_id', repo.id);
    } else {
      localStorage.removeItem('codelens_active_repo_id');
    }
  };

  const refreshRepos = async () => {
    try {
      const data = await api.listRepos();
      setRepos(data);
      if (data.length > 0) {
        const savedId = localStorage.getItem('codelens_active_repo_id');
        const matched = data.find(r => r.id === savedId);
        if (matched) {
          setActiveRepo(matched);
        } else {
          setActiveRepo(data[0]);
          localStorage.setItem('codelens_active_repo_id', data[0].id);
        }
      } else {
        setActiveRepo(null);
        localStorage.removeItem('codelens_active_repo_id');
      }

    } catch (e) {
      console.error('Failed to load repositories', e);
    }
  };


  const loadModels = async () => {
    try {
      const mList = await api.listModels();
      setModels(mList);
      if (mList.length > 0 && !mList.find(m => m.name === selectedModel)) {
        setSelectedModel(mList[0].name);
      }
    } catch (e) {
      console.error('Failed to load Ollama models', e);
    }
  };

  const loadSettings = async () => {
    try {
      const s = await api.getSettings();
      setSettingsState(s);
    } catch (e) {
      console.error('Failed to load settings', e);
    }
  };

  useEffect(() => {
    refreshRepos();
    loadModels();
    loadSettings();
  }, []);

  const loadFileContent = async (repoId: string, path: string, highlightLines?: [number, number]) => {
    try {
      const res = await api.readRepoFile(repoId, path);
      setActiveFile({
        path: res.file_path,
        content: res.content,
        highlightLines
      });
    } catch (e) {
      console.error('Failed reading file content', e);
    }
  };

  return (
    <AppContext.Provider
      value={{
        repos,
        activeRepo,
        setActiveRepo: handleSetActiveRepo,
        activeTab,

        setActiveTab,
        activeFile,
        setActiveFile,
        chatMessages,
        setChatMessages,
        activeCitations,
        setActiveCitations,
        models,
        selectedModel,
        setSelectedModel,
        settings,
        setSettings: setSettingsState,
        isImportModalOpen,
        setIsImportModalOpen,
        isSettingsModalOpen,
        setIsSettingsModalOpen,
        refreshRepos,
        loadFileContent
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppStore = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppStore must be used within an AppProvider');
  }
  return context;
};
