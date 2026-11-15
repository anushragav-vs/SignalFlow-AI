import React, { useState, useMemo } from 'react';
import type { Signal } from '../../types';
import {
  BarChart2,
  AlertTriangle,
  Zap,
  TrendingUp,
  Activity,
  ShieldAlert,
  HelpCircle,
  Scale,
  Sparkles,
  Flame,
  Clock,
  ChevronRight,
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface MarketImpactPanelProps {
  signals: Signal[];
  distribution: Record<string, number>;
  dimensionAverages: Record<string, number>;
  onOpenSignalDetail?: (signal: Signal) => void;
}

export const MarketImpactPanel: React.FC<MarketImpactPanelProps> = ({
  signals,
  distribution,
  dimensionAverages,
  onOpenSignalDetail,
}) => {
  const [levelFilter, setLevelFilter] = useState<string>('ALL');

  // Deduplicate signals by normalized headline
  const deduplicatedSignals = useMemo(() => {
    const seen = new Set<string>();
    return signals.filter((s) => {
      const key = (s.headline || '').trim().toLowerCase();
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [signals]);

  const filteredSignals = useMemo(() => {
    if (levelFilter === 'ALL') return deduplicatedSignals;
    return deduplicatedSignals.filter(
      (s) => (s.impact_level || 'LOW').toUpperCase() === levelFilter.toUpperCase()
    );
  }, [deduplicatedSignals, levelFilter]);

  // Priority Critical & High Impact Events
  const prioritySignals = useMemo(() => {
    return deduplicatedSignals
      .filter((s) => {
        const lvl = (s.impact_level || '').toUpperCase();
        return lvl === 'CRITICAL' || lvl === 'HIGH';
      })
      .slice(0, 3);
  }, [deduplicatedSignals]);

  const pieData = [
    { name: 'Critical', value: distribution['CRITICAL'] || 0, color: '#f43f5e' },
    { name: 'High', value: distribution['HIGH'] || 0, color: '#f59e0b' },
    { name: 'Medium', value: distribution['MEDIUM'] || 0, color: '#06b6d4' },
    { name: 'Low', value: distribution['LOW'] || 0, color: '#64748b' },
  ].filter((d) => d.value > 0);

  const dimensionItems = [
    {
      label: 'Economic Importance',
      weight: '25%',
      value: Math.round(dimensionAverages['economic_importance'] || 0),
      desc: 'Central bank announcements, GDP, inflation & employment releases',
    },
    {
      label: 'Surprise Factor',
      weight: '20%',
      value: Math.round(dimensionAverages['surprise_magnitude'] || 0),
      desc: 'Deviation from median market expectations and consensus',
    },
    {
      label: 'Direct Relevance',
      weight: '20%',
      value: Math.round(dimensionAverages['instrument_relevance'] || 0),
      desc: 'Direct or transmission nexus to supported forex pairs',
    },
    {
      label: 'Source Reliability',
      weight: '10%',
      value: Math.round(dimensionAverages['source_reliability'] || 0),
      desc: 'Institutional wire pedigree & central bank primary sources',
    },
    {
      label: 'Information Novelty',
      weight: '10%',
      value: Math.round(dimensionAverages['news_novelty'] || 0),
      desc: 'Freshness and novelty relative to historical wire traffic',
    },
    {
      label: 'Historical Volatility',
      weight: '15%',
      value: Math.round(dimensionAverages['potential_volatility'] || 0),
      desc: 'Historical FX pip dispersion following comparable macro catalysts',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Disclaimer Banner: Decoupled Magnitude Principle */}
      <div className="bg-[#0b1426] border border-[#1b2f56] rounded-2xl p-4 flex items-start gap-3 shadow-md">
        <Scale className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 space-y-1">
          <div className="flex items-center gap-2">
            <strong className="text-white font-mono uppercase tracking-wider block">
              Market Impact Predictor • Decoupled Magnitude Principle
            </strong>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
              Research Metric
            </span>
          </div>
          <p className="text-slate-400 leading-relaxed">
            Market Impact Score (0–100) measures expected macroeconomic significance, news surprise, and potential
            volatility dispersion. It <strong>reflects potential market magnitude, not confirmed price direction</strong>. A critical-impact event can be bullish, bearish, or directionally uncertain.
          </p>
        </div>
      </div>

      {/* Priority Critical & High Impact Events Strip */}
      {prioritySignals.length > 0 && (
        <div className="space-y-2.5">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <Flame className="w-4 h-4 text-rose-400" />
              <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                Priority High & Critical Impact Events
              </h3>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Immediate institutional catalyst watch
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {prioritySignals.map((sig) => {
              const score = sig.impact_score || 0;
              const isCrit = (sig.impact_level || '').toUpperCase() === 'CRITICAL';
              return (
                <div
                  key={`priority-${sig.id}`}
                  onClick={() => onOpenSignalDetail?.(sig)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer shadow-md group ${
                    isCrit
                      ? 'bg-gradient-to-b from-[#181120] to-[#0c162e] border-rose-500/40 hover:border-rose-400'
                      : 'bg-gradient-to-b from-[#18181a] to-[#0c162e] border-amber-500/40 hover:border-amber-400'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                        isCrit
                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                          : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                      }`}
                    >
                      {sig.impact_level} ({score}/100)
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {sig.publisher}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-white group-hover:text-cyan-300 transition-colors line-clamp-2 leading-relaxed mb-2">
                    {sig.headline}
                  </h4>

                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1 border-t border-[#1a2d52]">
                    <span>Vol: <strong className="text-cyan-400">{sig.volatility_assessment || 'moderate'}</strong></span>
                    <span className="text-cyan-400 group-hover:underline flex items-center">
                      View Dossier <ChevronRight className="w-3 h-3 ml-0.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Overview Analytics Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Card 1: Impact Level Distribution Chart */}
        <div className="bg-[#091122] border border-[#16243e] rounded-2xl p-4.5 space-y-3 shadow-lg">
          <div className="flex items-center justify-between text-xs font-mono font-bold text-slate-300 uppercase">
            <span>Impact Level Distribution</span>
            <span className="text-cyan-400 font-mono">{deduplicatedSignals.length} Events</span>
          </div>

          <div className="h-44 flex items-center justify-center">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    innerRadius={45}
                    outerRadius={65}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0b1426', borderColor: '#1b2f56', borderRadius: '8px', fontSize: '12px' }}
                    itemStyle={{ color: '#ffffff' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <span className="text-xs text-slate-500 font-mono">No analyzed signals yet</span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] font-mono pt-1">
            <div className="flex items-center gap-1.5 text-rose-400">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0" />
              <span>Critical: {distribution['CRITICAL'] || 0}</span>
            </div>
            <div className="flex items-center gap-1.5 text-amber-400">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
              <span>High: {distribution['HIGH'] || 0}</span>
            </div>
            <div className="flex items-center gap-1.5 text-cyan-400">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 shrink-0" />
              <span>Medium: {distribution['MEDIUM'] || 0}</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-400">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500 shrink-0" />
              <span>Low: {distribution['LOW'] || 0}</span>
            </div>
          </div>
        </div>

        {/* Card 2: 6 Normalized Impact Dimensions Breakdown */}
        <div className="bg-[#091122] border border-[#16243e] rounded-2xl p-4.5 space-y-3 shadow-lg lg:col-span-2">
          <div className="flex items-center justify-between text-xs font-mono font-bold text-slate-300 uppercase">
            <span>6 Normalized Impact Dimensions</span>
            <span className="text-slate-500 text-[11px]">Normalized Scale (0–100)</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-1">
            {dimensionItems.map((d, i) => (
              <div key={i} className="bg-[#0c162e] border border-[#182745] rounded-xl p-3 space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-300 font-medium truncate" title={d.label}>
                    {d.label}
                  </span>
                  <span className="font-mono font-extrabold text-white shrink-0 ml-1">
                    {d.value}/100
                  </span>
                </div>
                <div className="w-full bg-[#142038] h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      d.value >= 75
                        ? 'bg-rose-500'
                        : d.value >= 50
                        ? 'bg-amber-400'
                        : d.value >= 25
                        ? 'bg-cyan-400'
                        : 'bg-slate-500'
                    }`}
                    style={{ width: `${Math.min(100, d.value)}%` }}
                  />
                </div>
                <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono">
                  <span className="truncate pr-1" title={d.desc}>{d.desc}</span>
                  <span className="shrink-0 font-bold text-cyan-400">{d.weight}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="text-[11px] text-slate-400 bg-[#0c162e] p-2.5 rounded-lg border border-[#1b2c4e] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1 font-mono">
            <span>Linear Formula: 25% Econ + 20% Surp + 20% Rel + 10% Src + 10% Nov + 15% Vol</span>
            <span className="text-cyan-400">Low (0–24) • Med (25–49) • High (50–74) • Crit (75+)</span>
          </div>
        </div>
      </div>

      {/* Filter Tabs & Impact Feed */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-1">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold text-slate-300 uppercase">
              Impact Signals Feed ({filteredSignals.length})
            </span>
          </div>

          <div className="flex items-center gap-1.5 bg-[#0a1224] border border-[#16243e] p-1 rounded-xl overflow-x-auto">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setLevelFilter(lvl)}
                className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-all ${
                  levelFilter === lvl
                    ? 'bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        {filteredSignals.length === 0 ? (
          <div className="p-8 bg-[#091122] border border-[#16243e] rounded-2xl text-center space-y-2">
            <HelpCircle className="w-8 h-8 text-slate-500 mx-auto" />
            <h4 className="text-sm font-semibold text-white">No Signals in Selected Level</h4>
            <p className="text-xs text-slate-400">Select another filter tab to view analyzed market events.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredSignals.map((sig) => {
              const impactScore = sig.impact_score || 0;
              const lvl = (sig.impact_level || 'LOW').toUpperCase();
              const lvlColor =
                lvl === 'CRITICAL'
                  ? 'text-rose-400 bg-rose-500/10 border-rose-500/30'
                  : lvl === 'HIGH'
                  ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
                  : lvl === 'MEDIUM'
                  ? 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30'
                  : 'text-slate-400 bg-slate-500/10 border-slate-500/30';

              const sentiment = (sig.decider_sentiment || 'NEUTRAL').toUpperCase();
              const sentimentColor =
                sentiment === 'BULLISH'
                  ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                  : sentiment === 'BEARISH'
                  ? 'text-rose-400 bg-rose-500/10 border-rose-500/30'
                  : 'text-slate-400 bg-slate-500/10 border-slate-500/30';

              return (
                <div
                  key={sig.id}
                  onClick={() => onOpenSignalDetail?.(sig)}
                  className="bg-[#091122] hover:bg-[#0c162e] border border-[#15233c] hover:border-cyan-500/50 p-4.5 rounded-xl transition-all duration-150 cursor-pointer shadow-md group flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-2 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold uppercase border ${lvlColor}`}>
                        {lvl} ({impactScore}/100)
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold uppercase border ${sentimentColor}`}>
                        {sig.decider_sentiment || 'Neutral'}
                      </span>
                      <span className="text-xs font-mono text-slate-400 capitalize">
                        {sig.event_category?.replace(/_/g, ' ') || 'Macro Event'}
                      </span>
                      <span className="text-xs text-slate-500 font-mono">• {sig.publisher}</span>
                      {sig.timestamp && (
                        <span className="text-xs text-slate-500 font-mono flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(sig.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      )}
                    </div>

                    <h4 className="text-sm md:text-base font-bold text-white group-hover:text-cyan-300 transition-colors leading-snug">
                      {sig.headline}
                    </h4>

                    {sig.impact_explanation && (
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                        {sig.impact_explanation}
                      </p>
                    )}

                    {/* Affected Forex Pairs Chips */}
                    {sig.affected_instruments && sig.affected_instruments.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[10px] font-mono uppercase text-slate-500 mr-1">Pairs:</span>
                        {sig.affected_instruments.slice(0, 4).map((inst, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[#101b33] border border-[#1c2e54] text-slate-300"
                          >
                            {inst.symbol}
                            <span className="ml-1 text-[9px] uppercase text-cyan-400 font-bold">
                              {inst.relationship === 'direct' ? 'DIR' : inst.relationship === 'indirect' ? 'IND' : 'POT'}
                            </span>
                          </span>
                        ))}
                        {sig.affected_instruments.length > 4 && (
                          <span className="text-[10px] font-mono text-slate-500">
                            +{sig.affected_instruments.length - 4} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Right Score Badge & Volatility Gauge */}
                  <div className="flex md:flex-col items-center md:items-end justify-between md:justify-center gap-2 shrink-0 border-t md:border-t-0 border-[#16233b] pt-2 md:pt-0">
                    <div className="text-right">
                      <div className="text-2xl font-black font-mono text-white tracking-tight">
                        {impactScore}
                        <span className="text-xs text-slate-500 font-normal">/100</span>
                      </div>
                      <span className="text-[10px] font-mono uppercase font-bold text-slate-400 block">
                        Vol: <span className="text-cyan-400">{sig.volatility_assessment || 'moderate'}</span>
                      </span>
                    </div>

                    <span className="text-xs text-cyan-400 font-mono group-hover:underline flex items-center">
                      Details <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                    </span>
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


