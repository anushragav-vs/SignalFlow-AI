import React, { useState } from 'react';
import type { Signal, MarketSentiment } from '../../types';
import { api } from '../../lib/api-client';
import {
  Search,
  Sparkles,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Clock,
  Radio,
  Send,
  Loader2,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  MinusCircle,
  AlertTriangle,
  Cpu,
  Zap,
  X,
  ShieldCheck,
  Activity,
  Layers,
  Lightbulb,
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface NewsStreamPageProps {
  signals: Signal[];
  feeds: Record<string, string>;
  onRefreshSignals: () => Promise<void>;
  onSelectStock?: (symbol: string) => void;
}

export const NewsStreamPage: React.FC<NewsStreamPageProps> = ({
  signals,
  feeds,
  onRefreshSignals,
  onSelectStock,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFeed, setSelectedFeed] = useState<string>('All Feeds');
  const [filterNonFinancial, setFilterNonFinancial] = useState<boolean>(true);
  const [categoryFilter, setCategoryFilter] = useState<string>('All Financial');
  const [isFetching, setIsFetching] = useState(false);
  const [isEvaluatingManual, setIsEvaluatingManual] = useState(false);
  const [manualHeadline, setManualHeadline] = useState('');
  const [showManualInput, setShowManualInput] = useState(false);
  const [lastEvaluatedSignal, setLastEvaluatedSignal] = useState<Signal | null>(null);
  const [expandedSignalId, setExpandedSignalId] = useState<number | null>(null);

  // Extract smart financial hashtags
  const getArticleTags = (headline: string, sentiment: MarketSentiment): string[] => {
    const h = headline.toLowerCase();
    const tags: string[] = [];
    if (/(ai|nvidia|chip|semiconductor|tsmc|gpu|arm)/.test(h)) tags.push('#ai technology', '#semiconductors');
    if (/(fed|rate|inflation|cpi|powell|yield|treasury)/.test(h)) tags.push('#monetary policy', '#interest rates');
    if (/(earnings|revenue|profit|margin|income|q3|q4)/.test(h)) tags.push('#earnings beat', '#corporate finance');
    if (/(tesla|ev|automotive|rivian|byd)/.test(h)) tags.push('#electric vehicles', '#automotive');
    if (/(stock|shares|jump|surge|rally|gain)/.test(h)) tags.push('#stock rally');
    if (/(drop|fall|slump|plunge|decline|selloff)/.test(h)) tags.push('#valuation risk');
    if (sentiment === 'Bullish') tags.push('#growth catalyst');
    else if (sentiment === 'Bearish') tags.push('#macro headwind');
    else tags.push('#market update');
    return Array.from(new Set(tags)).slice(0, 4);
  };

  // Filter signals based on search query
  const searchFiltered = signals.filter((s) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return s.headline.toLowerCase().includes(q) || s.publisher.toLowerCase().includes(q);
  });

  // Calculate sentiment statistics for the summary card
  const totalCount = searchFiltered.length;
  const posCount = searchFiltered.filter((s) => s.decider_sentiment === 'Bullish').length;
  const negCount = searchFiltered.filter((s) => s.decider_sentiment === 'Bearish').length;
  const neuCount = searchFiltered.filter((s) => s.decider_sentiment === 'Neutral').length;
  const noiCount = searchFiltered.filter((s) => s.decider_sentiment === 'Noise').length;
  const revCount = searchFiltered.filter((s) => s.policy_action === 'REVIEW_QUEUE').length;
  const financialCount = posCount + negCount + neuCount + revCount;

  let overallBias: 'Bullish' | 'Bearish' | 'Neutral' = 'Neutral';
  if (posCount > negCount && posCount >= neuCount) overallBias = 'Bullish';
  else if (negCount > posCount && negCount >= neuCount) overallBias = 'Bearish';

  const denom = Math.max(totalCount, 1);
  const posPct = Math.round((posCount / denom) * 100);
  const neuPct = Math.round((neuCount / denom) * 100);
  const negPct = Math.round((negCount / denom) * 100);

  // Apply category pill filter with non-financial noise avoidance
  const displaySignals = searchFiltered.filter((s) => {
    // When non-financial filter is active, automatically drop Noise from financial views
    if (filterNonFinancial && categoryFilter !== 'Non-Financial Noise' && categoryFilter !== 'Noise' && s.decider_sentiment === 'Noise') {
      return false;
    }

    if (categoryFilter === 'All Financial') return s.decider_sentiment !== 'Noise';
    if (categoryFilter === 'All') return !filterNonFinancial || s.decider_sentiment !== 'Noise';
    if (categoryFilter === 'Positive') return s.decider_sentiment === 'Bullish';
    if (categoryFilter === 'Negative') return s.decider_sentiment === 'Bearish';
    if (categoryFilter === 'Neutral') return s.decider_sentiment === 'Neutral';
    if (categoryFilter === 'Non-Financial Noise' || categoryFilter === 'Noise') return s.decider_sentiment === 'Noise';
    if (categoryFilter === 'Review Queue') return s.policy_action === 'REVIEW_QUEUE';
    return true;
  });

  // Handle feed refresh
  const handleFetchFeed = async () => {
    setIsFetching(true);
    try {
      await api.fetchFeed(selectedFeed, 6);
      await onRefreshSignals();
    } catch (err: any) {
      alert(`Error fetching feed: ${err.message}`);
    } finally {
      setIsFetching(false);
    }
  };

  // Handle manual headline evaluation
  const handleManualSubmit = async (e?: React.FormEvent, customText?: string) => {
    if (e) e.preventDefault();
    const textToEvaluate = customText || manualHeadline;
    if (!textToEvaluate.trim()) return;

    setIsEvaluatingManual(true);
    try {
      const res = await api.evaluateHeadline(textToEvaluate.trim());
      setLastEvaluatedSignal(res);
      setManualHeadline('');
      setShowManualInput(true);
      await onRefreshSignals();
    } catch (err: any) {
      alert(`Evaluation error: ${err.message}`);
    } finally {
      setIsEvaluatingManual(false);
    }
  };

  // Donut chart data
  const donutData =
    totalCount > 0
      ? [
          { name: 'Positive', value: posCount, color: '#10b981' },
          { name: 'Neutral', value: neuCount, color: '#475569' },
          { name: 'Negative', value: negCount, color: '#ef4444' },
        ]
      : [{ name: 'No Data', value: 1, color: '#1e293b' }];

  return (
    <div className="space-y-5">
      {/* 1. Top Search & Action Bar (SentimentIQ Style) */}
      <div className="flex flex-col md:flex-row items-stretch gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search Ticker or Headline e.g. NVDA, AAPL, Tesla, Fed, Margin, Revenue..."
            className="w-full bg-[#0a1120] border border-[#1b2a47] rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue shadow-inner"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-white"
            >
              Clear
            </button>
          )}
        </div>

        {/* Source Selector */}
        <div className="flex items-center gap-2">
          <select
            value={selectedFeed}
            onChange={(e) => setSelectedFeed(e.target.value)}
            className="bg-[#0a1120] border border-[#1b2a47] rounded-xl px-3.5 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-blue"
          >
            <option value="All Feeds">⚡ Multi-Stream (All Live Feeds)</option>
            {Object.keys(feeds).map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>

          {/* Glowing Analyze News Button */}
          <button
            onClick={handleFetchFeed}
            disabled={isFetching}
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-blue-600 via-cyan-500 to-teal-500 text-white font-semibold text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 shrink-0"
          >
            {isFetching ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Evaluating...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Analyze News</span>
              </>
            )}
          </button>

          {/* Toggle Manual Input Button */}
          <button
            onClick={() => setShowManualInput(!showManualInput)}
            className={`flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-semibold transition-all shrink-0 ${
              showManualInput
                ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300 shadow-lg shadow-cyan-500/10'
                : 'bg-[#0d162a] border-[#1b2a47] hover:border-slate-500 text-slate-300'
            }`}
            title="Custom Headline Analyzer"
          >
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>Custom Headline</span>
          </button>
        </div>
      </div>

      {/* Manual Input Drawer if toggled */}
      {showManualInput && (
        <div className="bg-[#0c1527] border border-[#1e2f50] rounded-2xl p-5 shadow-xl space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Custom Financial Headline Analyzer</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                    Strands Decider 2B
                  </span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Classify custom headlines into Bullish, Bearish, Neutral, or Noise with calibrated confidence readout.
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowManualInput(false)}
              className="text-slate-500 hover:text-white p-1 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Quick preset headline pills */}
          <div className="space-y-1.5">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Quick Test Presets</div>
            <div className="flex flex-wrap gap-2">
              {[
                { label: '🚀 Bullish Growth', text: 'NVIDIA reports record Q3 revenue of $35.1B up 94% driven by AI compute demand' },
                { label: '📉 Bearish Slump', text: 'Tesla automotive gross margin slumps to 14.6% amid intense global EV price cuts' },
                { label: '⚖️ Fed Rate Decision', text: 'Federal Reserve holds benchmark policy rate unchanged at 5.25%-5.50% target range' },
                { label: '☕ Lifestyle Noise', text: 'Celebrity chef opens luxury Italian restaurant in downtown Manhattan with private tasting room' },
              ].map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setManualHeadline(p.text);
                    handleManualSubmit(undefined, p.text);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-[#070c18] border border-[#1b2a47] hover:border-cyan-500/40 text-xs text-slate-300 hover:text-white transition-all flex items-center gap-1.5"
                >
                  <span>{p.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Input Form */}
          <form onSubmit={(e) => handleManualSubmit(e)} className="flex gap-3 items-center">
            <input
              type="text"
              value={manualHeadline}
              onChange={(e) => setManualHeadline(e.target.value)}
              placeholder="Enter custom financial headline or breaking wire event..."
              className="flex-1 bg-[#070c18] border border-[#16233b] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 shadow-inner"
            />
            <button
              type="submit"
              disabled={isEvaluatingManual || !manualHeadline.trim()}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold text-sm hover:from-teal-400 hover:to-cyan-400 transition-all disabled:opacity-50 flex items-center gap-2 shrink-0 shadow-lg shadow-teal-500/20"
            >
              {isEvaluatingManual ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Evaluating...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  <span>Analyze Headline</span>
                </>
              )}
            </button>
          </form>

          {/* Evaluated Result Preview Card */}
          {lastEvaluatedSignal && (
            <div className="p-4 rounded-xl bg-[#080e1c] border border-cyan-500/30 space-y-3 animate-in fade-in slide-in-from-top-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-3 py-1 rounded-lg text-xs font-bold font-mono uppercase tracking-wider ${
                      lastEvaluatedSignal.decider_sentiment === 'Bullish'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : lastEvaluatedSignal.decider_sentiment === 'Bearish'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                        : lastEvaluatedSignal.decider_sentiment === 'Neutral'
                        ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    }`}
                  >
                    {lastEvaluatedSignal.decider_sentiment}
                  </span>
                  <span className="text-xs font-mono text-cyan-400 font-bold">
                    {(lastEvaluatedSignal.decider_confidence * 100).toFixed(1)}% Confidence
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    ({lastEvaluatedSignal.decider_latency_ms?.toFixed(0) || '0'} ms CPU)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-mono ${
                      lastEvaluatedSignal.policy_action === 'APPROVE'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : lastEvaluatedSignal.policy_action === 'REVIEW_QUEUE'
                        ? 'bg-amber-950 text-amber-400 border border-amber-800'
                        : 'bg-slate-900 text-slate-400 border border-slate-800'
                    }`}
                  >
                    {lastEvaluatedSignal.policy_action === 'APPROVE'
                      ? '✓ Approved: Cloud Dossier Synthesized'
                      : lastEvaluatedSignal.policy_action === 'REVIEW_QUEUE'
                      ? '⚠ Queued for Human Review'
                      : '⊘ Filtered Locally ($0.00 Cost)'}
                  </span>
                  <button
                    onClick={() => setLastEvaluatedSignal(null)}
                    className="text-slate-500 hover:text-white p-1"
                    title="Dismiss preview"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="text-sm font-semibold text-white">
                "{lastEvaluatedSignal.headline}"
              </div>

              {/* Gemini Synthesis Summary & Deep Research if available */}
              {lastEvaluatedSignal.event_summary && (
                <div className="p-4 rounded-xl bg-[#070e1c] border border-cyan-500/30 text-xs space-y-3.5">
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[#142138]">
                    <div className="font-bold text-cyan-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5 font-mono">
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Deep Research Breakdown • Google Gemini 3.5</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {lastEvaluatedSignal.market_impact_horizon && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-mono">
                          ⏱ {lastEvaluatedSignal.market_impact_horizon}
                        </span>
                      )}
                      {lastEvaluatedSignal.institutional_risk_level && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-mono">
                          ⚡ Risk: {lastEvaluatedSignal.institutional_risk_level}
                        </span>
                      )}
                    </div>
                  </div>

                  <p className="text-slate-200 leading-relaxed">{lastEvaluatedSignal.event_summary}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                    {/* Left: Facts & Mechanism */}
                    <div className="space-y-2.5">
                      {lastEvaluatedSignal.reported_facts && lastEvaluatedSignal.reported_facts.length > 0 && (
                        <div>
                          <div className="font-bold text-emerald-400 text-[11px] mb-1 flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" />
                            <span>Reported Facts</span>
                          </div>
                          <ul className="list-disc pl-4 text-slate-300 space-y-0.5">
                            {lastEvaluatedSignal.reported_facts.map((f, i) => (
                              <li key={i}>{f}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {lastEvaluatedSignal.transmission_mechanism && (
                        <div>
                          <div className="font-bold text-blue-400 text-[11px] mb-1 flex items-center gap-1">
                            <Zap className="w-3 h-3" />
                            <span>Transmission Mechanism</span>
                          </div>
                          <p className="text-slate-300 text-[11px] leading-relaxed bg-[#050b17] border border-[#142138] rounded p-2">
                            {lastEvaluatedSignal.transmission_mechanism}
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Right: Assets & Catalysts */}
                    <div className="space-y-2.5">
                      {lastEvaluatedSignal.affected_assets && lastEvaluatedSignal.affected_assets.length > 0 && (
                        <div>
                          <div className="font-bold text-cyan-400 text-[11px] mb-1 flex items-center gap-1">
                            <Activity className="w-3 h-3" />
                            <span>Affected Assets (Click for live ticker)</span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {lastEvaluatedSignal.affected_assets.map((a, i) => (
                              <button
                                key={i}
                                type="button"
                                onClick={() => onSelectStock?.(a)}
                                className="px-2 py-0.5 rounded bg-brand-teal/20 text-brand-teal hover:bg-brand-teal/30 hover:border-brand-teal/60 border border-brand-teal/30 font-mono text-[11px] font-bold transition-colors cursor-pointer flex items-center gap-1"
                                title={`Inspect ${a} live market quote & chart`}
                              >
                                <span>${a}</span>
                                <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {lastEvaluatedSignal.catalyst_watchpoints && lastEvaluatedSignal.catalyst_watchpoints.length > 0 && (
                        <div>
                          <div className="font-bold text-indigo-400 text-[11px] mb-1 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            <span>Catalyst Watchpoints</span>
                          </div>
                          <ul className="list-disc pl-4 text-slate-300 space-y-0.5">
                            {lastEvaluatedSignal.catalyst_watchpoints.map((c, i) => (
                              <li key={i}>{c}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 2. Ticker Summary Card with Segmented Progress Bar (SentimentIQ Style) */}
      <div className="bg-[#0a1120] border border-[#192640] rounded-2xl p-5 shadow-card">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 items-center">
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Scope / Ticker</div>
            <div className="text-xl font-extrabold text-white font-mono mt-0.5 truncate">
              {searchQuery.trim() ? searchQuery.toUpperCase().slice(0, 12) : 'MARKET STREAM'}
            </div>
          </div>
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Articles</div>
            <div className="text-xl font-extrabold text-white font-mono mt-0.5">{totalCount}</div>
          </div>
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Policy Bias</div>
            <div
              className={`text-xl font-extrabold font-mono mt-0.5 ${
                overallBias === 'Bullish'
                  ? 'text-emerald-400 glow-green-text'
                  : overallBias === 'Bearish'
                  ? 'text-rose-400 glow-red-text'
                  : 'text-indigo-400'
              }`}
            >
              {overallBias}
            </div>
          </div>
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Categorization</div>
            <div className="text-sm font-bold font-mono mt-1 space-x-2">
              <span className="text-emerald-400">{posCount} POS</span>
              <span className="text-slate-500">/</span>
              <span className="text-indigo-400">{neuCount} NEU</span>
              <span className="text-slate-500">/</span>
              <span className="text-rose-400">{negCount} NEG</span>
            </div>
          </div>
          <div className="col-span-2 md:col-span-1">
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              Signal Distribution ({posPct}% / {neuPct}% / {negPct}%)
            </div>
            {/* Segmented Multi-Color Progress Bar */}
            <div className="w-full h-2 rounded-full overflow-hidden flex bg-slate-800 mt-2">
              <div style={{ width: `${posPct}%` }} className="bg-emerald-400 transition-all duration-300" />
              <div style={{ width: `${neuPct}%` }} className="bg-slate-500 transition-all duration-300" />
              <div style={{ width: `${negPct}%` }} className="bg-rose-500 transition-all duration-300" />
            </div>
          </div>
        </div>
      </div>

      {/* 3. Interactive Filter Pills with Non-Financial Filter Switch */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mr-1 shrink-0">Filter:</span>
            {[
              { label: 'All Financial', count: financialCount },
              { label: 'Positive', count: posCount },
              { label: 'Neutral', count: neuCount },
              { label: 'Negative', count: negCount },
              { label: 'Review Queue', count: revCount },
              { label: 'Non-Financial Noise', count: noiCount },
            ].map((f) => {
              const isActive = categoryFilter === f.label;
              return (
                <button
                  key={f.label}
                  onClick={() => setCategoryFilter(f.label)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all duration-150 flex items-center gap-1.5 ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/50 shadow-sm shadow-blue-500/20'
                      : 'bg-[#0b1324] text-slate-400 border border-[#1a2944] hover:text-white hover:border-slate-500'
                  }`}
                >
                  <span>{f.label}</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                      isActive ? 'bg-blue-500/30 text-white' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {f.count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Non-Financial Noise Filter Toggle */}
          <button
            type="button"
            onClick={() => setFilterNonFinancial(!filterNonFinancial)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
              filterNonFinancial
                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40 shadow-sm shadow-emerald-500/10'
                : 'bg-[#0b1324] text-slate-400 border-[#1a2944] hover:text-slate-200'
            }`}
            title="Automatically avoids and filters out non-financial lifestyle and celebrity noise"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Filter Non-Financial: {filterNonFinancial ? 'ON' : 'OFF'}</span>
          </button>
        </div>

        {/* Filter Notice Banner if Non-Financial items are hidden */}
        {filterNonFinancial && noiCount > 0 && categoryFilter !== 'Non-Financial Noise' && (
          <div className="flex items-center justify-between text-[11px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-xl">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
              <span>
                <strong>Market Filter Active:</strong> {noiCount} non-financial noise items blocked locally by Strands Decider 2B ($0.00 cloud spend).
              </span>
            </span>
            <button
              onClick={() => setCategoryFilter('Non-Financial Noise')}
              className="underline hover:text-white ml-2 text-[10px] font-mono shrink-0"
            >
              View Blocked Noise
            </button>
          </div>
        )}
      </div>

      {/* 4. Main Two-Column Layout (News Feed vs Sentiment Overview & Donut) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Column (67% width) - Financial News Cards */}
        <div className="lg:col-span-2 space-y-4">
          {displaySignals.length === 0 ? (
            <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-12 text-center text-slate-400">
              <Radio className="w-10 h-10 mx-auto text-slate-600 mb-3" />
              <h3 className="text-base font-semibold text-slate-200">No signals match your filter</h3>
              <p className="text-xs text-slate-500 mt-1">
                Try switching the active filter pill or click &quot;Analyze News&quot; above to ingest fresh signals.
              </p>
            </div>
          ) : (
            displaySignals.map((signal) => {
              const tags = getArticleTags(signal.headline, signal.decider_sentiment);
              const isExpanded = expandedSignalId === signal.id;
              const hasGemini = signal.gemini_status === 'success' && signal.event_summary;

              return (
                <div
                  key={signal.id}
                  className="bg-[#0a1120] border border-[#16233b] hover:border-[#22365c] rounded-2xl p-5 shadow-card transition-all duration-200"
                >
                  {/* Top Metadata Line */}
                  <div className="flex flex-wrap items-center gap-2.5 text-xs text-slate-400 mb-3">
                    {/* Sentiment Badge */}
                    <span
                      className={`px-2.5 py-1 rounded-md text-[11px] font-bold tracking-wide uppercase border flex items-center gap-1.5 ${
                        signal.decider_sentiment === 'Bullish'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : signal.decider_sentiment === 'Bearish'
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                          : signal.decider_sentiment === 'Neutral'
                          ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                          : 'bg-slate-500/10 text-slate-400 border-slate-500/30'
                      }`}
                    >
                      {signal.decider_sentiment === 'Bullish' && <TrendingUp className="w-3 h-3" />}
                      {signal.decider_sentiment === 'Bearish' && <TrendingDown className="w-3 h-3" />}
                      {signal.decider_sentiment === 'Neutral' && <MinusCircle className="w-3 h-3" />}
                      {signal.decider_sentiment === 'Noise' && <AlertTriangle className="w-3 h-3" />}
                      <span>{signal.decider_sentiment}</span>
                    </span>

                    {/* Confidence Pill */}
                    <span className="bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono px-2 py-0.5 rounded-md text-[11px] font-semibold">
                      {Math.round(signal.decider_confidence * 100)}% confidence
                    </span>

                    {/* Latency Pill */}
                    <span className="bg-blue-500/10 text-blue-300 border border-blue-500/20 font-mono px-2 py-0.5 rounded-md text-[11px]">
                      ⚡ {Math.round(signal.decider_latency_ms)} ms (Decider 2B)
                    </span>

                    <span className="text-slate-600">•</span>
                    <span className="font-medium text-slate-300">{signal.publisher}</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-slate-500">{signal.timestamp.slice(0, 16).replace('T', ' ')}</span>

                    {signal.canonical_url && signal.canonical_url.startsWith('http') && (
                      <a
                        href={signal.canonical_url}
                        target="_blank"
                        rel="noreferrer"
                        className="ml-auto text-slate-400 hover:text-cyan-400 transition-colors"
                        title="Open Source Article"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>

                  {/* Headline */}
                  <h3 className="text-base font-bold text-white leading-snug hover:text-cyan-300 transition-colors cursor-pointer mb-3">
                    {signal.headline}
                  </h3>

                  {/* Dark Inset AI Summary Box (SentimentIQ Style) */}
                  <div className="bg-[#060e1d] border border-[#142138] rounded-xl p-4 mb-3.5">
                    <div className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      {hasGemini
                        ? 'AI Summary • Google Gemini 3.5 Intelligence'
                        : signal.policy_action === 'BLOCK_NOISE'
                        ? 'Decider 2B Policy Gatekeeper • Local Filter'
                        : signal.policy_action === 'BLOCK_NEUTRAL'
                        ? 'Decider 2B Policy Gatekeeper • Consensus Neutral'
                        : 'Policy Gatekeeper • Escalated to Review'}
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {hasGemini
                        ? signal.event_summary
                        : signal.policy_action === 'BLOCK_NOISE'
                        ? 'Classified locally as non-actionable noise or irrelevant promotional content. Dropped at edge (0 ms cloud latency, $0.00 spend).'
                        : signal.policy_action === 'BLOCK_NEUTRAL'
                        ? 'Classified as neutral financial information without material price dislocation catalyst. Persisted to audit ledger without consuming generative cloud tokens.'
                        : `Low confidence (${(signal.decider_confidence * 100).toFixed(
                            1
                          )}%) fell below safety threshold (0.80). Held in review queue for human verification.`}
                    </p>

                    {/* Show more toggle if analyzed by Gemini */}
                    {hasGemini && (
                      <button
                        onClick={() => setExpandedSignalId(isExpanded ? null : signal.id)}
                        className="mt-2 text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
                      >
                        {isExpanded ? (
                          <>
                            <span>Show less</span>
                            <ChevronUp className="w-3.5 h-3.5" />
                          </>
                        ) : (
                          <>
                            <span>View deep research breakdown</span>
                            <ChevronDown className="w-3.5 h-3.5" />
                          </>
                        )}
                      </button>
                    )}
                  </div>

                  {/* Expanded Institutional Dossier */}
                  {isExpanded && hasGemini && (
                    <div className="bg-[#050b17] border border-[#1a2944] rounded-xl p-4 md:p-5 mb-3.5 space-y-4 text-xs animate-in fade-in duration-200">
                      {/* Top Header Strip with Horizon, Risk Level, and Bias */}
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#142138]">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-bold text-slate-300 uppercase tracking-wider text-[10px] font-mono">
                            INSTITUTIONAL RESEARCH BREAKDOWN
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase ${
                              signal.decider_sentiment === 'Bullish'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                                : signal.decider_sentiment === 'Bearish'
                                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                                : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                            }`}
                          >
                            Directional Bias: {signal.decider_sentiment}
                          </span>
                          {signal.market_impact_horizon && (
                            <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px] font-mono flex items-center gap-1">
                              <Clock className="w-2.5 h-2.5" />
                              <span>Horizon: {signal.market_impact_horizon}</span>
                            </span>
                          )}
                          {signal.institutional_risk_level && (
                            <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[10px] font-mono flex items-center gap-1">
                              <AlertTriangle className="w-2.5 h-2.5" />
                              <span>Risk: {signal.institutional_risk_level}</span>
                            </span>
                          )}
                        </div>

                        <div className="text-[10px] text-slate-500 font-mono">
                          ID: #{signal.id} • Audit Ledger Verified
                        </div>
                      </div>

                      {/* 2-Column Institutional Breakdown */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        {/* Left Column: Facts, Transmission, Hypotheses */}
                        <div className="space-y-3.5">
                          {/* 1. Reported Facts */}
                          <div>
                            <div className="font-bold text-emerald-400 mb-1.5 flex items-center gap-1.5">
                              <CheckCircle className="w-3.5 h-3.5" />
                              <span>1. Reported Facts (Source Verifiable)</span>
                            </div>
                            {signal.reported_facts?.length > 0 ? (
                              <ul className="list-disc pl-4 text-slate-300 space-y-1">
                                {signal.reported_facts.map((fact, i) => (
                                  <li key={i}>{fact}</li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-slate-300">{signal.event_summary}</p>
                            )}
                          </div>

                          {/* 2. Transmission Mechanism */}
                          <div>
                            <div className="font-bold text-blue-400 mb-1.5 flex items-center gap-1.5">
                              <Zap className="w-3.5 h-3.5" />
                              <span>2. Economic Transmission Mechanism</span>
                            </div>
                            <p className="text-slate-300 leading-relaxed bg-[#081020] border border-[#142138] rounded-lg p-2.5">
                              {signal.transmission_mechanism || 'Direct cash flow and multiple valuation repricing across capital markets.'}
                            </p>
                          </div>

                          {/* 3. Analytical Hypotheses */}
                          {signal.analytical_hypotheses && signal.analytical_hypotheses.length > 0 && (
                            <div>
                              <div className="font-bold text-purple-400 mb-1.5 flex items-center gap-1.5">
                                <Cpu className="w-3.5 h-3.5" />
                                <span>3. Forward-Looking Analytical Hypotheses</span>
                              </div>
                              <ul className="list-disc pl-4 text-slate-300 space-y-1">
                                {signal.analytical_hypotheses.map((hyp, i) => (
                                  <li key={i}>{hyp}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>

                        {/* Right Column: Assets (Clickable!), Catalyst Watchpoints, Peers, Risks */}
                        <div className="space-y-3.5">
                          {/* 4. Affected Asset Classes & Key Tickers */}
                          <div>
                            <div className="font-bold text-cyan-400 mb-1.5 flex items-center justify-between">
                              <span className="flex items-center gap-1.5">
                                <Activity className="w-3.5 h-3.5" />
                                <span>4. Affected Asset Classes & Tickers</span>
                              </span>
                              <span className="text-[10px] text-slate-500 font-normal font-mono">
                                (Click stock for live quote)
                              </span>
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                              {signal.affected_assets?.length > 0 ? (
                                signal.affected_assets.map((asset, i) => (
                                  <button
                                    key={i}
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onSelectStock?.(asset);
                                    }}
                                    className="font-mono bg-blue-500/10 text-blue-300 hover:bg-cyan-500/20 hover:text-cyan-200 border border-blue-500/30 hover:border-cyan-400 px-2 py-1 rounded-md text-xs font-semibold cursor-pointer transition-all flex items-center gap-1 shadow-sm group"
                                    title={`Click to open live ${asset} market chart & news`}
                                  >
                                    <span>{asset}</span>
                                    <ExternalLink className="w-3 h-3 opacity-60 group-hover:opacity-100" />
                                  </button>
                                ))
                              ) : (
                                <span className="text-slate-500">Broader equities index</span>
                              )}
                            </div>
                          </div>

                          {/* 5. Catalyst Watchpoints */}
                          {signal.catalyst_watchpoints && signal.catalyst_watchpoints.length > 0 && (
                            <div>
                              <div className="font-bold text-indigo-400 mb-1.5 flex items-center gap-1.5">
                                <Clock className="w-3.5 h-3.5" />
                                <span>5. Upcoming Catalyst Watchpoints</span>
                              </div>
                              <ul className="list-disc pl-4 text-slate-300 space-y-1">
                                {signal.catalyst_watchpoints.map((cat, i) => (
                                  <li key={i}>{cat}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* 6. Peer & Supply Chain Sensitivity */}
                          {signal.peer_impact && signal.peer_impact.length > 0 && (
                            <div>
                              <div className="font-bold text-teal-400 mb-1.5 flex items-center gap-1.5">
                                <TrendingUp className="w-3.5 h-3.5" />
                                <span>6. Peer & Sector Sensitivity</span>
                              </div>
                              <div className="flex flex-wrap gap-1">
                                {signal.peer_impact.map((peer, i) => (
                                  <button
                                    key={i}
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onSelectStock?.(peer);
                                    }}
                                    className="font-mono bg-[#0c1830] text-teal-300 hover:bg-teal-500/20 border border-teal-500/30 px-2 py-0.5 rounded text-[11px] cursor-pointer transition-colors"
                                  >
                                    {peer}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* 7. Uncertainties & Downside Risks */}
                          <div>
                            <div className="font-bold text-amber-400 mb-1.5 flex items-center gap-1.5">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              <span>7. Invalidation Risks & Scenarios</span>
                            </div>
                            {signal.uncertainties?.length > 0 ? (
                              <ul className="list-disc pl-4 text-slate-300 space-y-1">
                                {signal.uncertainties.map((u, i) => (
                                  <li key={i}>⚠️ {u}</li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-slate-500">Macro uncertainty.</p>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Audit Provenance Footer Strip */}
                      <div className="pt-3 border-t border-[#16233b] flex flex-wrap items-center justify-between text-[11px] text-slate-500 font-mono gap-2">
                        <span>Model: {signal.gemini_model_id}</span>
                        <span>Tokens: In={signal.input_tokens || 0} Out={signal.output_tokens || 0}</span>
                        <span>Cloud Latency: {Math.round(signal.cloud_latency_ms)} ms</span>
                        <span>Spend: ${signal.estimated_cost_usd.toFixed(6)}</span>
                      </div>
                    </div>
                  )}

                  {/* Hashtag Group Pills */}
                  <div className="flex flex-wrap items-center gap-1.5">
                    {tags.map((tag, i) => (
                      <span
                        key={i}
                        className="text-[11px] font-mono bg-[#0d162a] text-blue-400 border border-[#1b2b4b] px-2.5 py-0.5 rounded-md"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Column (33% width) - Sentiment Overview & Donut Chart (SentimentIQ + AlphaPro Style) */}
        <div className="space-y-5 lg:sticky lg:top-6">
          {/* Sentiment Overview Card */}
          <div className="bg-[#0a1120] border border-[#192640] rounded-2xl p-5 shadow-card">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Sentiment Overview</div>
            <div className="text-lg font-extrabold text-white font-mono mb-2">
              {searchQuery.trim() ? searchQuery.toUpperCase() : 'MARKET OVERVIEW'}
            </div>

            {/* Donut Chart with Center Percentage */}
            <div className="relative h-48 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={donutData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {donutData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-2xl font-black text-emerald-400 font-mono glow-green-text">{posPct}%</span>
                <span className="text-[11px] text-slate-400 uppercase font-semibold">Bullish</span>
              </div>
            </div>

            {/* Legend with Progress Bars */}
            <div className="space-y-3 mt-2 text-xs">
              <div>
                <div className="flex justify-between font-semibold mb-1">
                  <span className="text-emerald-400">■ Positive (Bullish)</span>
                  <span className="text-slate-300 font-mono">
                    {posPct}% <span className="text-slate-500">({posCount})</span>
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div style={{ width: `${posPct}%` }} className="h-full bg-emerald-400 rounded-full" />
                </div>
              </div>

              <div>
                <div className="flex justify-between font-semibold mb-1">
                  <span className="text-slate-400">■ Neutral (Consensus)</span>
                  <span className="text-slate-300 font-mono">
                    {neuPct}% <span className="text-slate-500">({neuCount})</span>
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div style={{ width: `${neuPct}%` }} className="h-full bg-slate-500 rounded-full" />
                </div>
              </div>

              <div>
                <div className="flex justify-between font-semibold mb-1">
                  <span className="text-rose-400">■ Negative (Bearish)</span>
                  <span className="text-slate-300 font-mono">
                    {negPct}% <span className="text-slate-500">({negCount})</span>
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div style={{ width: `${negPct}%` }} className="h-full bg-rose-500 rounded-full" />
                </div>
              </div>
            </div>

            <p className="text-[11px] text-slate-500 mt-4 leading-relaxed border-t border-[#16233b] pt-3">
              Based on {totalCount} signals classified by Strands Decider 2B. High-conviction signals (≥ 0.80) are
              analyzed by Google Gemini.
            </p>
          </div>

          {/* Tracked Market Assets Watchlist (AlphaPro Style - Image 3) */}
          <div className="bg-[#0a1120] border border-[#192640] rounded-2xl p-5 shadow-card">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Tracked Assets</div>
            <div className="text-sm font-bold text-white mb-3">Institutional Watchlist</div>

            <div className="space-y-2">
              {[
                { ticker: 'NVDA', name: 'NVIDIA Corporation', score: '+4.20%', bias: 'Bullish 94%', positive: true },
                { ticker: 'AAPL', name: 'Apple Inc.', score: '+1.20%', bias: 'Bullish 78%', positive: true },
                { ticker: 'TSLA', name: 'Tesla Inc.', score: '-2.15%', bias: 'Bearish 38%', positive: false },
                { ticker: 'MSFT', name: 'Microsoft Corporation', score: '+0.85%', bias: 'Neutral 65%', positive: true },
              ].map((item) => (
                <div
                  key={item.ticker}
                  onClick={() => {
                    setSearchQuery(item.ticker);
                    onSelectStock?.(item.ticker);
                  }}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-[#060c18] hover:bg-[#0c1830] border border-[#142138] hover:border-cyan-500/50 cursor-pointer transition-all group shadow-sm"
                  title={`Click to open live ${item.ticker} quote, chart & filtered signals`}
                >
                  <div>
                    <div className="font-bold text-sm text-white group-hover:text-cyan-300 font-mono flex items-center gap-1.5 transition-colors">
                      <span>{item.ticker}</span>
                      <ExternalLink className="w-3 h-3 opacity-40 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="text-[11px] text-slate-500">{item.name}</div>
                  </div>
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                      item.positive
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {item.score} • {item.bias}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
