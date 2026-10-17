import React from 'react';
import type { AppHealth } from '../../types';
import { Zap, ShieldCheck, Database, Radio, CheckCircle2, AlertCircle } from 'lucide-react';

interface HeaderProps {
  health?: AppHealth;
  isBackendConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({ health, isBackendConnected }) => {
  const geminiConfigured = health?.system_two.configured ?? false;

  return (
    <header className="w-full bg-[#070c18] border-b border-[#16233b] px-6 py-4 flex flex-wrap items-center justify-between gap-4">
      {/* Brand & Subtitle */}
      <div className="flex items-center gap-3.5">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 via-teal-500 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20 shrink-0">
          <Zap className="w-5 h-5 fill-white text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              SignalFlow AI
            </h1>
            <span className="text-[11px] font-mono uppercase bg-brand-teal/15 text-brand-teal border border-brand-teal/30 px-2 py-0.5 rounded-full font-semibold">
              v2.0 React
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Real-Time Algorithmic Financial News Filter & Policy Gatekeeper
          </p>
        </div>
      </div>

      {/* Integration Status Badges (VoiceWatch AI Style) */}
      <div className="flex items-center gap-2.5 flex-wrap">
        {/* Google Cloud Gemini */}
        <div className="flex items-center gap-2 bg-[#0c1527] border border-[#1b2a47] rounded-lg px-3 py-1.5 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              geminiConfigured
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                : 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]'
            }`}
          />
          <span className="font-semibold text-slate-200">Google Cloud</span>
          <span className="text-slate-400 font-mono text-[11px]">
            {health?.system_two.model || 'Gemini 3.5'}
          </span>
        </div>

        {/* Strands Decider 2B */}
        <div className="flex items-center gap-2 bg-[#0c1527] border border-[#1b2a47] rounded-lg px-3 py-1.5 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
          <ShieldCheck className="w-3.5 h-3.5 text-brand-teal" />
          <span className="font-semibold text-slate-200">Strands Decider 2B</span>
          <span className="text-slate-400 font-mono text-[11px]">Local CPU</span>
        </div>

        {/* SQLite DB */}
        <div className="flex items-center gap-2 bg-[#0c1527] border border-[#1b2a47] rounded-lg px-3 py-1.5 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
          <Database className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-semibold text-slate-200">SQLite Audit</span>
          <span className="text-slate-400 text-[11px]">Immutable</span>
        </div>

        {/* RSS Feeds */}
        <div className="flex items-center gap-2 bg-[#0c1527] border border-[#1b2a47] rounded-lg px-3 py-1.5 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
          <Radio className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-semibold text-slate-200">Financial RSS</span>
          <span className="text-slate-400 text-[11px]">Multi-Stream</span>
        </div>

        {/* Backend Connection Indicator */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium ${
            isBackendConnected
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}
          title={isBackendConnected ? 'Backend API Connected (:8008)' : 'Backend API Disconnected'}
        >
          {isBackendConnected ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>API Live</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-3.5 h-3.5" />
              <span>API Offline</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
