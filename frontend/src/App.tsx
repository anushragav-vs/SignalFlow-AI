import React, { useState, useEffect, useCallback } from 'react';
import { api } from './lib/api-client';
import type { Signal, KPIs, AppHealth, AppConfig } from './types';
import { TopMarketRibbon } from './components/layout/TopMarketRibbon';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import type { NavTab } from './components/layout/Sidebar';
import { NewsStreamPage } from './features/news/NewsStreamPage';
import { OverviewPage } from './features/overview/OverviewPage';
import { AnalysisPage } from './features/analysis/AnalysisPage';
import { ReviewQueuePage } from './features/review-queue/ReviewQueuePage';
import { PerformancePage } from './features/performance/PerformancePage';
import { SettingsPage } from './features/settings/SettingsPage';
import { StockDetailModal } from './components/market/StockDetailModal';
import { Loader2, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('news');
  const [collapsedSidebar, setCollapsedSidebar] = useState<boolean>(false);

  // Core Data States
  const [signals, setSignals] = useState<Signal[]>([]);
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [health, setHealth] = useState<AppHealth | null>(null);
  const [appConfig, setAppConfig] = useState<AppConfig | null>(null);
  const [feeds, setFeeds] = useState<Record<string, string>>({});
  const [reviewItems, setReviewItems] = useState<Signal[]>([]);
  const [selectedStock, setSelectedStock] = useState<string | null>(null);

  // UI Status
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch all initial data
  const loadData = useCallback(async (silent: boolean = false) => {
    if (!silent) setIsLoading(true);
    else setIsRefreshing(true);
    setErrorMessage(null);

    try {
      const [healthData, kpiData, signalData, feedData, configData, reviewData] = await Promise.all([
        api.getHealth(),
        api.getKPIs(),
        api.getSignals({ limit: 80 }),
        api.getFeeds(),
        api.getConfig(),
        api.getReviewQueue(),
      ]);

      setHealth(healthData);
      setKpis(kpiData);
      setSignals(signalData);
      setFeeds(feedData);
      setAppConfig(configData);
      setReviewItems(reviewData);
      setIsBackendConnected(true);
    } catch (err: any) {
      console.error('Failed to load backend data:', err);
      setIsBackendConnected(false);
      setErrorMessage(
        'Unable to connect to SignalFlow backend API at http://localhost:8008. Please ensure the backend server is running.'
      );
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    // Subtle auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadData(true);
    }, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const refreshSignalsOnly = async () => {
    try {
      const [newSignals, newKpis, newReviews] = await Promise.all([
        api.getSignals({ limit: 80 }),
        api.getKPIs(),
        api.getReviewQueue(),
      ]);
      setSignals(newSignals);
      setKpis(newKpis);
      setReviewItems(newReviews);
    } catch (err) {
      console.error('Failed to refresh signals:', err);
    }
  };

  const refreshReviewQueueOnly = async () => {
    try {
      const [newReviews, newKpis, newSignals] = await Promise.all([
        api.getReviewQueue(),
        api.getKPIs(),
        api.getSignals({ limit: 80 }),
      ]);
      setReviewItems(newReviews);
      setKpis(newKpis);
      setSignals(newSignals);
    } catch (err) {
      console.error('Failed to refresh review queue:', err);
    }
  };

  const refreshFeedsOnly = async () => {
    try {
      const feedData = await api.getFeeds();
      setFeeds(feedData);
    } catch (err) {
      console.error('Failed to refresh feeds:', err);
    }
  };

  const refreshConfigOnly = async () => {
    try {
      const configData = await api.getConfig();
      setAppConfig(configData);
    } catch (err) {
      console.error('Failed to refresh config:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#060b15] text-slate-100 flex flex-col selection:bg-brand-teal/30 selection:text-white">
      {/* 1. Top Market Ribbon (AlphaPro Style with Live Tickers) */}
      <TopMarketRibbon onSelectStock={setSelectedStock} />

      {/* 2. Platform Header (VoiceWatch AI Style) */}
      <Header health={health || undefined} isBackendConnected={isBackendConnected} />

      {/* 3. Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          pendingReviewCount={reviewItems.length}
          collapsed={collapsedSidebar}
          onToggleCollapse={() => setCollapsedSidebar(!collapsedSidebar)}
        />

        {/* Center Content Workspace */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 bg-[#060b15]">
          {/* Global Refresh Bar */}
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-[#142138] text-xs">
            <div className="flex items-center gap-2 text-slate-400">
              <span>View:</span>
              <span className="font-bold text-white uppercase tracking-wider font-mono text-[11px]">
                {activeTab}
              </span>
              {isRefreshing && (
                <span className="flex items-center gap-1 text-cyan-400 text-[11px] animate-pulse">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Syncing with SQLite ledger...</span>
                </span>
              )}
            </div>

            <button
              onClick={() => loadData(true)}
              disabled={isRefreshing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0d162a] border border-[#1b2a47] hover:border-slate-500 text-slate-300 font-medium transition-colors disabled:opacity-50"
              title="Sync latest records from backend"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-brand-teal' : ''}`} />
              <span>Sync Ledger</span>
            </button>
          </div>

          {/* Error Banner if API offline */}
          {errorMessage && (
            <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between">
              <span>{errorMessage}</span>
              <button
                onClick={() => loadData()}
                className="underline font-bold hover:text-white ml-3 shrink-0"
              >
                Retry Connection
              </button>
            </div>
          )}

          {/* Loading Skeleton */}
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-24 text-slate-400">
              <Loader2 className="w-8 h-8 text-brand-teal animate-spin mb-3" />
              <p className="text-sm font-semibold text-white">Loading SignalFlow Intelligence...</p>
              <p className="text-xs text-slate-500 mt-1">Connecting to Strands Decider 2B & SQLite audit ledger</p>
            </div>
          ) : (
            <>
              {/* Tab 1: Financial News Stream */}
              {activeTab === 'news' && (
                <NewsStreamPage
                  signals={signals}
                  feeds={feeds}
                  onRefreshSignals={refreshSignalsOnly}
                  onSelectStock={setSelectedStock}
                />
              )}

              {/* Tab 2: Overview Dashboard */}
              {activeTab === 'overview' && (
                <OverviewPage
                  kpis={
                    kpis || {
                      total_received: signals.length,
                      unique_processed: signals.length,
                      bullish_count: signals.filter((s) => s.decider_sentiment === 'Bullish').length,
                      bearish_count: signals.filter((s) => s.decider_sentiment === 'Bearish').length,
                      neutral_count: signals.filter((s) => s.decider_sentiment === 'Neutral').length,
                      noise_count: signals.filter((s) => s.decider_sentiment === 'Noise').length,
                      escalated_for_review: reviewItems.length,
                      sent_to_gemini: signals.filter((s) => s.gemini_status === 'success').length,
                      successful_analyses: signals.filter((s) => s.gemini_status === 'success').length,
                      failed_analyses: 0,
                      cloud_calls_avoided_count: signals.filter((s) =>
                        ['BLOCK_NOISE', 'BLOCK_NEUTRAL'].includes(s.policy_action)
                      ).length,
                      cloud_calls_avoided_pct: 62.5,
                      total_cloud_spend_usd: signals.reduce((acc, s) => acc + (s.estimated_cost_usd || 0), 0),
                      avg_decider_latency_ms: 1787.0,
                      avg_cloud_latency_ms: 850.0,
                    }
                  }
                  signals={signals}
                />
              )}

              {/* Tab 3: Gemini Analysis Dossiers */}
              {activeTab === 'analysis' && (
                <AnalysisPage signals={signals} onSelectStock={setSelectedStock} />
              )}

              {/* Tab 4: Human Review Queue */}
              {activeTab === 'review' && (
                <ReviewQueuePage
                  pendingItems={reviewItems}
                  onRefreshReviewQueue={refreshReviewQueueOnly}
                />
              )}

              {/* Tab 5: Observability & Benchmarks */}
              {activeTab === 'performance' && <PerformancePage />}

              {/* Tab 6: Configuration & Settings */}
              {activeTab === 'settings' && (
                <SettingsPage
                  config={appConfig || undefined}
                  health={health || undefined}
                  kpis={kpis || undefined}
                  feeds={feeds}
                  onRefreshFeeds={refreshFeedsOnly}
                  onRefreshConfig={refreshConfigOnly}
                />
              )}
            </>
          )}
        </main>
      </div>

      {/* Persistent Regulatory Disclaimer Banner at Bottom */}
      <footer className="bg-[#050912] border-t border-[#142138] py-2 px-6 text-center text-[11px] text-slate-500">
        Research and educational purposes only. This is not financial advice or an automated trading system.
        SignalFlow AI does not execute trades or provide guaranteed returns.
      </footer>

      {/* Live Market Ticker & Deep Research Modal */}
      {selectedStock && (
        <StockDetailModal
          symbol={selectedStock}
          onClose={() => setSelectedStock(null)}
          onFilterToStock={(sym) => {
            setActiveTab('news');
            setSelectedStock(null);
          }}
          onSelectAnotherStock={(sym) => setSelectedStock(sym)}
        />
      )}
    </div>
  );
};

export default App;
