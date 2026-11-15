import React, { useState } from 'react';
import type { AlertRule, MarketAlert } from '../../types';
import {
  Bell,
  X,
  Plus,
  CheckCircle,
  AlertTriangle,
  Info,
  ShieldAlert,
  Trash2,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';

interface AlertsManagerModalProps {
  rules: AlertRule[];
  alerts: MarketAlert[];
  unreadCount: number;
  onClose: () => void;
  onAddRule: (rule: {
    name: string;
    condition_type: string;
    target_value?: string | null;
    min_confidence: number;
    enabled: boolean;
  }) => Promise<void>;
  onMarkRead: (alertId: number) => Promise<void>;
}

export const AlertsManagerModal: React.FC<AlertsManagerModalProps> = ({
  rules,
  alerts,
  unreadCount,
  onClose,
  onAddRule,
  onMarkRead,
}) => {
  const [activeTab, setActiveTab] = useState<'alerts' | 'rules'>('alerts');
  const [showAddForm, setShowAddForm] = useState<boolean>(false);

  // New Rule Form State
  const [ruleName, setRuleName] = useState<string>('');
  const [conditionType, setConditionType] = useState<string>('critical_impact');
  const [targetValue, setTargetValue] = useState<string>('');
  const [minConfidence, setMinConfidence] = useState<number>(0.80);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleSubmitRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ruleName.trim()) return;

    setIsSubmitting(true);
    try {
      await onAddRule({
        name: ruleName.trim(),
        condition_type: conditionType,
        target_value: targetValue.trim() ? targetValue.trim() : null,
        min_confidence: minConfidence,
        enabled: true,
      });
      setRuleName('');
      setTargetValue('');
      setShowAddForm(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 md:p-6 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#080e1c] border border-[#1b2b48] w-full max-w-3xl max-h-[85vh] rounded-2xl flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#16233b] flex items-center justify-between bg-[#0b1325]">
          <div className="flex items-center gap-3">
            <Bell className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white font-mono uppercase tracking-wider">
              Market Intelligence Alert Dispatcher
            </h3>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                {unreadCount} Unread
              </span>
            )}
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#16233b] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Controls */}
        <div className="flex border-b border-[#16233b] bg-[#070d18] px-6">
          <button
            onClick={() => setActiveTab('alerts')}
            className={`py-3 px-4 text-xs font-mono font-bold uppercase transition-all border-b-2 ${
              activeTab === 'alerts'
                ? 'border-cyan-400 text-white'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Triggered Notifications ({alerts.length})
          </button>
          <button
            onClick={() => setActiveTab('rules')}
            className={`py-3 px-4 text-xs font-mono font-bold uppercase transition-all border-b-2 ${
              activeTab === 'rules'
                ? 'border-cyan-400 text-white'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Configured Alert Rules ({rules.length})
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
          {activeTab === 'alerts' ? (
            alerts.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-xs font-mono space-y-2">
                <ShieldAlert className="w-8 h-8 text-slate-600 mx-auto" />
                <p>No active alerts triggered yet.</p>
                <p className="text-[11px] text-slate-600">
                  Alerts fire automatically when high/critical impact news or watchlist pairs are detected.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((al) => {
                  const sevColor =
                    al.severity === 'critical'
                      ? 'border-rose-500/40 bg-rose-500/10 text-rose-300'
                      : al.severity === 'warning'
                      ? 'border-amber-500/40 bg-amber-500/10 text-amber-300'
                      : 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300';

                  return (
                    <div
                      key={al.id}
                      className={`p-4 rounded-xl border flex items-start justify-between gap-3 ${
                        al.is_read ? 'bg-[#091122]/60 border-[#15233c]' : 'bg-[#0a1428] border-cyan-500/30 shadow-md'
                      }`}
                    >
                      <div className="space-y-1.5 flex-1">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${sevColor}`}>
                            {al.severity}
                          </span>
                          <span className="text-xs font-bold text-white font-mono">
                            {al.title}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono ml-auto">
                            {new Date(al.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{al.message}</p>
                      </div>

                      {!al.is_read && (
                        <button
                          onClick={() => onMarkRead(al.id)}
                          className="px-2.5 py-1 text-[11px] font-mono font-semibold rounded bg-[#101b33] text-cyan-400 hover:bg-[#16274b] border border-[#1b3158] transition-colors shrink-0"
                        >
                          Mark Read
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400 font-mono">
                  Custom criteria evaluated on incoming financial news feeds
                </span>
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-sm hover:opacity-90 transition-opacity"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>{showAddForm ? 'Cancel' : 'Add Rule'}</span>
                </button>
              </div>

              {/* Add Rule Form */}
              {showAddForm && (
                <form
                  onSubmit={handleSubmitRule}
                  className="bg-[#0b1428] border border-[#1b2f56] p-4 rounded-xl space-y-3"
                >
                  <h4 className="text-xs font-bold text-cyan-400 font-mono uppercase">
                    New Alert Trigger Condition
                  </h4>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] text-slate-400 block mb-1">Rule Name</label>
                      <input
                        type="text"
                        placeholder="e.g. BoE Unexpected Rate Cuts"
                        value={ruleName}
                        onChange={(e) => setRuleName(e.target.value)}
                        required
                        className="w-full bg-[#080e1d] border border-[#1b2b4a] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-400"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] text-slate-400 block mb-1">Condition Trigger</label>
                      <select
                        value={conditionType}
                        onChange={(e) => setConditionType(e.target.value)}
                        className="w-full bg-[#080e1d] border border-[#1b2b4a] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-400"
                      >
                        <option value="critical_impact">Critical Impact News (Score &ge; 75)</option>
                        <option value="high_impact">High Impact News (Score &ge; 50)</option>
                        <option value="watchlist_pair">Watchlist Pair Affected (e.g. EUR/USD)</option>
                        <option value="currency_mention">Currency Mentioned (e.g. USD, JPY)</option>
                        <option value="central_bank_event">Central Bank Event (e.g. Federal Reserve)</option>
                      </select>
                    </div>
                  </div>

                  {conditionType !== 'critical_impact' && conditionType !== 'high_impact' && (
                    <div>
                      <label className="text-[11px] text-slate-400 block mb-1">
                        Target Value (Pair, Currency code, or Central Bank name)
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. EUR/USD, GBP, or Bank of Japan"
                        value={targetValue}
                        onChange={(e) => setTargetValue(e.target.value)}
                        className="w-full bg-[#080e1d] border border-[#1b2b4a] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-400 font-mono"
                      />
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2">
                    <span className="text-xs font-mono text-slate-400">
                      Min Decider Confidence: <strong className="text-cyan-400">{(minConfidence * 100).toFixed(0)}%</strong>
                    </span>
                    <input
                      type="range"
                      min="0.50"
                      max="0.95"
                      step="0.05"
                      value={minConfidence}
                      onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                      className="w-32 accent-cyan-400 cursor-pointer"
                    />
                  </div>

                  <div className="flex justify-end pt-2">
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="px-4 py-1.5 rounded-lg text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-[#060b15] transition-colors disabled:opacity-50"
                    >
                      {isSubmitting ? 'Saving...' : 'Save Alert Rule'}
                    </button>
                  </div>
                </form>
              )}

              {/* Rules List */}
              <div className="space-y-2">
                {rules.map((r) => (
                  <div
                    key={r.id}
                    className="p-3 rounded-xl bg-[#0a1224] border border-[#15233c] flex items-center justify-between text-xs"
                  >
                    <div className="space-y-0.5">
                      <div className="font-bold text-white font-mono flex items-center gap-2">
                        <span>{r.name}</span>
                        {r.target_value && (
                          <span className="px-1.5 py-0.2 rounded bg-[#101b33] text-cyan-400 border border-[#1b2e50] text-[10px]">
                            {r.target_value}
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        Trigger: {r.condition_type} • Min Conviction: {(r.min_confidence * 100).toFixed(0)}%
                      </div>
                    </div>

                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      Active
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

