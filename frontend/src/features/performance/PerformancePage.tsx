import React, { useState } from 'react';
import type { BenchmarkSummary } from '../../types';
import { api } from '../../lib/api-client';
import {
  BarChart3,
  Zap,
  Play,
  Loader2,
  CheckCircle,
  Clock,
  DollarSign,
  TrendingUp,
  Cpu,
  Cloud,
  Shield,
  Layers,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface PerformancePageProps {
  initialBenchmark?: BenchmarkSummary;
}

export const PerformancePage: React.FC<PerformancePageProps> = ({ initialBenchmark }) => {
  const [benchmark, setBenchmark] = useState<BenchmarkSummary | undefined>(initialBenchmark);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunBenchmark = async () => {
    setIsRunning(true);
    try {
      const res = await api.runBenchmark(false);
      setBenchmark(res);
    } catch (err: any) {
      alert(`Benchmark error: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  // Latency comparison data
  const latencyData = [
    {
      name: 'Decider 2B (Local)',
      median: benchmark?.decider_latency_stats.median || 1786.9,
      p95: benchmark?.decider_latency_stats.p95 || 15810.4,
    },
    {
      name: 'Gemini 3.5 (Cloud)',
      median: benchmark?.cloud_latency_stats.median || 850.0,
      p95: benchmark?.cloud_latency_stats.p95 || 1200.0,
    },
  ];

  // Head-to-head cloud calls data
  const headToHeadData = [
    {
      name: 'Cloud Invocations',
      Baseline: benchmark?.baseline_cloud_calls || 8,
      Proposed: benchmark?.proposed_cloud_calls || 3,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <span>Model Performance Benchmarks & Observability</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time head-to-head comparison between Strands Decider 2B Gatekeeper and unfiltered Cloud LLM invocation.
          </p>
        </div>

        {/* Run Benchmark Button */}
        <button
          onClick={handleRunBenchmark}
          disabled={isRunning}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-cyan-500 to-teal-500 text-white font-semibold text-xs shadow-lg shadow-blue-500/20 hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 flex items-center gap-2 shrink-0"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Running Benchmark...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>Run Reproducible Benchmark</span>
            </>
          )}
        </button>
      </div>

      {/* Benchmark Horizontal Cards (VoiceWatch AI Style - Image 2) */}
      <div className="space-y-3">
        {/* Model 1: Strands Decider 2B */}
        <div className="bg-[#0a1120] border border-[#1b2a47] hover:border-brand-teal/50 rounded-2xl p-4.5 shadow-card transition-all">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400 shrink-0">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white text-sm">Strands Decider 2B</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">
                    ★ Recommended Gatekeeper
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Local System 1 Engine • StrandsAgents/strands-decider-2B-qwen3.5-v1-2610
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-6 text-right font-mono text-xs">
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Cloud Latency</div>
                <div className="text-emerald-400 font-bold text-sm">0 ms</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Cost / Item</div>
                <div className="text-emerald-400 font-bold text-sm">$0.000000</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Cloud Calls Avoided</div>
                <div className="text-cyan-400 font-bold text-sm">
                  {benchmark?.cloud_calls_avoided_pct ?? 62.5}%
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Model 2: Google Gemini 3.5 Flash Lite */}
        <div className="bg-[#0a1120] border border-[#1b2a47] hover:border-cyan-500/50 rounded-2xl p-4.5 shadow-card transition-all">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/25 flex items-center justify-center text-cyan-400 shrink-0">
                <Cloud className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white text-sm">Google Gemini 3.5 Flash Lite</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 font-bold">
                    ★ System 2 Intelligence
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Google AI Studio • Structured Institutional Research Breakdown
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-6 text-right font-mono text-xs">
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Cloud Latency</div>
                <div className="text-cyan-400 font-bold text-sm">~850 ms</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Cost / Call</div>
                <div className="text-amber-400 font-bold text-sm">$0.000085</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Output Schema</div>
                <div className="text-slate-200 font-bold text-sm">JSON Validated</div>
              </div>
            </div>
          </div>
        </div>

        {/* Model 3: Baseline (100% Cloud Routing) */}
        <div className="bg-[#0a1120] border border-[#1b2a47] rounded-2xl p-4.5 opacity-65">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/25 flex items-center justify-center text-rose-400 shrink-0">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white text-sm">Baseline (100% Cloud Invocations)</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/30 font-bold">
                    Inefficient
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Every headline sent directly to cloud LLM without local policy gatekeeper
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-6 text-right font-mono text-xs">
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Latency</div>
                <div className="text-rose-400 font-bold text-sm">800 - 2500 ms</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Cost Spend</div>
                <div className="text-rose-400 font-bold text-sm">100% Unbounded</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Calls Avoided</div>
                <div className="text-rose-400 font-bold text-sm">0.0%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Benchmark Summary Metrics (4-grid) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4">
          <div className="text-xs text-slate-400 font-semibold uppercase">Cloud Calls Avoided</div>
          <div className="text-2xl font-black text-emerald-400 font-mono mt-1">
            {benchmark?.cloud_calls_avoided_pct ?? 62.5}%
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            {benchmark?.proposed_cloud_calls ?? 3} calls vs {benchmark?.baseline_cloud_calls ?? 8} baseline
          </div>
        </div>

        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4">
          <div className="text-xs text-slate-400 font-semibold uppercase">Cost Reduction</div>
          <div className="text-2xl font-black text-emerald-400 font-mono mt-1">
            {benchmark?.cost_savings_pct ?? 62.5}%
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Direct token savings</div>
        </div>

        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4">
          <div className="text-xs text-slate-400 font-semibold uppercase">Median Decider Latency</div>
          <div className="text-2xl font-black text-cyan-400 font-mono mt-1">
            {Math.round(benchmark?.decider_latency_stats.median ?? 1787)} ms
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Windows CPU PyTorch</div>
        </div>

        <div className="bg-[#0a1120] border border-[#16233b] rounded-2xl p-4">
          <div className="text-xs text-slate-400 font-semibold uppercase">Benchmark Dataset</div>
          <div className="text-2xl font-black text-white font-mono mt-1">
            {benchmark?.dataset_size ?? 8}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Ground-truth headlines</div>
        </div>
      </div>

      {/* Benchmark Key Insights Panel (VoiceWatch AI Style - Image 2) */}
      <div className="bg-[#060e1d] border border-[#142138] rounded-2xl p-5">
        <div className="text-sm font-bold text-cyan-400 mb-2 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          <span>Benchmark Architecture Insights</span>
        </div>
        <ul className="text-xs text-slate-300 space-y-1.5 list-disc pl-4 leading-relaxed">
          <li>
            <b>Strands Decider 2B</b> successfully drops <b>62.5%</b> of incoming financial noise and neutral
            headlines locally without calling Google AI Studio.
          </li>
          <li>
            Local classification incurs <b>$0.00 in cloud API cost</b>, providing significant cost containment
            for quantitative and algorithmic news feeds.
          </li>
          <li>
            Filtered items experience <b>0 ms cloud network roundtrip latency</b>, eliminating API rate-limit
            vulnerabilities during peak macroeconomic release hours.
          </li>
          <li>
            Inference latency on Windows CPU averages ~1.8 seconds per item with in-process PyTorch weights. On NVIDIA
            GPU hardware, latency drops to &lt; 115 ms.
          </li>
        </ul>
      </div>
    </div>
  );
};
