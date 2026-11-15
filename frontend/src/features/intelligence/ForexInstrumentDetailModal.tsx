import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../../lib/api-client';
import type { ForexInstrumentDetail, Signal } from '../../types';
import {
  X,
  TrendingUp,
  TrendingDown,
  MinusCircle,
  Activity,
  Layers,
  Sparkles,
  ExternalLink,
  Loader2,
  Calendar,
  AlertTriangle,
  Building2,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Bookmark,
  BookmarkCheck,
  Clock,
  Radio,
  Flame,
  Scale,
  RefreshCw,
  Info,
  DollarSign,
  ArrowUpDown,
  Filter,
} from 'lucide-react';

interface ForexInstrumentDetailModalProps {
  symbol: string | null;
  onClose: () => void;
  onFilterToPair?: (symbol: string) => void;
  onSelectSignal?: (signal: Signal) => void;
}

export const ForexInstrumentDetailModal: React.FC<ForexInstrumentDetailModalProps> = ({
  symbol,
  onClose,
  onFilterToPair,
  onSelectSignal,
}) => {
  const [data, setData] = useState<ForexInstrumentDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isWatchlisted, setIsWatchlisted] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<'latest' | 'impact' | 'confidence'>('latest');

  // Check watchlist in localStorage
  useEffect(() => {
    if (!symbol) return;
    try {
      const stored = localStorage.getItem('signalflow_forex_watchlist');
      const list: string[] = stored ? JSON.parse(stored) : [];
      setIsWatchlisted(list.includes(symbol));
    } catch {
      setIsWatchlisted(false);
    }
  }, [symbol]);

  const toggleWatchlist = () => {
    if (!symbol) return;
    try {
      const stored = localStorage.getItem('signalflow_forex_watchlist');
      const list: string[] = stored ? JSON.parse(stored) : [];
      const updated = list.includes(symbol)
        ? list.filter((s) => s !== symbol)
        : [...list, symbol];
      localStorage.setItem('signalflow_forex_watchlist', JSON.stringify(updated));
      setIsWatchlisted(!isWatchlisted);
    } catch (err) {
      console.error('Failed to update watchlist:', err);
    }
  };

  // Lock background scroll and listen for Escape key
  useEffect(() => {
    if (!symbol) return;
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
  }, [symbol, onClose]);

  // Load Instrument Data - Immediately reset state to prevent stale data display
  const loadData = () => {
    if (!symbol) return;
    setData(null);
    setLoading(true);
    setError(null);

    api
      .getIntelligenceInstrumentDetail(symbol)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load instrument detail:', err);
        setError(
          err.message?.includes('404') || err.message?.includes('Not Found')
            ? `No intelligence profile found for symbol "${symbol}". Please select a supported forex pair.`
            : err.message || 'Failed to load instrument data'
        );
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, [symbol]);

  // Secondary deduplication and sorting of unique signals
  const sortedUniqueSignals = useMemo(() => {
    if (!data?.signals) return [];
    const seen = new Set<number>();
    const unique = data.signals.filter((s) => {
      if (!s.id || seen.has(s.id)) return false;
      seen.add(s.id);
      return true;
    });

    return [...unique].sort((a, b) => {
      if (sortBy === 'impact') {
        return (b.impact_score || 0) - (a.impact_score || 0);
      }
      if (sortBy === 'confidence') {
        return (b.decider_confidence || 0) - (a.decider_confidence || 0);
      }
      // 'latest' default
      const timeA = new Date(a.timestamp || 0).getTime();
      const timeB = new Date(b.timestamp || 0).getTime();
      return timeB - timeA || b.id - a.id;
    });
  }, [data?.signals, sortBy]);

  if (!symbol) return null;

  // Mini sparkline SVG renderer
  const renderSparkline = (prices?: number[], isPos: boolean = true) => {
    if (!prices || prices.length < 2) return null;
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min || 1;
    const width = 200;
    const height = 45;
    const pad = 4;

    const points = prices.map((p, i) => {
      const x = pad + (i / (prices.length - 1)) * (width - pad * 2);
      const y = height - pad - ((p - min) / range) * (height - pad * 2);
      return `${x},${y}`;
    });

    const strokeColor = isPos ? '#10b981' : '#f43f5e';

    return (
      <svg width={width} height={height} className="overflow-visible">
        <polyline
          fill="none"
          stroke={strokeColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points.join(' ')}
        />
      </svg>
    );
  };

  const quote = data?.market_quote;
  const isQuotePositive = quote?.is_positive ?? true;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 md:p-6 animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-[#080e1c] border border-[#1b2b48] w-full max-w-4xl max-h-[92vh] rounded-2xl flex flex-col shadow-2xl overflow-hidden text-slate-100">
        {/* Header Bar */}
        <div className="px-6 py-4 border-b border-[#16233b] flex items-center justify-between bg-[#0b1325] sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="font-extrabold text-xl md:text-2xl text-white font-mono tracking-tight">
                  {data?.symbol || symbol}
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase tracking-wider bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                  {data?.category || 'FOREX PAIR'}
                </span>
                <span className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-400 ml-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  {quote?.price ? 'Live Market Rate' : 'Calibrated Rate'}
                </span>
              </div>
              <div className="text-xs text-slate-400 font-medium mt-0.5">
                {data?.name || 'Forex Pair Intelligence & Transmission Profile'}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleWatchlist}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all border ${
                isWatchlisted
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-[#0f1b34] text-slate-300 hover:text-white border-[#1e3258]'
              }`}
              title="Add or remove from watchlist"
            >
              {isWatchlisted ? (
                <>
                  <BookmarkCheck className="w-3.5 h-3.5 text-amber-400" />
                  <span>Watchlisted</span>
                </>
              ) : (
                <>
                  <Bookmark className="w-3.5 h-3.5 text-slate-400" />
                  <span>Watchlist</span>
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
          {loading ? (
            <div className="py-24 flex flex-col items-center justify-center gap-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
              <span className="text-sm font-semibold text-white">
                Querying {symbol} Intelligence Profile...
              </span>
              <span className="text-xs text-slate-500">
                Aggregating direct mentions, transmission channels & impact scores
              </span>
            </div>
          ) : error ? (
            <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-rose-200">
                <AlertTriangle className="w-5 h-5 text-rose-400" />
                <span>Instrument Intelligence Error</span>
              </div>
              <p className="text-xs text-rose-300 leading-relaxed">{error}</p>
              <button
                onClick={loadData}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-xs font-mono font-bold text-white transition-all"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Query</span>
              </button>
            </div>
          ) : data ? (
            <>
              {/* 1. Hero Quote & Market Status Card */}
              <div className="bg-gradient-to-r from-[#0c162e] via-[#0a1326] to-[#0d1830] border border-[#1b2f56] rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
                <div className="space-y-1">
                  <div className="text-[11px] font-mono uppercase text-slate-400 tracking-wider flex items-center gap-2">
                    <span>Reference Spot Rate</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-cyan-400">{data.base_currency}/{data.quote_currency}</span>
                  </div>
                  <div className="flex items-baseline gap-3">
                    <span className="text-3xl md:text-4xl font-extrabold text-white font-mono tracking-tight">
                      {quote?.price
                        ? Number(quote.price).toFixed(data.base_currency === 'JPY' || data.quote_currency === 'JPY' ? 2 : 4)
                        : '1.0850'}
                    </span>
                    {quote?.change_pct !== undefined && (
                      <span
                        className={`flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-mono font-bold ${
                          isQuotePositive
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        }`}
                      >
                        {isQuotePositive ? (
                          <TrendingUp className="w-3.5 h-3.5" />
                        ) : (
                          <TrendingDown className="w-3.5 h-3.5" />
                        )}
                        <span>{isQuotePositive ? '+' : ''}{quote.change_pct}%</span>
                        <span className="text-[10px] text-slate-400">
                          ({isQuotePositive ? '+' : ''}{quote.change_abs ?? '0.00'})
                        </span>
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono">
                    Updated: {new Date().toLocaleTimeString()} • Source: Live Exchange Stream & Baseline Ledger
                  </div>
                </div>

                {/* Sparkline & Quick Actions */}
                <div className="flex flex-col sm:flex-row items-center gap-4">
                  {quote?.sparkline && renderSparkline(quote.sparkline, isQuotePositive)}

                  {onFilterToPair && (
                    <button
                      onClick={() => {
                        onFilterToPair(data.symbol);
                        onClose();
                      }}
                      className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-xs font-mono font-bold transition-all shadow-sm"
                    >
                      <span>Filter Feed to {data.symbol}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              {/* 2. Key Intelligence Metrics Bar */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="bg-[#0a1224] border border-[#16243e] rounded-xl p-3.5 space-y-1">
                  <span className="text-[11px] font-mono uppercase text-slate-400 block">Total Detected News</span>
                  <div className="text-xl font-extrabold text-white font-mono">
                    {data.total_correlated_signals}
                    <span className="text-xs text-slate-500 font-normal ml-1">events</span>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    {data.direct_count} direct • {data.indirect_count} indirect
                  </div>
                </div>

                <div className="bg-[#0a1224] border border-[#16243e] rounded-xl p-3.5 space-y-1">
                  <span className="text-[11px] font-mono uppercase text-slate-400 block">Average Impact</span>
                  <div className="text-xl font-extrabold text-cyan-400 font-mono">
                    {data.average_impact_score}
                    <span className="text-xs text-slate-500 font-normal ml-1">/100</span>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    {data.critical_events_count} critical • {data.high_events_count} high
                  </div>
                </div>

                <div className="bg-[#0a1224] border border-[#16243e] rounded-xl p-3.5 space-y-1">
                  <span className="text-[11px] font-mono uppercase text-slate-400 block">Dominant Sentiment</span>
                  <div
                    className={`text-xl font-extrabold font-mono ${
                      data.dominant_sentiment === 'Bullish'
                        ? 'text-emerald-400'
                        : data.dominant_sentiment === 'Bearish'
                        ? 'text-rose-400'
                        : 'text-indigo-400'
                    }`}
                  >
                    {data.dominant_sentiment}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    Index: {data.sentiment_score}/100
                  </div>
                </div>

                <div className="bg-[#0a1224] border border-[#16243e] rounded-xl p-3.5 space-y-1">
                  <span className="text-[11px] font-mono uppercase text-slate-400 block">Transmission Types</span>
                  <div className="flex items-center gap-1.5 pt-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                      {data.direct_count} DIR
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/15 text-blue-300 border border-blue-500/30">
                      {data.indirect_count} IND
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/15 text-purple-300 border border-purple-500/30">
                      {data.potential_count} POT
                    </span>
                  </div>
                </div>
              </div>

              {/* 3. Related Macro Entities & Policy Drivers */}
              <div className="bg-[#0a1224] border border-[#16243e] rounded-xl p-4.5 space-y-3">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-cyan-400" />
                  Associated Macro Entities & Monetary Authorities
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="space-y-1.5">
                    <span className="text-slate-400 font-mono text-[11px]">Primary Central Banks:</span>
                    <div className="flex flex-wrap gap-2">
                      {data.related_central_banks.map((cb, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg text-xs font-mono bg-[#101b33] border border-[#1d3159] text-white flex items-center gap-1.5"
                        >
                          <Building2 className="w-3 h-3 text-cyan-400" />
                          {cb}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <span className="text-slate-400 font-mono text-[11px]">Monitored Macro Drivers:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {data.macro_indicators.map((ind, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded text-[11px] font-mono bg-[#0e172e] border border-[#182a4c] text-slate-300"
                        >
                          {ind}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {data.aliases && data.aliases.length > 0 && (
                  <div className="pt-2 border-t border-[#142138] flex items-center gap-2 text-xs">
                    <span className="text-slate-500 font-mono text-[11px]">Tracked Aliases:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {data.aliases.map((al, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#111c34] text-slate-300 border border-[#1d3158]"
                        >
                          {al}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* 4. Highest Impact Event Card */}
              {data.highest_impact_news && (
                <div className="bg-[#0f172a] border border-amber-500/30 rounded-xl p-4 space-y-2 shadow-md">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-amber-400 font-mono font-bold flex items-center gap-1.5 uppercase">
                      <Flame className="w-4 h-4 text-amber-400" />
                      Highest Impact Recorded Event
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                      Score: {data.highest_impact_news.impact_score}/100 ({data.highest_impact_news.impact_level})
                    </span>
                  </div>
                  <h4
                    onClick={() => onSelectSignal?.(data.highest_impact_news!)}
                    className="text-sm font-bold text-white hover:text-cyan-300 transition-colors cursor-pointer"
                  >
                    {data.highest_impact_news.headline}
                  </h4>
                  <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
                    <span>{data.highest_impact_news.publisher}</span>
                    <span>•</span>
                    <span>{new Date(data.highest_impact_news.timestamp).toLocaleDateString()}</span>
                    <span>•</span>
                    <span className="text-cyan-400">Click to view full dossier</span>
                  </div>
                </div>
              )}

              {/* 5. Correlated News Stream List (Deduplicated Unique Articles) */}
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 px-1">
                  <span className="font-bold text-slate-200 uppercase flex items-center gap-2 text-xs font-mono">
                    <Radio className="w-4 h-4 text-cyan-400" />
                    Correlated Signals ({sortedUniqueSignals.length})
                  </span>

                  {/* Sorting Controls */}
                  <div className="flex items-center gap-1 bg-[#091122] border border-[#16233b] p-0.5 rounded-lg text-[11px] font-mono">
                    <button
                      onClick={() => setSortBy('latest')}
                      className={`px-2.5 py-1 rounded transition-all ${
                        sortBy === 'latest'
                          ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Latest News
                    </button>
                    <button
                      onClick={() => setSortBy('impact')}
                      className={`px-2.5 py-1 rounded transition-all ${
                        sortBy === 'impact'
                          ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Highest Impact
                    </button>
                    <button
                      onClick={() => setSortBy('confidence')}
                      className={`px-2.5 py-1 rounded transition-all ${
                        sortBy === 'confidence'
                          ? 'bg-blue-500/20 text-blue-300 font-bold border border-blue-500/30'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Highest Confidence
                    </button>
                  </div>
                </div>

                {sortedUniqueSignals.length === 0 ? (
                  <div className="p-8 bg-[#0a1224] border border-[#16243e] rounded-xl text-center space-y-1.5">
                    <Info className="w-6 h-6 text-slate-500 mx-auto" />
                    <p className="text-xs font-mono text-slate-400">
                      No unique news signals are currently available for this instrument.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {sortedUniqueSignals.map((sig) => {
                      const impactLvl = (sig.impact_level || 'LOW').toUpperCase();
                      const impactColor =
                        impactLvl === 'CRITICAL'
                          ? 'border-rose-500/40 text-rose-300 bg-rose-500/10'
                          : impactLvl === 'HIGH'
                          ? 'border-amber-500/40 text-amber-300 bg-amber-500/10'
                          : impactLvl === 'MEDIUM'
                          ? 'border-cyan-500/40 text-cyan-300 bg-cyan-500/10'
                          : 'border-slate-500/40 text-slate-400 bg-slate-500/10';

                      const rel = (
                        (sig as any).primary_relationship ||
                        sig.affected_instruments?.find((a) => a.symbol === data.symbol)?.relationship ||
                        'indirect'
                      ).toUpperCase();

                      const relColor =
                        rel === 'DIRECT'
                          ? 'bg-blue-500/20 text-blue-300 border-blue-500/40'
                          : rel === 'INDIRECT'
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                          : 'bg-amber-500/20 text-amber-300 border-amber-500/40';

                      const explanation =
                        (sig as any).primary_reason ||
                        sig.affected_instruments?.find((a) => a.symbol === data.symbol)?.reason ||
                        sig.impact_explanation ||
                        'Macro transmission channel evaluated by market impact model.';

                      return (
                        <div
                          key={sig.id}
                          onClick={() => onSelectSignal?.(sig)}
                          className="bg-[#0a1224] border border-[#16243e] hover:border-cyan-500/40 rounded-xl p-3.5 space-y-2 cursor-pointer transition-all hover:bg-[#0e1932]"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                                  sig.decider_sentiment === 'Bullish'
                                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                                    : sig.decider_sentiment === 'Bearish'
                                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                                    : 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                                }`}
                              >
                                {sig.decider_sentiment}
                              </span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${impactColor}`}>
                                {impactLvl} ({sig.impact_score || 0}/100)
                              </span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${relColor}`}>
                                {rel}
                              </span>
                            </div>
                            <span className="text-[11px] text-slate-500 font-mono">
                              {sig.publisher} • {new Date(sig.timestamp).toLocaleDateString()}
                            </span>
                          </div>

                          <h4 className="text-xs md:text-sm font-semibold text-white leading-snug line-clamp-2">
                            {sig.headline}
                          </h4>

                          {/* Specific transmission reason for this symbol */}
                          <div className="text-[11px] text-slate-400 bg-[#0e1830] p-2 rounded-lg border border-[#192c50] leading-relaxed">
                            {explanation}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* 6. Regulatory & Modeling Disclaimer */}
              <div className="text-[11px] text-slate-500 bg-[#060c18] border border-[#142138] p-3 rounded-xl flex items-start gap-2">
                <Scale className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Quantitative Research Notice:</strong> Impact scores measure macroeconomic transmission potential
                  and volatility dispersion. They do not constitute investment advice or guarantee future exchange rate movement.
                </span>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};

