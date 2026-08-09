import React, { useState } from 'react';
import { X, GitPullRequest, UploadCloud, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

export const RepoImportModal: React.FC = () => {
  const { isImportModalOpen, setIsImportModalOpen, refreshRepos, setActiveRepo } = useAppStore();
  const [activeTab, setActiveTab] = useState<'url' | 'upload'>('url');
  const [repoUrl, setRepoUrl] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [error, setError] = useState<string>('');

  if (!isImportModalOpen) return null;

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setLoading(true);
    setError('');
    setStatusMessage('Cloning repository and running Tree-sitter AST indexing...');

    try {
      const repo = await api.importRepoUrl(repoUrl.trim());
      await refreshRepos();
      setActiveRepo(repo);
      setIsImportModalOpen(false);
      setRepoUrl('');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to import repository.');
    } finally {
      setLoading(false);
      setStatusMessage('');
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    setError('');
    setStatusMessage('Extracting ZIP archive and generating local FAISS vector embeddings...');

    try {
      const repo = await api.uploadRepoZip(selectedFile);
      await refreshRepos();
      setActiveRepo(repo);
      setIsImportModalOpen(false);
      setSelectedFile(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to upload repository zip.');
    } finally {
      setLoading(false);
      setStatusMessage('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-github-panel border border-github-border rounded-xl w-full max-w-lg shadow-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-github-border flex items-center justify-between">
          <div className="flex items-center space-x-2 font-semibold text-white">
            <GitPullRequest className="w-5 h-5 text-github-accent" />
            <span>Import Repository</span>
          </div>
          <button
            onClick={() => !loading && setIsImportModalOpen(false)}
            className="text-github-muted hover:text-white p-1 rounded-md transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex border-b border-github-border bg-github-dark">
          <button
            onClick={() => setActiveTab('url')}
            className={`flex-1 py-2.5 text-xs font-medium text-center border-b-2 transition ${
              activeTab === 'url'
                ? 'border-github-accent text-github-accent bg-github-panel'
                : 'border-transparent text-github-muted hover:text-white'
            }`}
          >
            GitHub Repository URL
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex-1 py-2.5 text-xs font-medium text-center border-b-2 transition ${
              activeTab === 'upload'
                ? 'border-github-accent text-github-accent bg-github-panel'
                : 'border-transparent text-github-muted hover:text-white'
            }`}
          >
            Upload Local ZIP Archive
          </button>
        </div>

        <div className="p-5">
          {error && (
            <div className="mb-4 p-3 bg-red-950/60 border border-red-800/60 rounded-lg text-xs text-red-300 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {activeTab === 'url' ? (
            <form onSubmit={handleUrlSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-github-text mb-1">
                  GitHub Public or Internal Repository HTTPS URL
                </label>
                <input
                  type="url"
                  placeholder="https://github.com/fastapi/fastapi"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  disabled={loading}
                  className="w-full bg-github-dark border border-github-border rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-github-accent placeholder-github-muted"
                  required
                />
              </div>

              <div className="text-[11px] text-github-muted bg-github-dark p-3 rounded-lg border border-github-border/60 space-y-1">
                <p>• Clones via GitPython with fallback to direct archive ZIP fetching.</p>
                <p>• Parses AST symbols (Classes, Functions, Methods) via Tree-sitter.</p>
                <p>• Generates vector embeddings locally using BAAI/bge-small-en-v1.5.</p>
              </div>

              <button
                type="submit"
                disabled={loading || !repoUrl.trim()}
                className="w-full bg-github-green hover:bg-green-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg text-sm transition flex items-center justify-center space-x-2 shadow"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Indexing Repository...</span>
                  </>
                ) : (
                  <span>Import & Build RAG Index</span>
                )}
              </button>
            </form>
          ) : (
            <form onSubmit={handleFileUpload} className="space-y-4">
              <div className="border-2 border-dashed border-github-border hover:border-github-accent rounded-xl p-6 text-center cursor-pointer transition bg-github-dark">
                <input
                  type="file"
                  accept=".zip"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="zip-upload-input"
                  disabled={loading}
                />
                <label htmlFor="zip-upload-input" className="cursor-pointer block">
                  <UploadCloud className="w-10 h-10 text-github-accent mx-auto mb-2" />
                  {selectedFile ? (
                    <div className="flex items-center justify-center space-x-1.5 text-xs text-white">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span className="font-medium">{selectedFile.name}</span>
                    </div>
                  ) : (
                    <>
                      <p className="text-xs font-medium text-white mb-1">Click or drag & drop ZIP file here</p>
                      <p className="text-[11px] text-github-muted">Supports local project directories compressed as .zip</p>
                    </>
                  )}
                </label>
              </div>

              <button
                type="submit"
                disabled={loading || !selectedFile}
                className="w-full bg-github-green hover:bg-green-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg text-sm transition flex items-center justify-center space-x-2 shadow"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing Archive...</span>
                  </>
                ) : (
                  <span>Upload & Build RAG Index</span>
                )}
              </button>
            </form>
          )}

          {loading && (
            <div className="mt-4 p-3 bg-github-dark rounded-lg border border-github-border text-xs text-github-accent flex items-center space-x-2 animate-pulse">
              <Loader2 className="w-4 h-4 animate-spin shrink-0" />
              <span>{statusMessage}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
