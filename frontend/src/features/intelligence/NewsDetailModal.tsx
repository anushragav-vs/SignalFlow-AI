import React, { useEffect, useState } from 'react';
import type { Signal } from '../../types';
import { api } from '../../lib/api-client';
import {
  X,
  ExternalLink,
  Clock,
  Radio,
  Cpu,
  Zap,
  TrendingUp,
  TrendingDown,
  MinusCircle,
  AlertTriangle,
  Layers,
  ShieldCheck,
  CheckCircle,
  BrainCircuit,
  Info,
  Calendar,
  BarChart2,
  RefreshCw,
  Sparkles,
  Bookmark,
  BookmarkCheck,
  Scale,
  FileText,
  Activity,
  ArrowRight,
  ShieldAlert,
  Loader2,
} from 'lucide-react';

interface NewsDetailModalProps {
  signal: Signal | null;
  onClose: () => void;
  onReanalyze?: (signalId: number, useGemini?: boolean) => Promise<void>;
  onFilterToTicker?: (symbol: string) => void;
  isReanalyzing?: boolean;
}

export const NewsDetailModal: React.FC<NewsDetailModalProps> = ({
  signal: initialSignal,
  onClose,
  onReanalyze,
  onFilterToTicker,
  isReanalyzing = false,
}) => {
  const [signal, setSignal] = useState<Signal | null>(initialSignal);
  const [loading, setLoading] = useState<boolean>(false);
  const [isAnalyzingGemini, setIsAnalyzingGemini] = useState<boolean>(false);
  const [isWatchlisted, setIsWatchlisted] = useState<boolean>(false);

  // Sync internal state when prop changes
  useEffect(() => {
    setSignal(initialSignal);
    if (initialSignal?.id) {
      // Check if watchlisted
      try {
        const stored = localStorage.getItem('signalflow_article_watchlist');
        const list: number[] = stored ? JSON.parse(stored) : [];
        setIsWatchlisted(list.includes(initialSignal.id));
      } catch {
        setIsWatchlisted(false);
      }

      // Fetch fresh details from backend to ensure complete intelligence fields
      setLoading(true);
      api
        .getIntelligenceNewsDetail(initialSignal.id)
        .then((freshSignal) => {
          setSignal(freshSignal);
          setLoading(false);
        })
        .catch(() => {
          // If error or offline, fallback to the passed prop signal
          setLoading(false);
        });
    }
  }, [initialSignal?.id]);

  // Lock background scroll and listen for Escape key
  useEffect(() => {
    if (!initialSignal) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    const origOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = origOverflow;
    };
  }, [initialSignal, onClose]);

  const toggleWatchlist = () => {
    if (!signal?.id) return;
    try {
      const stored = localStorage.getItem('signalflow_article_watchlist');
      const list: number[] = stored ? JSON.parse(stored) : [];
      const updated = list.includes(signal.id)
        ? list.filter((id) => id !== signal.id)
        : [...list, signal.id];
      localStorage.setItem('signalflow_article_watchlist', JSON.stringify(updated));
      setIsWatchlisted(!isWatchlisted);
    } catch (err) {
      console.error('Failed to update article watchlist:', err);
    }
  };

  const handleRunGemini = async () => {
    if (!signal?.id) return;
    setIsAnalyzingGemini(true);
    try {
      if (onReanalyze) {
        await onReanalyze(signal.id, true);
      }
      const updated = await api.reanalyzeArticleIntelligence(signal.id, true);
      setSignal(updated);
    } catch (err) {
      console.error('Failed to run Gemini analysis:', err);
    } finally {
      setIsAnalyzingGemini(false);
    }
  };

  if (!initialSignal) return null;
  const currentSignal = signal || initialSignal;

  const sentimentColor =
    currentSignal.decider_sentiment === 'Bullish'
      ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
      : currentSignal.decider_sentiment === 'Bearish'
      ? 'text-rose-400 bg-rose-500/10 border-rose-500/30'
      : currentSignal.decider_sentiment === 'Neutral'
      ? 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30'
      : 'text-slate-400 bg-slate-500/10 border-slate-500/30';

  const impactLvl = currentSignal.impact_level || 'LOW';
  const impactLevelColor =
    impactLvl === 'CRITICAL'
      ? 'text-rose-400 bg-rose-500/20 border-rose-500/40'
      : impactLvl === 'HIGH'
      ? 'text-amber-400 bg-amber-500/20 border-amber-500/40'
      : impactLvl === 'MEDIUM'
      ? 'text-cyan-400 bg-cyan-500/20 border-cyan-500/40'
      : 'text-slate-400 bg-slate-500/20 border-slate-500/40';

  const dims = currentSignal.impact_dimensions || {
    economic_importance: 0,
    surprise_magnitude: 0,
    instrument_relevance: 0,
    source_reliability: 0,
    news_novelty: 0,
    potential_volatility: 0,
  };

  const hasGemini =
    currentSignal.gemini_status === 'success' &&
    Boolean(currentSignal.event_summary || currentSignal.reported_facts?.length);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 md:p-6 bg-black/85 backdrop-blur-md animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-[#080e1c] border border-[#1b2b48] w-full max-w-4xl max-h-[92vh] rounded-2xl flex flex-col shadow-2xl overflow-hidden text-slate-100">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-[#16233b] flex items-center justify-between bg-[#0b1325] sticky top-0 z-20">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold uppercase tracking-wider bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              Article #{currentSignal.id}
            </span>
            <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold uppercase border ${impactLevelColor}`}>
              Impact: {impactLvl} ({currentSignal.impact_score || 0}/100)
            </span>
            <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold uppercase border ${sentimentColor}`}>
              Decider: {currentSignal.decider_sentiment} ({((currentSignal.decider_confidence || 0) * 100).toFixed(0)}%)
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleWatchlist}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all border ${
                isWatchlisted
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-[#0f1b34] text-slate-300 hover:text-white border-[#1e3258]'
              }`}
              title="Add or remove from research watchlist"
            >
              {isWatchlisted ? (
                <>
                  <BookmarkCheck className="w-3.5 h-3.5 text-amber-400" />
                  <span>Saved</span>
                </>
              ) : (
                <>
                  <Bookmark className="w-3.5 h-3.5 text-slate-400" />
                  <span>Save</span>
                </>
              )}
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#16233b] transition-colors"
              title="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm text-slate-300 custom-scrollbar">
          {loading && (
            <div className="py-2 px-3 bg-cyan-500/10 border border-cyan-500/20 rounded-xl text-cyan-400 text-xs flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Synchronizing deep intelligence metrics from audit ledger...</span>
            </div>
          )}

          {/* Section 1: Headline & Metadata */}
          <div className="space-y-3">
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight leading-snug">
              {currentSignal.headline}
            </h2>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
              <span className="flex items-center gap-1.5 font-medium text-slate-300">
                <Radio className="w-3.5 h-3.5 text-cyan-400" />
                {currentSignal.publisher}
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                {new Date(currentSignal.timestamp).toUTCString()}
              </span>
              <span className="text-[11px] font-mono text-slate-500">
                Ledger Status: {currentSignal.is_live ? 'Live Stream Ingestion' : 'Persisted Historical Audit'}
              </span>

              {currentSignal.canonical_url && currentSignal.canonical_url.startsWith('http') && (
                <a
                  href={currentSignal.canonical_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 transition-colors underline font-semibold ml-auto"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open Original Source</span>
                </a>
              )}
            </div>

            {/* Article Body or Graceful Fallback */}
            <div className="bg-[#0a1224] border border-[#16243e] rounded-xl p-4 text-xs text-slate-300 space-y-2">
              <div className="text-[11px] font-mono uppercase text-slate-400 font-bold flex items-center gap-2">
                <FileText className="w-3.5 h-3.5 text-cyan-400" />
                <span>Full Article Report</span>
              </div>
              <p className="leading-relaxed text-slate-200 whitespace-pre-line">
                {currentSignal.article_body ||
                  currentSignal.event_summary ||
                  `Full article wire dispatch was ingested and processed from ${currentSignal.publisher}. The complete original article is accessible directly on the publisher's portal using the source link above.`}
              </p>
            </div>
          </div>

          {/* Section 2: AI Classification & Policy Gatekeeper */}
          <div className="bg-[#0a1224] border border-[#16243e] rounded-xl p-4.5 space-y-3">
            <h3 className="text-xs font-mono font-bold tracking-wider uppercase text-cyan-400 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              Strands Decider 2B & Policy Gatekeeper
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="bg-[#0c1529] border border-[#172646] rounded-xl p-3 space-y-1">
                <span className="text-slate-400 text-[11px]">Sentiment Inference</span>
                <div className="text-sm font-extrabold text-white font-mono flex items-center gap-1.5">
                  {currentSignal.decider_sentiment === 'Bullish' && <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />}
                  {currentSignal.decider_sentiment === 'Bearish' && <TrendingDown className="w-3.5 h-3.5 text-rose-400" />}
                  {currentSignal.decider_sentiment === 'Neutral' && <MinusCircle className="w-3.5 h-3.5 text-cyan-400" />}
                  {currentSignal.decider_sentiment === 'Noise' && <AlertTriangle className="w-3.5 h-3.5 text-slate-400" />}
                  <span>{currentSignal.decider_sentiment}</span>
                </div>
              </div>

              <div className="bg-[#0c1529] border border-[#172646] rounded-xl p-3 space-y-1">
                <span className="text-slate-400 text-[11px]">Decider Confidence</span>
                <div className="text-sm font-extrabold text-cyan-400 font-mono">
                  {((currentSignal.decider_confidence || 0) * 100).toFixed(1)}%
                </div>
              </div>

              <div className="bg-[#0c1529] border border-[#172646] rounded-xl p-3 space-y-1">
                <span className="text-slate-400 text-[11px]">Processing Latency</span>
                <div className="text-sm font-extrabold text-white font-mono">
                  ⚡ {Math.round(currentSignal.decider_latency_ms || 0)} ms
                </div>
              </div>

              <div className="bg-[#0c1529] border border-[#172646] rounded-xl p-3 space-y-1">
                <span className="text-slate-400 text-[11px]">Policy Route</span>
                <div className="text-xs font-bold text-white font-mono uppercase">
                  {currentSignal.policy_action || 'APPROVE'}
                </div>
              </div>
            </div>

            {currentSignal.policy_reason && (
              <div className="text-xs text-slate-300 bg-[#0d162d] p-3 rounded-lg border border-[#192b4f] flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-white">Gatekeeper Rationale:</strong> {currentSignal.policy_reason}
                </div>
              </div>
            )}
          </div>

          {/* Section 3: Smart Ticker Detection & Affected Forex Pairs */}
          <div className="bg-[#0a1224] border border-[#16243e] rounded-xl p-4.5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono font-bold tracking-wider uppercase text-cyan-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                Smart Ticker Detection & Macro Transmission
              </h3>
              <span className="text-[11px] text-slate-500 font-mono">
                {currentSignal.affected_instruments?.length || 0} Affected Instruments
              </span>
            </div>

            {/* Detected Entities Badges */}
            {currentSignal.detected_entities && currentSignal.detected_entities.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[11px] font-mono text-slate-400">Detected Financial Entities:</span>
                <div className="flex flex-wrap gap-2">
                  {currentSignal.detected_entities.map((ent, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono bg-[#101b33] border border-[#1e3258] text-slate-200"
                    >
                      <span className="text-[10px] uppercase font-bold text-cyan-400">
                        [{ent.entity_type.replace('_', ' ')}]
                      </span>
                      {ent.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Affected Instruments Cards */}
            {currentSignal.affected_instruments && currentSignal.affected_instruments.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                {currentSignal.affected_instruments.map((inst, idx) => {
                  const relBadge =
                    inst.relationship === 'direct'
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                      : inst.relationship === 'indirect'
                      ? 'bg-blue-500/20 text-blue-300 border-blue-500/40'
                      : 'bg-purple-500/20 text-purple-300 border-purple-500/40';

                  return (
                    <div
                      key={idx}
                      className="bg-[#0d162b] border border-[#182745] rounded-lg p-3 space-y-2 hover:border-cyan-500/40 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-base font-extrabold text-white font-mono tracking-tight">
                          {inst.symbol}
                        </span>
                        <div className="flex items-center gap-1.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${relBadge}`}>
                            {inst.relationship}
                          </span>
                          <span className="text-[11px] font-mono text-slate-400">
                            {(inst.confidence * 100).toFixed(0)}% conf
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        {inst.reason}
                      </p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">
                No specific forex pairs met the transmission confidence threshold for this event.
              </p>
            )}
          </div>

          {/* Section 4: Market Impact Predictor Analysis */}
          <div className="bg-[#0a1224] border border-[#16243e] rounded-xl p-4.5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono font-bold tracking-wider uppercase text-cyan-400 flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-cyan-400" />
                Market Impact Analysis & 6 Normalized Dimensions
              </h3>
              <span className="text-xs font-mono text-slate-400">
                Category: <strong className="text-white capitalize">{currentSignal.event_category?.replace(/_/g, ' ')}</strong>
              </span>
            </div>

            {/* Impact Explanation */}
            {currentSignal.impact_explanation && (
              <p className="text-xs md:text-sm text-slate-200 bg-[#0e172e] p-3 rounded-lg border border-[#1a2d52] leading-relaxed">
                {currentSignal.impact_explanation}
              </p>
            )}

            {/* 6 Dimensions Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 pt-1">
              {[
                { label: 'Economic Importance', value: dims.economic_importance, weight: '25%' },
                { label: 'Surprise Magnitude', value: dims.surprise_magnitude, weight: '20%' },
                { label: 'Instrument Relevance', value: dims.instrument_relevance, weight: '20%' },
                { label: 'Source Reliability', value: dims.source_reliability, weight: '10%' },
                { label: 'News Novelty', value: dims.news_novelty, weight: '10%' },
                { label: 'Potential Volatility', value: dims.potential_volatility, weight: '15%' },
              ].map((d, i) => (
                <div key={i} className="bg-[#0c1529] border border-[#162543] rounded-lg p-2.5 space-y-1.5">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400 font-medium">{d.label}</span>
                    <span className="font-mono font-bold text-white">{d.value}/100</span>
                  </div>
                  <div className="w-full bg-[#142038] h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        d.value >= 75
                          ? 'bg-rose-500'
                          : d.value >= 50
                          ? 'bg-amber-400'
                          : d.value >= 25
                          ? 'bg-cyan-400'
                          : 'bg-slate-500'
                      }`}
                      style={{ width: `${d.value}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono text-right">
                    Weight: {d.weight}
                  </div>
                </div>
              ))}
            </div>

            {/* Distinct Callout: Predicted Impact vs Confirmed Reaction */}
            <div className="text-[11px] text-slate-400 bg-[#091122] p-3 rounded-lg border border-[#16243e] space-y-1">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <Scale className="w-3.5 h-3.5 text-cyan-400" />
                Decoupled Impact Principle & Methodology Note:
              </span>
              <p className="text-slate-400 leading-relaxed">
                Market Impact Score ({currentSignal.impact_score}/100) estimates <em>potential macroeconomic significance</em> and expected volatility dispersion. It is strictly separated from price direction and does not imply guaranteed returns. Actual market reaction depends on pre-event positioning and market consensus expectations.
              </p>
            </div>
          </div>

          {/* Section 5: Gemini Deep Research Intelligence */}
          <div className="bg-[#0a1224] border border-[#16243e] rounded-xl p-4.5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono font-bold tracking-wider uppercase text-cyan-400 flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-cyan-400" />
                Google Gemini 3.5 Synthesis & 8-Factor Research Dossier
              </h3>
              {hasGemini && (
                <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" />
                  Synthesis Generated
                </span>
              )}
            </div>

            {hasGemini ? (
              <div className="space-y-4">
                {currentSignal.event_summary && (
                  <div className="bg-[#0d162d] border border-[#192b4f] p-3.5 rounded-lg space-y-1">
                    <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wide">
                      Executive Summary:
                    </span>
                    <p className="text-xs text-slate-200 leading-relaxed">
                      {currentSignal.event_summary}
                    </p>
                  </div>
                )}

                {currentSignal.reported_facts && currentSignal.reported_facts.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-bold text-slate-200">1. Source-Reported Objective Facts:</span>
                    <ul className="list-disc list-inside space-y-1 text-xs text-slate-300 pl-2">
                      {currentSignal.reported_facts.map((fact, idx) => (
                        <li key={idx}>{fact}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {currentSignal.analytical_hypotheses && currentSignal.analytical_hypotheses.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-bold text-slate-200">2. Analytical Hypotheses & Directional Implications:</span>
                    <ul className="list-disc list-inside space-y-1 text-xs text-slate-300 pl-2">
                      {currentSignal.analytical_hypotheses.map((hypo, idx) => (
                        <li key={idx}>{hypo}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {currentSignal.catalyst_watchpoints && currentSignal.catalyst_watchpoints.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-bold text-slate-200">3. Upcoming Catalyst Watchpoints:</span>
                    <ul className="list-disc list-inside space-y-1 text-xs text-slate-300 pl-2">
                      {currentSignal.catalyst_watchpoints.map((cat, idx) => (
                        <li key={idx}>{cat}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-5 bg-[#091122] border border-[#16243e] rounded-xl flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="space-y-1">
                  <span className="text-xs font-bold text-white">Gemini Synthesis Not Yet Generated</span>
                  <p className="text-[11px] text-slate-400">
                    This headline was classified locally at the edge by Strands Decider 2B ($0.00 cloud tokens). You can run Google Gemini on demand.
                  </p>
                </div>
                <button
                  onClick={handleRunGemini}
                  disabled={isAnalyzingGemini}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 via-cyan-500 to-teal-500 text-white font-semibold text-xs shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 shrink-0"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${isAnalyzingGemini ? 'animate-spin' : ''}`} />
                  <span>{isAnalyzingGemini ? 'Synthesizing...' : 'Analyze with Gemini 3.5'}</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Modal Bottom Action Footer */}
        <div className="px-6 py-4 border-t border-[#16233b] bg-[#091122] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {currentSignal.canonical_url && currentSignal.canonical_url.startsWith('http') && (
              <a
                href={currentSignal.canonical_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#111c34] hover:bg-[#18284b] border border-[#1f335b] text-cyan-300 transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Open Source Article</span>
              </a>
            )}

            {!hasGemini && (
              <button
                onClick={handleRunGemini}
                disabled={isAnalyzingGemini}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 transition-colors disabled:opacity-50"
              >
                <Sparkles className={`w-3.5 h-3.5 ${isAnalyzingGemini ? 'animate-spin' : ''}`} />
                <span>{isAnalyzingGemini ? 'Analyzing...' : 'Analyze with Gemini'}</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-[#111c34] hover:bg-[#18284b] border border-[#1f335b] text-slate-300 hover:text-white transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
