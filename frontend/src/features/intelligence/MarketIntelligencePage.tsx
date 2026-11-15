import React, { useState, useEffect, useCallback } from 'react';
import type { Signal, InstrumentSummary, AlertRule, MarketAlert, IntelligenceStats } from '../../types';
import { api } from '../../lib/api-client';
import { SmartTickerDetectionPanel } from './SmartTickerDetectionPanel';
import { MarketImpactPanel } from './MarketImpactPanel';
import { NewsDetailModal } from './NewsDetailModal';
import { AlertsManagerModal } from './AlertsManagerModal';
import { ForexInstrumentDetailModal } from './ForexInstrumentDetailModal';
import {
  Radar,
  BarChart2,
  Bell,
  RefreshCw,
  Search,
  Filter,
  Layers,
  ShieldAlert,
  Flame,
  Activity,
  DollarSign,
  TrendingUp,
  Cpu,
  Sparkles,
} from 'lucide-react';

interface MarketIntelligencePageProps {
  signals: Signal[];
  onRefreshAll: () => Promise<void>;
  onSelectStock?: (symbol: string) => void;
}

export const MarketIntelligencePage: React.FC<MarketIntelligencePageProps> = ({
  signals,
  onRefreshAll,
  onSelectStock,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'tickers' | 'impact'>('tickers');
  const [instrumentsSummary, setInstrumentsSummary] = useState<InstrumentSummary[]>([]);
  const [impactData, setImpactData] = useState<{
    distribution: Record<string, number>;
    dimension_averages: Record<string, number>;
  }>({
    distribution: { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 },
    dimension_averages: {},
  });
  const [alerts, setAlerts] = useState<MarketAlert[]>([]);
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [unreadAlertCount, setUnreadAlertCount] = useState<number>(0);
  const [stats, setStats] = useState<IntelligenceStats | null>(null);

  // Modals
  const [selectedSignalForModal, setSelectedSignalForModal] = useState<Signal | null>(null);
  const [selectedForexPairForModal, setSelectedForexPairForModal] = useState<string | null>(null);
  const [showAlertsModal, setShowAlertsModal] = useState<boolean>(false);
  const [isReanalyzing, setIsReanalyzing] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Load backend intelligence data
  const loadIntelligenceData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [tickerRes, impactRes, alertRes, statRes] = await Promise.all([
        api.getIntelligenceTickers(),
        api.getIntelligenceImpact({ limit: 80 }),
        api.getIntelligenceAlerts(),
        api.getIntelligenceStatistics(),
      ]);

      setInstrumentsSummary(tickerRes.instruments_summary || []);
      setImpactData({
        distribution: impactRes.distribution || {},
        dimension_averages: impactRes.dimension_averages || {},
      });
      setAlerts(alertRes.alerts || []);
      setRules(alertRes.rules || []);
      setUnreadAlertCount(alertRes.unread_count || 0);
      setStats(statRes);
    } catch (err) {
      console.error('Failed to load market intelligence data:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadIntelligenceData();
  }, [loadIntelligenceData]);

  // Handle re-analyzing an article
  const handleReanalyze = async (signalId: number) => {
    setIsReanalyzing(true);
    try {
      const updatedSignal = await api.reanalyzeArticleIntelligence(signalId);
      setSelectedSignalForModal(updatedSignal);
      await Promise.all([loadIntelligenceData(), onRefreshAll()]);
    } catch (err) {
      console.error('Failed to reanalyze signal:', err);
    } finally {
      setIsReanalyzing(false);
    }
  };

  // Handle adding an alert rule
  const handleAddRule = async (ruleData: {
    name: string;
    condition_type: string;
    target_value?: string | null;
    min_confidence: number;
    enabled: boolean;
  }) => {
    await api.createAlertRule(ruleData);
    await loadIntelligenceData();
  };

  // Handle marking an alert read
  const handleMarkAlertRead = async (alertId: number) => {
    await api.markAlertRead(alertId);
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a))
    );
    setUnreadAlertCount((c) => Math.max(0, c - 1));
  };

  return (
    <div className="space-y-6">
      {/* Top Intelligence Header Banner */}
      <div className="bg-[#091122] border border-[#16243e] rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/40 text-cyan-400 shrink-0">
              <Radar className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight">
                  Market Intelligence
                </h1>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold">
                  Decider 2B • Gemini
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                AI-powered forex news analysis and market impact monitoring.
              </p>
            </div>
          </div>

          {/* Quick Action Controls */}
          <div className="flex items-center gap-2.5 self-end lg:self-auto">
            <button
              onClick={() => setShowAlertsModal(true)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#0e1a32] hover:bg-[#142548] border border-[#1f345c] text-white text-xs font-mono font-bold transition-all shadow-sm active:scale-95"
            >
              <Bell className="w-3.5 h-3.5 text-cyan-400" />
              <span>Alerts</span>
              {unreadAlertCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full bg-rose-500 text-white text-[10px]">
                  {unreadAlertCount}
                </span>
              )}
            </button>

            <button
              onClick={() => loadIntelligenceData()}
              disabled={isLoading}
              className="p-2 rounded-xl bg-[#0e1a32] hover:bg-[#142548] border border-[#1f345c] text-slate-300 hover:text-white transition-all disabled:opacity-50"
              title="Refresh Intelligence Data"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* 4 Compact Metrics Cards: Total Detected Events, Affected Forex Pairs, High-Impact Events, Critical-Impact Events */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-1">
          <div className="bg-[#0c162e] border border-[#1a2d52] rounded-xl p-3.5 transition-all hover:border-cyan-500/30">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span className="font-mono text-[11px] uppercase tracking-wider">Total Detected Events</span>
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-2xl font-black font-mono text-white tracking-tight">
              {stats?.total_analyzed ?? signals.length}
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Analyzed news signals</div>
          </div>

          <div className="bg-[#0c162e] border border-[#1a2d52] rounded-xl p-3.5 transition-all hover:border-cyan-500/30">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span className="font-mono text-[11px] uppercase tracking-wider">Affected Forex Pairs</span>
              <Layers className="w-3.5 h-3.5 text-blue-400" />
            </div>
            <div className="text-2xl font-black font-mono text-white tracking-tight">
              {instrumentsSummary.length > 0 ? instrumentsSummary.length : 12}
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Tracked currency pairs</div>
          </div>

          <div className="bg-[#0c162e] border border-[#1a2d52] rounded-xl p-3.5 transition-all hover:border-amber-500/30">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span className="font-mono text-[11px] uppercase tracking-wider">High-Impact Events</span>
              <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-2xl font-black font-mono text-amber-400 tracking-tight">
              {stats?.high_count ?? signals.filter((s) => (s.impact_level || '').toUpperCase() === 'HIGH').length}
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Score range: 50–74</div>
          </div>

          <div className="bg-[#0c162e] border border-[#1a2d52] rounded-xl p-3.5 transition-all hover:border-rose-500/30">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span className="font-mono text-[11px] uppercase tracking-wider">Critical-Impact Events</span>
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            </div>
            <div className="text-2xl font-black font-mono text-rose-400 tracking-tight">
              {stats?.critical_count ?? signals.filter((s) => (s.impact_level || '').toUpperCase() === 'CRITICAL').length}
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Score range: 75–100</div>
          </div>
        </div>
      </div>

      {/* Main Tab Navigation: Clear Segmented Switch */}
      <div className="flex items-center gap-2 border-b border-[#16233b] pb-1">
        <button
          onClick={() => setActiveSubTab('tickers')}
          className={`px-4 py-2.5 rounded-t-xl text-xs sm:text-sm font-mono font-bold uppercase flex items-center gap-2 transition-all border-b-2 -mb-1 ${
            activeSubTab === 'tickers'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-500/10'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-[#0c152a]'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Smart Ticker Detection</span>
          <span className="ml-1 px-1.5 py-0.5 rounded text-[10px] bg-[#162540] text-slate-300 font-mono">
            {instrumentsSummary.length || 12}
          </span>
        </button>

        <button
          onClick={() => setActiveSubTab('impact')}
          className={`px-4 py-2.5 rounded-t-xl text-xs sm:text-sm font-mono font-bold uppercase flex items-center gap-2 transition-all border-b-2 -mb-1 ${
            activeSubTab === 'impact'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-500/10'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-[#0c152a]'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          <span>Market Impact Predictor</span>
          <span className="ml-1 px-1.5 py-0.5 rounded text-[10px] bg-[#162540] text-slate-300 font-mono">
            6 Dimensions
          </span>
        </button>
      </div>

      {/* Tab Panels */}
      {activeSubTab === 'tickers' ? (
        <SmartTickerDetectionPanel
          signals={signals}
          instrumentsSummary={instrumentsSummary}
          onSelectInstrument={(sym) => setSelectedForexPairForModal(sym)}
          onOpenSignalDetail={(sig) => setSelectedSignalForModal(sig)}
        />
      ) : (
        <MarketImpactPanel
          signals={signals}
          distribution={impactData.distribution}
          dimensionAverages={impactData.dimension_averages}
          onOpenSignalDetail={(sig) => setSelectedSignalForModal(sig)}
        />
      )}

      {/* Forex Instrument Detail Modal */}
      {selectedForexPairForModal && (
        <ForexInstrumentDetailModal
          symbol={selectedForexPairForModal}
          onClose={() => setSelectedForexPairForModal(null)}
          onSelectSignal={(sig) => setSelectedSignalForModal(sig)}
        />
      )}

      {/* News Detail Modal */}
      <NewsDetailModal
        signal={selectedSignalForModal}
        onClose={() => setSelectedSignalForModal(null)}
        onReanalyze={handleReanalyze}
        isReanalyzing={isReanalyzing}
      />

      {/* Alerts Dispatcher Modal */}
      {showAlertsModal && (
        <AlertsManagerModal
          rules={rules}
          alerts={alerts}
          unreadCount={unreadAlertCount}
          onClose={() => setShowAlertsModal(false)}
          onAddRule={handleAddRule}
          onMarkRead={handleMarkAlertRead}
        />
      )}
    </div>
  );
};

