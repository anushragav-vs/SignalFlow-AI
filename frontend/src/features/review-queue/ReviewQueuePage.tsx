import React, { useState } from 'react';
import type { Signal, MarketSentiment } from '../../types';
import { api } from '../../lib/api-client';
import {
  ShieldAlert,
  CheckCircle,
  Edit3,
  XCircle,
  Sparkles,
  Loader2,
  AlertCircle,
  X,
} from 'lucide-react';

interface ReviewQueuePageProps {
  pendingItems: Signal[];
  onRefreshReviewQueue: () => Promise<void>;
}

export const ReviewQueuePage: React.FC<ReviewQueuePageProps> = ({
  pendingItems,
  onRefreshReviewQueue,
}) => {
  const [loadingId, setLoadingId] = useState<number | null>(null);
  const [selectedLabels, setSelectedLabels] = useState<Record<number, MarketSentiment>>({});
  const [reviewerNotes, setReviewerNotes] = useState<Record<number, string>>({});
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

  const showFeedback = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => {
      setNotification((prev) => (prev?.message === message ? null : prev));
    }, 5000);
  };

  const handleConfirm = async (id: number) => {
    setLoadingId(id);
    try {
      await api.confirmReview(id);
      showFeedback('success', `Signal #${id} approved! Google Gemini generated the deep research dossier.`);
      await onRefreshReviewQueue();
    } catch (err: any) {
      showFeedback('error', `Error approving review item: ${err.message}`);
    } finally {
      setLoadingId(null);
    }
  };

  const handleReclassify = async (id: number) => {
    const label = selectedLabels[id] || 'Bullish';
    const notes = reviewerNotes[id] || `Reclassified to ${label} by human reviewer`;
    setLoadingId(id);
    try {
      await api.reclassifyReview(id, label, notes);
      showFeedback('info', `Signal #${id} reclassified to ${label}. Original Decider output preserved.`);
      await onRefreshReviewQueue();
    } catch (err: any) {
      showFeedback('error', `Error reclassifying: ${err.message}`);
    } finally {
      setLoadingId(null);
    }
  };

  const handleDismiss = async (id: number) => {
    const notes = reviewerNotes[id] || 'Dismissed as non-actionable noise';
    setLoadingId(id);
    try {
      await api.dismissReview(id, notes);
      showFeedback('info', `Signal #${id} dismissed as noise.`);
      await onRefreshReviewQueue();
    } catch (err: any) {
      showFeedback('error', `Error dismissing: ${err.message}`);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          <h2 className="text-xl font-bold text-white tracking-tight">Human-in-the-Loop Review Queue</h2>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Low-confidence signals (&lt; 0.80 threshold) and policy edge cases are safely held here for supervisor
          oversight. Actions update the audit ledger while strictly preserving the original Strands Decider model output.
        </p>
      </div>

      {/* Styled Feedback Notification Banner */}
      {notification && (
        <div
          className={`p-4 rounded-xl text-xs flex items-center justify-between border animate-in fade-in duration-200 ${
            notification.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : notification.type === 'error'
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
          }`}
        >
          <div className="flex items-center gap-2 font-medium">
            {notification.type === 'success' && <CheckCircle className="w-4 h-4 shrink-0" />}
            {notification.type === 'error' && <AlertCircle className="w-4 h-4 shrink-0" />}
            {notification.type === 'info' && <Sparkles className="w-4 h-4 shrink-0" />}
            <span>{notification.message}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-white p-1 rounded transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {pendingItems.length === 0 ? (
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-12 text-center text-slate-400">
          <CheckCircle className="w-12 h-12 mx-auto text-emerald-400 mb-3" />
          <h3 className="text-lg font-bold text-white">Review Queue is Clean!</h3>
          <p className="text-xs text-slate-400 mt-1">
            All incoming headlines have been confidently classified or already approved by human oversight.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-xs font-semibold text-slate-400 flex items-center gap-2">
            <span>Pending items requiring verification:</span>
            <span className="font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full font-bold">
              {pendingItems.length}
            </span>
          </div>

          {pendingItems.map((item) => {
            const isLoading = loadingId === item.id;
            const currentSelectedLabel = selectedLabels[item.id] || 'Bullish';

            return (
              <div
                key={item.id}
                className="bg-[#0a1120] border border-[#1b2a47] hover:border-amber-500/40 rounded-2xl p-5 shadow-card transition-all"
              >
                {/* Meta Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#142138] text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-mono bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-bold">
                      #{item.id}
                    </span>
                    <span className="font-semibold text-slate-300">Decider Output:</span>
                    <span className="font-mono font-bold text-amber-400">{item.decider_sentiment}</span>
                    <span className="text-slate-600">•</span>
                    <span className="font-semibold text-slate-300">Confidence:</span>
                    <span className="font-mono font-bold text-cyan-400">
                      {(item.decider_confidence * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-slate-400">
                    <span>Source: {item.publisher}</span>
                    <span>•</span>
                    <span>{item.timestamp.slice(0, 16).replace('T', ' ')}</span>
                  </div>
                </div>

                {/* Headline */}
                <div className="my-3.5">
                  <h3 className="text-base font-bold text-white leading-snug">{item.headline}</h3>
                  <div className="mt-1 text-xs text-amber-400/90 font-medium flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>Escalation Reason: {item.policy_reason}</span>
                  </div>
                </div>

                {/* Interactive Triage Controls */}
                <div className="pt-3 border-t border-[#142138] flex flex-wrap items-center justify-between gap-3">
                  {/* Left: Reclassify Controls */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 font-medium">Reclassify to:</span>
                    <select
                      value={currentSelectedLabel}
                      onChange={(e) =>
                        setSelectedLabels({
                          ...selectedLabels,
                          [item.id]: e.target.value as MarketSentiment,
                        })
                      }
                      className="bg-[#060c18] border border-[#1b2a47] rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-400 font-mono"
                    >
                      <option value="Bullish">Bullish</option>
                      <option value="Bearish">Bearish</option>
                      <option value="Neutral">Neutral</option>
                      <option value="Noise">Noise</option>
                    </select>

                    <button
                      onClick={() => handleReclassify(item.id)}
                      disabled={isLoading}
                      className="px-3 py-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/40 text-amber-300 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    >
                      {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Edit3 className="w-3.5 h-3.5" />}
                      <span>Save Reclassification</span>
                    </button>
                  </div>

                  {/* Right: Confirm & Dismiss Buttons */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDismiss(item.id)}
                      disabled={isLoading}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    >
                      <XCircle className="w-3.5 h-3.5 text-rose-400" />
                      <span>Dismiss as Noise</span>
                    </button>

                    <button
                      onClick={() => handleConfirm(item.id)}
                      disabled={isLoading}
                      className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white text-xs font-bold shadow-md shadow-emerald-500/20 flex items-center gap-1.5 transition-all disabled:opacity-50"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Routing to Gemini...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>Approve & Send to Gemini</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
