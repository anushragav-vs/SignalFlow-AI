import React, { useState } from 'react';
import type { AppConfig, AppHealth, KPIs } from '../../types';
import { api } from '../../lib/api-client';
import {
  Settings,
  Sliders,
  Radio,
  Plus,
  Trash2,
  Database,
  Lock,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';

interface SettingsPageProps {
  config?: AppConfig;
  health?: AppHealth;
  kpis?: KPIs;
  feeds: Record<string, string>;
  onRefreshFeeds: () => Promise<void>;
  onRefreshConfig: () => Promise<void>;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  config,
  health,
  kpis,
  feeds,
  onRefreshFeeds,
  onRefreshConfig,
}) => {
  const [threshold, setThreshold] = useState<number>(config?.min_confidence_threshold ?? 0.8);
  const [modelId, setModelId] = useState<string>(config?.gemini_model_id ?? 'gemini-3.5-flash-lite');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // New feed form
  const [newFeedName, setNewFeedName] = useState('');
  const [newFeedUrl, setNewFeedUrl] = useState('');
  const [isAddingFeed, setIsAddingFeed] = useState(false);

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await api.updateConfig({
        min_confidence_threshold: threshold,
        gemini_model_id: modelId,
      });
      await onRefreshConfig();
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(`Save error: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddFeed = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFeedName.trim() || !newFeedUrl.trim()) return;
    setIsAddingFeed(true);
    try {
      await api.addFeed(newFeedName.trim(), newFeedUrl.trim());
      setNewFeedName('');
      setNewFeedUrl('');
      await onRefreshFeeds();
    } catch (err: any) {
      alert(`Error adding feed: ${err.message}`);
    } finally {
      setIsAddingFeed(false);
    }
  };

  const handleDeleteFeed = async (name: string) => {
    if (!confirm(`Are you sure you want to remove feed: ${name}?`)) return;
    try {
      await api.deleteFeed(name);
      await onRefreshFeeds();
    } catch (err: any) {
      alert(`Error deleting feed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-cyan-400" />
          <span>System Configuration & Policy Settings</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Adjust runtime policy thresholds, inspect active model checkpoints, and manage financial RSS ingestion feeds.
        </p>
      </div>

      {/* Model & Policy Settings Card */}
      <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-6 shadow-card">
        <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <Sliders className="w-4 h-4 text-brand-teal" />
          <span>Policy Thresholds & Model Parameters</span>
        </h3>

        <form onSubmit={handleSaveConfig} className="space-y-5">
          {/* Confidence Threshold */}
          <div>
            <div className="flex justify-between items-center text-xs font-semibold mb-2">
              <label htmlFor="confidence-threshold" className="text-slate-300">Minimum Policy Confidence Threshold</label>
              <span className="font-mono text-cyan-400 font-bold text-sm">
                {(threshold * 100).toFixed(0)}% ({threshold.toFixed(2)})
              </span>
            </div>
            <input
              id="confidence-threshold"
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full accent-brand-teal bg-slate-800 h-2 rounded-lg cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Classified headlines with calibrated confidence below this threshold are routed to the Human Review
              Queue rather than dispatched automatically to Google Gemini.
            </p>
          </div>

          {/* Gemini Model ID */}
          <div>
            <label htmlFor="gemini-model-select" className="block text-xs font-semibold text-slate-300 mb-2">Google Gemini Model ID</label>
            <select
              id="gemini-model-select"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              className="w-full bg-[#060c18] border border-[#1b2a47] rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-brand-teal font-mono"
            >
              <option value="gemini-3.5-flash-lite">gemini-3.5-flash-lite (Recommended - Fast & Economical)</option>
              <option value="gemini-3.8-flash">gemini-3.8-flash</option>
              <option value="gemini-2.5-flash">gemini-2.5-flash</option>
              <option value="gemini-2.5-pro">gemini-2.5-pro</option>
            </select>
          </div>

          {/* Security & Credentials info */}
          <div className="bg-[#060e1d] border border-[#142138] rounded-xl p-3.5 text-xs space-y-2">
            <div className="flex items-center gap-2 text-slate-400">
              <Lock className="w-3.5 h-3.5 text-amber-400" />
              <span>
                Gemini API Key: <code className="text-slate-200 font-mono">{config?.masked_api_key}</code>
              </span>
            </div>
            <div className="text-[11px] text-slate-500">
              API credentials are secure and loaded from backend environment variables (<code className="text-slate-400">.env</code>). They are never exposed to client-side JavaScript.
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2.5 rounded-xl bg-brand-teal text-slate-900 font-bold text-xs hover:bg-teal-400 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isSaving && <Loader2 className="w-4 h-4 animate-spin" />}
              <span>Save Policy Settings</span>
            </button>
            {saveSuccess && (
              <span className="text-xs text-emerald-400 flex items-center gap-1 font-semibold animate-in fade-in">
                <CheckCircle className="w-4 h-4" />
                <span>Settings saved to active session!</span>
              </span>
            )}
          </div>
        </form>
      </div>

      {/* RSS Feed Management Card */}
      <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-6 shadow-card">
        <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
          <Radio className="w-4 h-4 text-cyan-400" />
          <span>Configured RSS News Feeds</span>
        </h3>

        {/* Existing Feed List */}
        <div className="space-y-2 mb-4">
          {Object.entries(feeds).map(([name, url]) => (
            <div
              key={name}
              className="flex items-center justify-between p-3 rounded-xl bg-[#060c18] border border-[#142138] text-xs"
            >
              <div>
                <div className="font-bold text-white">{name}</div>
                <div className="text-[11px] text-slate-500 font-mono truncate max-w-md">{url}</div>
              </div>
              <button
                onClick={() => handleDeleteFeed(name)}
                className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg transition-colors"
                title="Delete Feed"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Add New Feed Form */}
        <form onSubmit={handleAddFeed} className="flex flex-col sm:flex-row gap-2 pt-3 border-t border-[#142138]">
          <input
            type="text"
            value={newFeedName}
            onChange={(e) => setNewFeedName(e.target.value)}
            placeholder="Feed Name e.g. Bloomberg Tech"
            className="w-full sm:w-1/3 bg-[#060c18] border border-[#1b2a47] rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
          <input
            type="url"
            value={newFeedUrl}
            onChange={(e) => setNewFeedUrl(e.target.value)}
            placeholder="Feed RSS URL https://..."
            className="flex-1 bg-[#060c18] border border-[#1b2a47] rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={isAddingFeed || !newFeedName.trim() || !newFeedUrl.trim()}
            className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5 shrink-0"
          >
            {isAddingFeed ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
            <span>Add Feed</span>
          </button>
        </form>
      </div>

      {/* SQLite Database Audit Status */}
      <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-5 shadow-card text-xs">
        <h3 className="font-bold text-white mb-2 flex items-center gap-2">
          <Database className="w-4 h-4 text-indigo-400" />
          <span>Local Audit Ledger Verification</span>
        </h3>
        <div className="text-slate-400 space-y-1 font-mono text-[11px]">
          <div>Database Path: <span className="text-slate-200">{config?.sqlite_db_path || 'signalflow.db'}</span></div>
          <div>Total Records: <span className="text-slate-200">{kpis?.total_received || 0}</span></div>
          <div>Audit Integrity: <span className="text-emerald-400 font-semibold">Immutable (Original classifications preserved)</span></div>
        </div>
      </div>
    </div>
  );
};
