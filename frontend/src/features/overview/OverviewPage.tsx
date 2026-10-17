import React from 'react';
import type { KPIs, Signal } from '../../types';
import {
  Inbox,
  FileCheck,
  TrendingUp,
  TrendingDown,
  MinusCircle,
  AlertTriangle,
  Clock,
  Sparkles,
  ShieldCheck,
  DollarSign,
  Zap,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

interface OverviewPageProps {
  kpis: KPIs;
  signals: Signal[];
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ kpis, signals }) => {
  // Sentiment breakdown data
  const sentimentChartData = [
    { name: 'Bullish', count: kpis.bullish_count, color: '#10b981' },
    { name: 'Bearish', count: kpis.bearish_count, color: '#ef4444' },
    { name: 'Neutral', count: kpis.neutral_count, color: '#8b5cf6' },
    { name: 'Noise', count: kpis.noise_count, color: '#64748b' },
  ];

  // Cloud avoidance gatekeeping data
  const gatekeepingData = [
    { name: 'Routed to Gemini (Cloud)', value: kpis.sent_to_gemini, color: '#06b6d4' },
    { name: 'Filtered Locally at Edge', value: kpis.cloud_calls_avoided_count, color: '#1e293b' },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Overview Dashboard</h2>
        <p className="text-xs text-slate-400 mt-1">
          Real-time System One (Strands Decider 2B) and System Two (Google Gemini) operational metrics.
        </p>
      </div>

      {/* KPI Stat Cards (4-column grid) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Headlines */}
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4 shadow-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Received</span>
            <Inbox className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">{kpis.total_received}</div>
          <div className="text-[11px] text-slate-500 mt-1">
            {kpis.unique_processed} unique normalized headlines
          </div>
        </div>

        {/* Cloud Calls Avoided */}
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4 shadow-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Calls Avoided</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 font-mono glow-green-text">
            {kpis.cloud_calls_avoided_pct}%
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            {kpis.cloud_calls_avoided_count} items kept off cloud
          </div>
        </div>

        {/* Gemini Analyses */}
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4 shadow-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Sent to Gemini</span>
            <Sparkles className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-cyan-400 font-mono">{kpis.sent_to_gemini}</div>
          <div className="text-[11px] text-slate-500 mt-1">
            {kpis.successful_analyses} successful dossiers
          </div>
        </div>

        {/* Cloud Spend */}
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4 shadow-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Cloud Spend</span>
            <DollarSign className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400 font-mono">
            ${kpis.total_cloud_spend_usd.toFixed(5)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Exact token usage billing</div>
        </div>
      </div>

      {/* Second Row Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Bullish */}
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4">
          <div className="flex items-center justify-between text-emerald-400 mb-1">
            <span className="text-xs font-semibold">Bullish Signals</span>
            <TrendingUp className="w-4 h-4" />
          </div>
          <div className="text-xl font-bold text-white font-mono">{kpis.bullish_count}</div>
        </div>

        {/* Bearish */}
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4">
          <div className="flex items-center justify-between text-rose-400 mb-1">
            <span className="text-xs font-semibold">Bearish Signals</span>
            <TrendingDown className="w-4 h-4" />
          </div>
          <div className="text-xl font-bold text-white font-mono">{kpis.bearish_count}</div>
        </div>

        {/* Neutral */}
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4">
          <div className="flex items-center justify-between text-indigo-400 mb-1">
            <span className="text-xs font-semibold">Consensus Neutral</span>
            <MinusCircle className="w-4 h-4" />
          </div>
          <div className="text-xl font-bold text-white font-mono">{kpis.neutral_count}</div>
        </div>

        {/* Noise */}
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-semibold">Noise Dropped</span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-xl font-bold text-white font-mono">{kpis.noise_count}</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Market Classification Distribution */}
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-5 shadow-card">
          <h3 className="text-sm font-bold text-white mb-1">Market Sentiment Distribution</h3>
          <p className="text-xs text-slate-400 mb-4">
            Aggregated classification breakdown produced by Strands Decider 2B.
          </p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sentimentChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0c1527',
                    border: '1px solid #1e2e4f',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {sentimentChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cloud Gatekeeping Ratio */}
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-5 shadow-card">
          <h3 className="text-sm font-bold text-white mb-1">Policy Gatekeeping Ratio</h3>
          <p className="text-xs text-slate-400 mb-4">
            Proportion of headlines routed to Google Gemini vs locally handled at edge.
          </p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={gatekeepingData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {gatekeepingData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0c1527',
                    border: '1px solid #1e2e4f',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Legend
                  wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                  formatter={(value) => <span className="text-slate-300">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Latency Footprint Callout */}
      <div className="bg-[#060e1d] border border-[#142138] rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-white">System 1 vs System 2 Asymmetry</div>
            <div className="text-xs text-slate-400">
              Filtered items experience <b className="text-emerald-400">0 ms cloud latency</b> and{' '}
              <b className="text-emerald-400">$0.00 cost</b>, shielding downstream architectures from API rate limits.
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono shrink-0">
          <div className="text-right">
            <div className="text-slate-500">AVG DECIDER LATENCY</div>
            <div className="text-white font-bold">{Math.round(kpis.avg_decider_latency_ms)} ms</div>
          </div>
          <div className="text-right">
            <div className="text-slate-500">AVG GEMINI LATENCY</div>
            <div className="text-cyan-400 font-bold">{Math.round(kpis.avg_cloud_latency_ms)} ms</div>
          </div>
        </div>
      </div>
    </div>
  );
};
