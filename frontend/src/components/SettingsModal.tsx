import React, { useState } from 'react';
import { X, Settings as SettingsIcon, Save } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

export const SettingsModal: React.FC = () => {
  const { isSettingsModalOpen, setIsSettingsModalOpen, settings, setSettings, models } = useAppStore();
  const [formData, setFormData] = useState(settings);
  const [saving, setSaving] = useState<boolean>(false);

  if (!isSettingsModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await api.updateSettings(formData);
      setSettings(updated);
      setIsSettingsModalOpen(false);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-github-panel border border-github-border rounded-xl w-full max-w-lg shadow-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-github-border flex items-center justify-between">
          <div className="flex items-center space-x-2 font-semibold text-white">
            <SettingsIcon className="w-5 h-5 text-github-accent" />
            <span>CodeLens RAG & LLM Settings</span>
          </div>
          <button
            onClick={() => setIsSettingsModalOpen(false)}
            className="text-github-muted hover:text-white p-1 rounded-md transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          <div>
            <label className="block text-github-text font-medium mb-1">Active LLM Model</label>
            <select
              value={formData.default_model}
              onChange={(e) => setFormData({ ...formData, default_model: e.target.value })}
              className="w-full bg-github-dark border border-github-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-github-accent"
            >
              {models.map(m => (
                <option key={m.name} value={m.name}>{m.name} ({m.size_human})</option>
              ))}
            </select>
          </div>

          <div>
            <div className="flex justify-between font-medium text-github-text mb-1">
              <span>Top-K Chunks Retrieved</span>
              <span className="text-github-accent font-mono">{formData.top_k}</span>
            </div>
            <input
              type="range"
              min="2"
              max="15"
              value={formData.top_k}
              onChange={(e) => setFormData({ ...formData, top_k: parseInt(e.target.value) })}
              className="w-full accent-blue-500"
            />
          </div>

          <div>
            <div className="flex justify-between font-medium text-github-text mb-1">
              <span>Generation Temperature</span>
              <span className="text-github-accent font-mono">{formData.temperature}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={formData.temperature}
              onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
              className="w-full accent-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-github-text font-medium mb-1">AST Chunk Size (tokens)</label>
              <input
                type="number"
                value={formData.chunk_size}
                onChange={(e) => setFormData({ ...formData, chunk_size: parseInt(e.target.value) })}
                className="w-full bg-github-dark border border-github-border rounded-lg px-3 py-2 text-white focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-github-text font-medium mb-1">Overlap (tokens)</label>
              <input
                type="number"
                value={formData.chunk_overlap}
                onChange={(e) => setFormData({ ...formData, chunk_overlap: parseInt(e.target.value) })}
                className="w-full bg-github-dark border border-github-border rounded-lg px-3 py-2 text-white focus:outline-none"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-github-border flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="bg-github-accent hover:bg-blue-600 text-white font-medium px-4 py-2 rounded-lg text-xs flex items-center space-x-1.5 transition shadow"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Settings</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
