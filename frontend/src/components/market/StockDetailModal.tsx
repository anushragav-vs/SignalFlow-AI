import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api-client';
import type { StockDetail, Signal } from '../../types';
import {
  X,
  TrendingUp,
  TrendingDown,
  Activity,
  Sparkles,
  ExternalLink,
  Loader2,
  Calendar,
  AlertTriangle,
  Building,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Layers,
  Lightbulb,
  Clock,
  Zap,
} from 'lucide-react';

interface StockDetailModalProps {
  symbol: string | null;
  onClose: () => void;
  onFilterToStock?: (symbol: string) => void;
  onSelectAnotherStock?: (symbol: string) => void;
}

export const StockDetailModal: React.FC<StockDetailModalProps> = ({
  symbol,
  onClose,
  onFilterToStock,
  onSelectAnotherStock,
}) => {
  const [data, setData] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSignalId, setExpandedSignalId] = useState<number | null>(null);

  useEffect(() => {
    if (!symbol) return;
    let isMounted = true;
    setLoading(true);
    setError(null);
    setExpandedSignalId(null);

    api
      .getMarketQuote(symbol)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load stock data');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [symbol]);

  if (!symbol) return null;

  // Format volume
  const formatVol = (v?: number) => {
    if (!v) return 'N/A';
    if (v >= 1e9) return `${(v / 1e9).toFixed(2)}B`;
    if (v >= 1e6) return `${(v / 1e6).toFixed(2)}M`;
    if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K`;
    return v.toLocaleString();
  };

  // Sparkline coordinates
  const renderSparkline = (prices: number[]) => {
    if (!prices || prices.length < 2) return null;
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min || 1;
    const width = 280;
    const height = 55;
    const pad = 6;

    const points = prices.map((p, i) => {
      const x = pad + (i / (prices.length - 1)) * (width - pad * 2);
      const y = height - pad - ((p - min) / range) * (height - pad * 2);
      return `${x},${y}`;
    });

    const isPositive = prices[prices.length - 1] >= prices[0];
    const strokeColor = isPositive ? '#10b981' : '#f43f5e';
    const fillGradient = isPositive ? 'url(#greenGradModal)' : 'url(#redGradModal)';

    return (
      <svg width={width} height={height} className="overflow-visible">
        <defs>
          <linearGradient id="greenGradModal" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
          </linearGradient>
          <linearGradient id="redGradModal" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.0" />
          </linearGradient>
        </defs>
        <polygon
          points={`${pad},${height} ${points.join(' ')} ${width - pad},${height}`}
          fill={fillGradient}
        />
        <polyline
          fill="none"
          stroke={strokeColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points.join(' ')}
        />
        {prices.length > 0 && (
          <circle
            cx={points[points.length - 1].split(',')[0]}
            cy={points[points.length - 1].split(',')[1]}
            r="4"
            fill={strokeColor}
            className="animate-ping"
          />
        )}
      </svg>
    );
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-3 md:p-6 animate-in fade-in duration-150">
      <div className="bg-[#091021] border border-[#1e2f50] rounded-2xl w-full max-w-4xl max-h-[92vh] overflow-y-auto shadow-2xl flex flex-col text-slate-100">
        {/* Header Bar */}
        <div className="p-5 border-b border-[#142138] flex items-center justify-between sticky top-0 bg-[#091021]/95 backdrop-blur z-20">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl md:text-2xl text-white font-mono tracking-tight">
                  {data?.display_symbol || symbol.replace('^', '')}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase tracking-wider bg-[#101b33] text-cyan-400 border border-[#1e3258]">
                  {data?.category || 'MARKET ASSET'}
                </span>
                <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-400 ml-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  Live Feed
                </span>
              </div>
              <div className="text-xs text-slate-400 font-medium mt-0.5">
                {data?.name || 'Financial Asset Intelligence & Real-Time Market Stream'}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-[#0c1527] border border-[#1a2b4a] text-slate-400 hover:text-white hover:border-slate-500 transition-colors"
            title="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 flex-1">
          {loading ? (
            <div className="py-24 flex flex-col items-center justify-center gap-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-brand-teal" />
              <span className="text-sm font-semibold text-white">Connecting to live market quotes & database...</span>
              <span className="text-xs text-slate-500">Querying Yahoo Finance & SQLite intelligence ledger</span>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          ) : data ? (
            <>
              {/* 1. Live Price & Sparkline Hero Card */}
              <div className="bg-[#0c162c] border border-[#1d3056] rounded-2xl p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
                <div>
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Current Market Price</div>
                  <div className="flex items-baseline gap-3 mt-1">
                    <span className="text-3xl md:text-4xl font-extrabold text-white font-mono tracking-tight">
                      ${data.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <span
                      className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-sm font-bold font-mono ${
                        data.is_positive
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      }`}
                    >
                      {data.is_positive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      <span>{data.change_pct > 0 ? `+${data.change_pct.toFixed(2)}%` : `${data.change_pct.toFixed(2)}%`}</span>
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 font-mono mt-1">
                    Prev Close: ${data.prev_close.toFixed(2)} • Exchange: {data.exchange} • Updated {data.updated_at}
                  </div>
                </div>

                {/* 5-Day Sparkline Trend */}
                <div className="flex flex-col items-end">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    5-Day Historical Trend
                  </div>
                  <div className="bg-[#070c18] border border-[#16233b] rounded-xl p-2 shadow-inner">
                    {renderSparkline(data.sparkline)}
                  </div>
                </div>
              </div>

              {/* 2. Key Statistics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="bg-[#091122] border border-[#16243f] rounded-xl p-3.5">
                  <div className="text-slate-400 text-[11px] font-medium">Day Range</div>
                  <div className="font-mono text-white font-bold text-sm mt-0.5">
                    ${data.day_low?.toFixed(2) || '—'} - ${data.day_high?.toFixed(2) || '—'}
                  </div>
                </div>
                <div className="bg-[#091122] border border-[#16243f] rounded-xl p-3.5">
                  <div className="text-slate-400 text-[11px] font-medium">52-Week Range</div>
                  <div className="font-mono text-white font-bold text-sm mt-0.5">
                    ${data.year_low?.toFixed(2) || '—'} - ${data.year_high?.toFixed(2) || '—'}
                  </div>
                </div>
                <div className="bg-[#091122] border border-[#16243f] rounded-xl p-3.5">
                  <div className="text-slate-400 text-[11px] font-medium">Trading Volume</div>
                  <div className="font-mono text-white font-bold text-sm mt-0.5">{formatVol(data.volume)}</div>
                </div>
                <div className="bg-[#091122] border border-[#16243f] rounded-xl p-3.5">
                  <div className="text-slate-400 text-[11px] font-medium">Market Sentiment Index</div>
                  <div
                    className={`font-mono font-bold text-sm mt-0.5 ${
                      data.sentiment_stats.sentiment_score >= 60
                        ? 'text-emerald-400'
                        : data.sentiment_stats.sentiment_score <= 40
                        ? 'text-rose-400'
                        : 'text-indigo-400'
                    }`}
                  >
                    {data.sentiment_stats.sentiment_score}/100 ({data.sentiment_stats.sentiment_label})
                  </div>
                </div>
              </div>

              {/* 3. Deep Research & Correlated Signals */}
              <div className="space-y-4 pt-2">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <h4 className="text-sm font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    <span>Correlated News Signals & Research Intelligence</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 font-mono">
                      {data.related_signals_count} matched
                    </span>
                  </h4>

                  {onFilterToStock && (
                    <button
                      onClick={() => {
                        onFilterToStock(data.display_symbol);
                        onClose();
                      }}
                      className="text-xs text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1.5 self-start sm:self-auto bg-cyan-500/10 border border-cyan-500/20 px-3 py-1.5 rounded-lg hover:border-cyan-500/50 transition-colors"
                    >
                      <span>Filter News Stream to this Ticker</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {data.related_signals && data.related_signals.length > 0 ? (
                  <div className="space-y-3">
                    {data.related_signals.map((sig) => {
                      const isExpanded = expandedSignalId === sig.id;
                      const hasGemini = sig.gemini_status === 'success' && (sig.event_summary || sig.reported_facts?.length);

                      return (
                        <div
                          key={sig.id}
                          className="bg-[#080f20] border border-[#172643] rounded-xl p-4 space-y-3 hover:border-cyan-500/40 transition-colors shadow-sm"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                            <div className="flex items-center gap-2">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase ${
                                  sig.decider_sentiment === 'Bullish'
                                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                    : sig.decider_sentiment === 'Bearish'
                                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                    : sig.decider_sentiment === 'Neutral'
                                    ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                }`}
                              >
                                {sig.decider_sentiment}
                              </span>
                              <span className="font-mono text-cyan-400 text-[11px] font-semibold">
                                {(sig.decider_confidence * 100).toFixed(0)}% Confidence
                              </span>
                              <span className="text-slate-500 text-[11px]">• {sig.publisher}</span>
                            </div>
                            <span className="text-[11px] text-slate-500 font-mono">
                              {sig.timestamp?.slice(0, 16).replace('T', ' ')}
                            </span>
                          </div>

                          <div className="text-sm font-semibold text-white leading-snug">{sig.headline}</div>

                          {/* Gemini Summary Box */}
                          {sig.event_summary && (
                            <div className="bg-[#060b17] border border-[#132038] rounded-lg p-3 text-xs text-slate-300 space-y-2">
                              <div className="font-bold text-cyan-400 text-[10px] uppercase tracking-wider flex items-center gap-1.5">
                                <Sparkles className="w-3 h-3 text-cyan-400" />
                                <span>AI Summary • Google Gemini 3.5 Intelligence</span>
                              </div>
                              <p className="leading-relaxed text-slate-200">{sig.event_summary}</p>

                              {/* Toggle Deep Dossier */}
                              <button
                                type="button"
                                onClick={() => setExpandedSignalId(isExpanded ? null : sig.id)}
                                className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1 pt-1"
                              >
                                {isExpanded ? (
                                  <>
                                    <span>Hide Deep Research Breakdown</span>
                                    <ChevronUp className="w-3.5 h-3.5" />
                                  </>
                                ) : (
                                  <>
                                    <span>View Deep Research Breakdown</span>
                                    <ChevronDown className="w-3.5 h-3.5" />
                                  </>
                                )}
                              </button>
                            </div>
                          )}

                          {/* Expanded Full Institutional Dossier */}
                          {isExpanded && (
                            <div className="bg-[#040812] border border-[#182742] rounded-xl p-4 text-xs space-y-4 animate-in fade-in duration-150">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Left Column */}
                                <div className="space-y-3">
                                  {/* 1. Reported Facts */}
                                  <div>
                                    <div className="font-bold text-slate-200 mb-1 flex items-center gap-1.5 text-emerald-400">
                                      <CheckCircle2 className="w-3.5 h-3.5" />
                                      <span>1. Reported Facts (Source Verifiable)</span>
                                    </div>
                                    {sig.reported_facts && sig.reported_facts.length > 0 ? (
                                      <ul className="list-disc pl-4 text-slate-300 space-y-1">
                                        {sig.reported_facts.map((fact, idx) => (
                                          <li key={idx}>{fact}</li>
                                        ))}
                                      </ul>
                                    ) : (
                                      <p className="text-slate-400">{sig.event_summary}</p>
                                    )}
                                  </div>

                                  {/* 2. Transmission Mechanism */}
                                  <div>
                                    <div className="font-bold text-slate-200 mb-1 flex items-center gap-1.5 text-blue-400">
                                      <Layers className="w-3.5 h-3.5" />
                                      <span>2. Economic Transmission Mechanism</span>
                                    </div>
                                    <p className="text-slate-300 leading-relaxed">
                                      {sig.transmission_mechanism ||
                                        'Direct cash flow and multiple valuation repricing.'}
                                    </p>
                                  </div>

                                  {/* 3. Analytical Hypotheses */}
                                  {sig.analytical_hypotheses && sig.analytical_hypotheses.length > 0 && (
                                    <div>
                                      <div className="font-bold text-slate-200 mb-1 flex items-center gap-1.5 text-purple-400">
                                        <Lightbulb className="w-3.5 h-3.5" />
                                        <span>3. Forward-Looking Analytical Hypotheses</span>
                                      </div>
                                      <ul className="list-disc pl-4 text-slate-300 space-y-1">
                                        {sig.analytical_hypotheses.map((hyp, idx) => (
                                          <li key={idx}>{hyp}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                </div>

                                {/* Right Column */}
                                <div className="space-y-3">
                                  {/* 4. Directional Bias & Horizon */}
                                  <div>
                                    <div className="font-bold text-slate-200 mb-1">4. Impact Horizon & Bias</div>
                                    <div className="flex flex-wrap items-center gap-2">
                                      <span
                                        className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase ${
                                          sig.decider_sentiment === 'Bullish'
                                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                                            : sig.decider_sentiment === 'Bearish'
                                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                                            : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                                        }`}
                                      >
                                        Bias: {sig.decider_sentiment}
                                      </span>
                                      {sig.market_impact_horizon && (
                                        <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px] font-mono">
                                          ⏱ {sig.market_impact_horizon}
                                        </span>
                                      )}
                                      {sig.institutional_risk_level && (
                                        <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[10px] font-mono">
                                          ⚡ Risk: {sig.institutional_risk_level}
                                        </span>
                                      )}
                                    </div>
                                  </div>

                                  {/* 5. Affected Asset Classes */}
                                  <div>
                                    <div className="font-bold text-slate-200 mb-1">5. Affected Asset Classes</div>
                                    <div className="flex flex-wrap gap-1">
                                      {sig.affected_assets && sig.affected_assets.length > 0 ? (
                                        sig.affected_assets.map((asset, idx) => (
                                          <button
                                            key={idx}
                                            type="button"
                                            onClick={() => onSelectAnotherStock?.(asset)}
                                            className="font-mono bg-blue-500/10 text-blue-300 hover:bg-cyan-500/20 hover:text-cyan-200 border border-blue-500/30 px-2 py-0.5 rounded text-[10px] transition-colors"
                                          >
                                            {asset}
                                          </button>
                                        ))
                                      ) : (
                                        <span className="text-slate-500">General Equities</span>
                                      )}
                                    </div>
                                  </div>

                                  {/* 6. Catalyst Watchpoints */}
                                  {sig.catalyst_watchpoints && sig.catalyst_watchpoints.length > 0 && (
                                    <div>
                                      <div className="font-bold text-slate-200 mb-1 text-cyan-400">
                                        6. Catalyst Watchpoints
                                      </div>
                                      <ul className="list-disc pl-4 text-slate-300 space-y-0.5">
                                        {sig.catalyst_watchpoints.map((cat, idx) => (
                                          <li key={idx}>{cat}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {/* 7. Uncertainties & Risks */}
                                  <div>
                                    <div className="font-bold text-slate-200 mb-1 text-amber-400">
                                      7. Uncertainties & Downside Risks
                                    </div>
                                    {sig.uncertainties && sig.uncertainties.length > 0 ? (
                                      <ul className="list-disc pl-4 text-slate-300 space-y-0.5">
                                        {sig.uncertainties.map((u, idx) => (
                                          <li key={idx}>⚠️ {u}</li>
                                        ))}
                                      </ul>
                                    ) : (
                                      <p className="text-slate-400">Consensus macro volatility.</p>
                                    )}
                                  </div>
                                </div>
                              </div>

                              <div className="pt-2 border-t border-[#16233b] flex items-center justify-between text-[11px] text-slate-500 font-mono">
                                <span>Model: {sig.gemini_model_id || 'gemini-3.5-flash-lite'}</span>
                                <span>Cloud Latency: {Math.round(sig.cloud_latency_ms || 0)} ms</span>
                                <span>Spend: ${(sig.estimated_cost_usd || 0).toFixed(6)}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-6 rounded-xl bg-[#080f20] border border-[#172643] text-center text-xs text-slate-400 space-y-2">
                    <p>No processed signals in the local ledger currently mention {data.display_symbol}.</p>
                    <p className="text-slate-500">
                      Try ingesting fresh news using "Analyze News" or enter a breaking headline in the Custom Headline Analyzer.
                    </p>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-[#142138] flex items-center justify-between text-xs text-slate-500 bg-[#070c18]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-brand-teal" />
            <span>Institutional Market Data & Research Intelligence • SignalFlow Engine</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#0c1527] border border-[#1a2b4a] text-slate-200 hover:text-white hover:border-slate-500 transition-colors font-semibold"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
