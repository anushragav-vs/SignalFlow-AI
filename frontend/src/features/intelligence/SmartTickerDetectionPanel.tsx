import React, { useState, useMemo } from 'react';
import type { Signal, InstrumentSummary } from '../../types';
import {
  Layers,
  Search,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  TrendingDown,
  MinusCircle,
  Building2,
  DollarSign,
  Activity,
  SlidersHorizontal,
  ArrowRight,
  Radio,
  Clock,
  X,
  RotateCcw,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

interface SmartTickerDetectionPanelProps {
  signals: Signal[];
  instrumentsSummary: InstrumentSummary[];
  onSelectInstrument?: (symbol: string) => void;
  onOpenSignalDetail?: (signal: Signal) => void;
}

export const SmartTickerDetectionPanel: React.FC<SmartTickerDetectionPanelProps> = ({
  signals,
  instrumentsSummary,
  onSelectInstrument,
  onOpenSignalDetail,
}) => {
  // Filter states
  const [selectedPair, setSelectedPair] = useState<string>('ALL');
  const [selectedRel, setSelectedRel] = useState<string>('ALL');
  const [selectedSentiment, setSelectedSentiment] = useState<string>('ALL');
  const [selectedImpact, setSelectedImpact] = useState<string>('ALL');
  const [minConfidence, setMinConfidence] = useState<number>(0.70);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortBy, setSortBy] = useState<'latest' | 'impact' | 'confidence'>('latest');

  // Check if any filter is active
  const isFilterActive =
    selectedPair !== 'ALL' ||
    selectedRel !== 'ALL' ||
    selectedSentiment !== 'ALL' ||
    selectedImpact !== 'ALL' ||
    minConfidence > 0.70 ||
    searchQuery.trim().length > 0;

  const handleResetFilters = () => {
    setSelectedPair('ALL');
    setSelectedRel('ALL');
    setSelectedSentiment('ALL');
    setSelectedImpact('ALL');
    setMinConfidence(0.70);
    setSearchQuery('');
    setSortBy('latest');
  };

  // Filter & deduplicate signals
  const filteredSignals = useMemo(() => {
    // Deduplicate by headline or id
    const seenHeadlines = new Set<string>();
    const uniqueSignals: Signal[] = [];

    for (const s of signals) {
      const normHeadline = s.headline.trim().toLowerCase();
      if (!seenHeadlines.has(normHeadline)) {
        seenHeadlines.add(normHeadline);
        uniqueSignals.push(s);
      }
    }

    return uniqueSignals
      .filter((s) => {
        const aff = s.affected_instruments || [];

        // Pair filter
        if (selectedPair !== 'ALL') {
          if (!aff.some((i) => i.symbol === selectedPair)) return false;
        }

        // Relationship filter
        if (selectedRel !== 'ALL') {
          if (!aff.some((i) => i.relationship.toLowerCase() === selectedRel.toLowerCase())) {
            return false;
          }
        }

        // Sentiment filter
        if (selectedSentiment !== 'ALL') {
          if (s.decider_sentiment.toUpperCase() !== selectedSentiment.toUpperCase()) {
            return false;
          }
        }

        // Impact level filter
        if (selectedImpact !== 'ALL') {
          if ((s.impact_level || 'LOW').toUpperCase() !== selectedImpact.toUpperCase()) {
            return false;
          }
        }

        // Minimum confidence filter
        if (minConfidence > 0) {
          const maxConf = Math.max(
            s.decider_confidence || 0,
            ...aff.map((i) => i.confidence || 0)
          );
          if (maxConf < minConfidence) return false;
        }

        // Search query filter (headline, detected entities, symbols)
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const hasInHeadline = s.headline.toLowerCase().includes(q);
          const hasInEntities = (s.detected_entities || []).some((e) =>
            e.name.toLowerCase().includes(q)
          );
          const hasInPair = aff.some((i) => i.symbol.toLowerCase().includes(q));
          const hasInSource = (s.publisher || '').toLowerCase().includes(q);
          if (!hasInHeadline && !hasInEntities && !hasInPair && !hasInSource) return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'impact') {
          return (b.impact_score || 0) - (a.impact_score || 0);
        }
        if (sortBy === 'confidence') {
          return (b.decider_confidence || 0) - (a.decider_confidence || 0);
        }
        // latest
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      });
  }, [
    signals,
    selectedPair,
    selectedRel,
    selectedSentiment,
    selectedImpact,
    minConfidence,
    searchQuery,
    sortBy,
  ]);

  return (
    <div className="space-y-6">
      {/* 1. Forex Universe Cards Overview Grid (Task 3.B) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-mono px-1">
          <span className="font-bold text-slate-200 uppercase flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            Institutional Forex Pair Universe ({instrumentsSummary.length} Pairs)
          </span>
          <span className="text-slate-400 text-[11px]">
            Click any pair to open detailed instrument profile
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {instrumentsSummary.map((inst) => {
            const isPairSelected = selectedPair === inst.symbol;

            const sentimentColor =
              inst.dominant_sentiment === 'Bullish'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : inst.dominant_sentiment === 'Bearish'
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';

            return (
              <div
                key={inst.symbol}
                onClick={() => onSelectInstrument?.(inst.symbol)}
                className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all duration-200 flex flex-col justify-between group shadow-sm ${
                  isPairSelected
                    ? 'bg-cyan-500/15 border-cyan-400 shadow-cyan-500/10 scale-[1.02]'
                    : 'bg-[#091122] border-[#16243e] hover:border-cyan-500/50 hover:bg-[#0d1830]'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-sm font-mono text-white tracking-tight group-hover:text-cyan-300 transition-colors">
                      {inst.symbol}
                    </span>
                    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold border ${sentimentColor}`}>
                      {inst.dominant_sentiment}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400 truncate mt-0.5">
                    {inst.name}
                  </div>
                </div>

                <div className="mt-3 pt-2 border-t border-[#142138] space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="text-slate-400">Events:</span>
                    <span className="font-bold text-white">{inst.total_mentions}</span>
                  </div>

                  <div className="flex items-center justify-between gap-1 text-[9px] font-mono font-bold">
                    <span className="px-1 py-0.2 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20" title="Direct Mentions">
                      {inst.direct_count} DIR
                    </span>
                    <span className="px-1 py-0.2 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20" title="Indirect Transmission">
                      {inst.indirect_count} IND
                    </span>
                    <span className="px-1 py-0.2 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20" title="Potential Spillover">
                      {inst.potential_count} POT
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. Compact Smart Filters Toolbar (Task 3.C) */}
      <div className="bg-[#091122] border border-[#16243e] rounded-2xl p-4 shadow-lg space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#142138] pb-3">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
              Smart Filters & Macro Screener
            </span>
            <span className="text-xs font-mono text-cyan-400">
              ({filteredSignals.length} events matching)
            </span>
          </div>

          {/* Right Action: Clear Filters & Sort */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-[#0f1b34] border border-[#1e3258] text-white text-xs rounded-xl px-2.5 py-1.5 focus:outline-none focus:border-cyan-400 font-mono"
            >
              <option value="latest">Latest Ingested</option>
              <option value="impact">Highest Impact Score</option>
              <option value="confidence">Highest Confidence</option>
            </select>

            {isFilterActive && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#13203c] hover:bg-[#1a2d54] text-xs font-mono text-cyan-300 hover:text-white border border-[#233b68] transition-all"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Clear Filters</span>
              </button>
            )}
          </div>
        </div>

        {/* Filter Controls Row */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5 text-xs">
          {/* Pair Select */}
          <div className="space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Forex Pair</span>
            <select
              value={selectedPair}
              onChange={(e) => setSelectedPair(e.target.value)}
              className="w-full bg-[#0f1b34] border border-[#1e3258] text-white text-xs rounded-xl px-2.5 py-2 focus:outline-none focus:border-cyan-400 font-mono"
            >
              <option value="ALL">All Pairs ({instrumentsSummary.length})</option>
              {instrumentsSummary.map((inst) => (
                <option key={inst.symbol} value={inst.symbol}>
                  {inst.symbol} ({inst.total_mentions})
                </option>
              ))}
            </select>
          </div>

          {/* Relationship Type */}
          <div className="space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Relationship</span>
            <select
              value={selectedRel}
              onChange={(e) => setSelectedRel(e.target.value)}
              className="w-full bg-[#0f1b34] border border-[#1e3258] text-white text-xs rounded-xl px-2.5 py-2 focus:outline-none focus:border-cyan-400 font-mono"
            >
              <option value="ALL">All Relationships</option>
              <option value="direct">Direct Mention</option>
              <option value="indirect">Indirect Transmission</option>
              <option value="potential">Potential Spillover</option>
            </select>
          </div>

          {/* Sentiment */}
          <div className="space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Sentiment</span>
            <select
              value={selectedSentiment}
              onChange={(e) => setSelectedSentiment(e.target.value)}
              className="w-full bg-[#0f1b34] border border-[#1e3258] text-white text-xs rounded-xl px-2.5 py-2 focus:outline-none focus:border-cyan-400 font-mono"
            >
              <option value="ALL">All Sentiments</option>
              <option value="Bullish">Bullish</option>
              <option value="Bearish">Bearish</option>
              <option value="Neutral">Neutral</option>
              <option value="Noise">Noise</option>
            </select>
          </div>

          {/* Impact Level */}
          <div className="space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Impact Level</span>
            <select
              value={selectedImpact}
              onChange={(e) => setSelectedImpact(e.target.value)}
              className="w-full bg-[#0f1b34] border border-[#1e3258] text-white text-xs rounded-xl px-2.5 py-2 focus:outline-none focus:border-cyan-400 font-mono"
            >
              <option value="ALL">All Impact Levels</option>
              <option value="CRITICAL">Critical (75–100)</option>
              <option value="HIGH">High (50–74)</option>
              <option value="MEDIUM">Medium (25–49)</option>
              <option value="LOW">Low (0–24)</option>
            </select>
          </div>

          {/* Min Confidence Slider */}
          <div className="space-y-1">
            <div className="flex justify-between text-[10px] font-mono text-slate-400 uppercase">
              <span>Min Conf:</span>
              <span className="text-cyan-400 font-bold">{(minConfidence * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.50"
              max="0.95"
              step="0.05"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer h-7"
            />
          </div>

          {/* Search Box */}
          <div className="space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Keyword / Entity</span>
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Powell, NFP, EUR..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#0f1b34] border border-[#1e3258] rounded-xl pl-8 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono"
              />
            </div>
          </div>
        </div>
      </div>

      {/* 3. Detected News & Transmission Signals Feed (Task 3.D) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-mono px-1">
          <span className="font-bold text-slate-200 uppercase flex items-center gap-2">
            <Radio className="w-4 h-4 text-cyan-400" />
            Detected News & Transmission Signals ({filteredSignals.length})
          </span>
          <span className="text-slate-400 text-[11px]">Click any card to open complete dossier</span>
        </div>

        {filteredSignals.length === 0 ? (
          <div className="p-12 bg-[#091122] border border-[#16243e] rounded-2xl text-center space-y-3">
            <HelpCircle className="w-10 h-10 text-slate-500 mx-auto" />
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-white">No Signals Match Selected Filters</h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                Try widening your confidence slider, switching currency pairs, or clicking &quot;Clear Filters&quot; to restore all events.
              </p>
            </div>
            {isFilterActive && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="px-4 py-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-xs font-mono font-bold text-cyan-300 transition-all inline-flex items-center gap-2"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset All Filters</span>
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredSignals.map((signal) => {
              const impactLvl = signal.impact_level || 'LOW';
              const impactBadgeColor =
                impactLvl === 'CRITICAL'
                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                  : impactLvl === 'HIGH'
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : impactLvl === 'MEDIUM'
                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                  : 'bg-slate-500/20 text-slate-400 border-slate-500/40';

              const sentimentBadgeColor =
                signal.decider_sentiment === 'Bullish'
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                  : signal.decider_sentiment === 'Bearish'
                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                  : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';

              return (
                <div
                  key={signal.id}
                  onClick={() => onOpenSignalDetail?.(signal)}
                  className="bg-[#091122] border border-[#16243e] hover:border-cyan-500/50 rounded-2xl p-4.5 space-y-3 cursor-pointer transition-all duration-150 hover:bg-[#0c162e] shadow-md group"
                >
                  {/* Top Metadata Row */}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${sentimentBadgeColor}`}>
                        {signal.decider_sentiment}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${impactBadgeColor}`}>
                        {impactLvl} Impact ({signal.impact_score || 0}/100)
                      </span>
                      <span className="text-[11px] font-mono text-cyan-400">
                        {((signal.decider_confidence || 0) * 100).toFixed(0)}% conf
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
                      <span className="text-slate-300 font-semibold">{signal.publisher}</span>
                      <span>•</span>
                      <span>{new Date(signal.timestamp).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Headline */}
                  <h3 className="text-sm md:text-base font-bold text-white leading-snug group-hover:text-cyan-300 transition-colors">
                    {signal.headline}
                  </h3>

                  {/* Transmission Pairs & Entities Chips */}
                  <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[#132038]">
                    <span className="text-[10px] font-mono text-slate-500 uppercase">Affected Pairs:</span>
                    {signal.affected_instruments && signal.affected_instruments.length > 0 ? (
                      signal.affected_instruments.map((inst, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono bg-[#0f1b34] border border-[#1e3258] text-white"
                        >
                          <span className="font-extrabold text-cyan-300">{inst.symbol}</span>
                          <span className={`text-[9px] uppercase font-bold px-1 rounded ${
                            inst.relationship === 'direct'
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : inst.relationship === 'indirect'
                              ? 'bg-blue-500/20 text-blue-300'
                              : 'bg-purple-500/20 text-purple-300'
                          }`}>
                            {inst.relationship}
                          </span>
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-slate-500 italic">Macro spillover</span>
                    )}

                    <div className="ml-auto flex items-center gap-1 text-xs font-mono text-cyan-400 group-hover:text-cyan-300 transition-colors">
                      <span>View Dossier</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
