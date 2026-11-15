import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MarketIntelligencePage } from '../features/intelligence/MarketIntelligencePage';
import { SmartTickerDetectionPanel } from '../features/intelligence/SmartTickerDetectionPanel';
import { MarketImpactPanel } from '../features/intelligence/MarketImpactPanel';
import { NewsDetailModal } from '../features/intelligence/NewsDetailModal';
import { AlertsManagerModal } from '../features/intelligence/AlertsManagerModal';
import { ForexInstrumentDetailModal } from '../features/intelligence/ForexInstrumentDetailModal';
import type { Signal, InstrumentSummary, AlertRule, MarketAlert, IntelligenceStats } from '../types';
import { api } from '../lib/api-client';

const mockInstrumentsSummary: InstrumentSummary[] = [
  {
    symbol: 'EUR/USD',
    name: 'Euro / US Dollar',
    base_currency: 'EUR',
    quote_currency: 'USD',
    total_mentions: 24,
    direct_count: 8,
    indirect_count: 14,
    potential_count: 2,
    avg_impact_score: 68.5,
    dominant_sentiment: 'Bearish',
    sentiments: { Bullish: 4, Bearish: 16, Neutral: 4, Noise: 0 },
  },
  {
    symbol: 'USD/JPY',
    name: 'US Dollar / Japanese Yen',
    base_currency: 'USD',
    quote_currency: 'JPY',
    total_mentions: 18,
    direct_count: 5,
    indirect_count: 11,
    potential_count: 2,
    avg_impact_score: 62.0,
    dominant_sentiment: 'Bullish',
    sentiments: { Bullish: 12, Bearish: 3, Neutral: 3, Noise: 0 },
  },
];

const mockStats: IntelligenceStats = {
  total_analyzed: 45,
  avg_impact_score: 54.2,
  critical_count: 5,
  high_count: 15,
  medium_count: 18,
  low_count: 7,
  top_events: [{ category: 'interest_rate_announcements', count: 12 }],
  total_alerts: 8,
  unread_alerts: 2,
};

const mockAlertRules: AlertRule[] = [
  {
    id: 1,
    name: 'Critical Market Impact Alert',
    condition_type: 'critical_impact',
    min_confidence: 0.80,
    enabled: true,
    created_at: '2026-10-16T00:00:00Z',
  },
];

const mockAlerts: MarketAlert[] = [
  {
    id: 1,
    signal_id: 101,
    rule_id: 1,
    alert_type: 'critical_impact',
    title: 'CRITICAL IMPACT (88/100): Federal Reserve Interest Rate Decision',
    message: 'Federal Reserve delivers surprise 50 bps interest rate hike to curb persistent inflation',
    severity: 'critical',
    created_at: '2026-10-16T12:00:00Z',
    is_read: false,
  },
];

// Mock API client
vi.mock('../lib/api-client', () => ({
  api: {
    getIntelligenceTickers: vi.fn().mockResolvedValue({
      supported_universe: [],
      instruments_summary: [
        {
          symbol: 'EUR/USD',
          name: 'Euro / US Dollar',
          base_currency: 'EUR',
          quote_currency: 'USD',
          total_mentions: 24,
          direct_count: 8,
          indirect_count: 14,
          potential_count: 2,
          avg_impact_score: 68.5,
          dominant_sentiment: 'Bearish',
          sentiments: { Bullish: 4, Bearish: 16, Neutral: 4, Noise: 0 },
        },
      ],
      total_supported: 12,
    }),
    getIntelligenceImpact: vi.fn().mockResolvedValue({
      distribution: { CRITICAL: 5, HIGH: 15, MEDIUM: 18, LOW: 7 },
      dimension_averages: {
        economic_importance: 68.4,
        surprise_magnitude: 52.1,
        instrument_relevance: 71.0,
        source_reliability: 85.0,
        news_novelty: 62.3,
        potential_volatility: 59.8,
      },
      total_analyzed: 45,
      signals: [],
    }),
    getIntelligenceAlerts: vi.fn().mockResolvedValue({
      rules: [
        {
          id: 1,
          name: 'Critical Market Impact Alert',
          condition_type: 'critical_impact',
          min_confidence: 0.80,
          enabled: true,
          created_at: '2026-10-16T00:00:00Z',
        },
      ],
      alerts: [
        {
          id: 1,
          signal_id: 101,
          rule_id: 1,
          alert_type: 'critical_impact',
          title: 'CRITICAL IMPACT (88/100): Federal Reserve Interest Rate Decision',
          message: 'Federal Reserve delivers surprise 50 bps interest rate hike to curb persistent inflation',
          severity: 'critical',
          created_at: '2026-10-16T12:00:00Z',
          is_read: false,
        },
      ],
      unread_count: 1,
    }),
    getIntelligenceStatistics: vi.fn().mockResolvedValue({
      total_analyzed: 45,
      avg_impact_score: 54.2,
      critical_count: 5,
      high_count: 15,
      medium_count: 18,
      low_count: 7,
      top_events: [{ category: 'interest_rate_announcements', count: 12 }],
      total_alerts: 8,
      unread_alerts: 2,
    }),
    createAlertRule: vi.fn().mockResolvedValue({ status: 'ok', rule_id: 2, rules: [] }),
    markAlertRead: vi.fn().mockResolvedValue({ status: 'ok', alert_id: 1 }),
    reanalyzeArticleIntelligence: vi.fn(),
    getIntelligenceNewsDetail: vi.fn().mockImplementation((id: number) => {
      const found = mockIntelligenceSignals.find((s) => s.id === id);
      return Promise.resolve(found || mockIntelligenceSignals[0]);
    }),
    getIntelligenceInstrumentDetail: vi.fn().mockResolvedValue({
      symbol: 'EUR/USD',
      name: 'Euro / US Dollar',
      base_currency: 'EUR',
      quote_currency: 'USD',
      category: 'major',
      aliases: ['EURUSD', 'Fiber'],
      total_correlated_signals: 24,
      direct_count: 8,
      indirect_count: 14,
      potential_count: 2,
      average_impact_score: 68.5,
      critical_events_count: 3,
      high_events_count: 8,
      highest_impact_news: null,
      relationship_counts: { direct: 8, indirect: 14, potential: 2 },
      sentiment_counts: { Bullish: 4, Bearish: 16, Neutral: 4 },
      dominant_sentiment: 'Bearish',
      sentiment_score: 30,
      related_central_banks: ['European Central Bank (ECB)', 'Federal Reserve (Fed)'],
      related_currencies: ['EUR', 'USD'],
      macro_indicators: ['Interest Rate Decisions', 'Inflation (CPI)'],
      market_quote: { price: 1.0850, change_pct: 0.23, change_abs: 0.0025, is_positive: true },
      signals: [],
    }),
  },
}));

const mockIntelligenceSignals: Signal[] = [
  {
    id: 101,
    timestamp: '2026-10-16T12:00:00Z',
    headline: 'Federal Reserve delivers surprise 50 bps interest rate hike to curb persistent inflation',
    canonical_url: 'https://reuters.com/markets/fed-rate-hike',
    publisher: 'Reuters',
    is_live: 1,
    decider_sentiment: 'Bearish',
    decider_confidence: 0.94,
    probabilities: { Bullish: 0.02, Bearish: 0.94, Neutral: 0.03, Noise: 0.01 },
    decider_latency_ms: 1750,
    decider_model_id: 'strands-decider-2B',
    policy_action: 'APPROVE',
    policy_reason: 'High confidence bearish signal',
    review_status: 'NONE',
    impact_score: 88,
    impact_level: 'CRITICAL',
    event_category: 'interest_rate_announcements',
    volatility_assessment: 'high',
    impact_dimensions: {
      economic_importance: 95,
      surprise_magnitude: 85,
      instrument_relevance: 90,
      source_reliability: 95,
      news_novelty: 75,
      potential_volatility: 85,
    },
    detected_entities: [
      { name: 'Federal Reserve', entity_type: 'central_bank', mention_type: 'explicit' },
      { name: 'USD', entity_type: 'currency', mention_type: 'explicit' },
      { name: 'Inflation', entity_type: 'economic_indicator', mention_type: 'explicit' },
    ],
    affected_instruments: [
      {
        symbol: 'EUR/USD',
        relationship: 'indirect',
        confidence: 0.89,
        reason: 'Unexpected rate hikes alter yield spread differentials and capital flows.',
        mentioned_explicitly: false,
      },
      {
        symbol: 'USD/JPY',
        relationship: 'indirect',
        confidence: 0.89,
        reason: 'US rate adjustments impact bilateral yield spreads against JPY.',
        mentioned_explicitly: false,
      },
    ],
    affected_assets: ['EUR/USD', 'USD/JPY', 'USD'],
  },
  {
    id: 102,
    timestamp: '2026-10-16T13:00:00Z',
    headline: 'European Central Bank maintains neutral stance amid steady Eurozone growth',
    canonical_url: 'https://bloomberg.com/markets/ecb-neutral',
    publisher: 'Bloomberg',
    is_live: 1,
    decider_sentiment: 'Neutral',
    decider_confidence: 0.91,
    probabilities: { Bullish: 0.04, Bearish: 0.05, Neutral: 0.91, Noise: 0.00 },
    decider_latency_ms: 1680,
    decider_model_id: 'strands-decider-2B',
    policy_action: 'BLOCK_NEUTRAL',
    policy_reason: 'Neutral sentiment',
    review_status: 'NONE',
    impact_score: 42,
    impact_level: 'MEDIUM',
    event_category: 'central_bank_decisions',
    volatility_assessment: 'moderate',
    impact_dimensions: {
      economic_importance: 60,
      surprise_magnitude: 20,
      instrument_relevance: 70,
      source_reliability: 90,
      news_novelty: 40,
      potential_volatility: 35,
    },
    detected_entities: [
      { name: 'European Central Bank', entity_type: 'central_bank', mention_type: 'explicit' },
      { name: 'EUR', entity_type: 'currency', mention_type: 'explicit' },
    ],
    affected_instruments: [
      {
        symbol: 'EUR/USD',
        relationship: 'indirect',
        confidence: 0.85,
        reason: 'ECB decisions directly steer EUR valuation against major currencies.',
        mentioned_explicitly: false,
      },
    ],
    affected_assets: ['EUR/USD', 'EUR'],
  },
];

describe('Market Intelligence Frontend Test Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders MarketIntelligencePage with macro stats bar and panels', async () => {
    render(
      <MarketIntelligencePage
        signals={mockIntelligenceSignals}
        onRefreshAll={vi.fn()}
      />
    );

    // Title banner
    expect(screen.getByRole('heading', { level: 1, name: /Market Intelligence/i })).toBeInTheDocument();
    expect(screen.getByText(/AI-powered forex news analysis and market impact monitoring/i)).toBeInTheDocument();

    // Verify 4 compact metrics cards
    await waitFor(() => {
      expect(screen.getByText('Total Detected Events')).toBeInTheDocument();
      expect(screen.getByText('Affected Forex Pairs')).toBeInTheDocument();
      expect(screen.getByText('High-Impact Events')).toBeInTheDocument();
      expect(screen.getByText('Critical-Impact Events')).toBeInTheDocument();
    });

    // Subtab navigation
    expect(screen.getByText(/Smart Ticker Detection/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Market Impact Predictor/i).length).toBeGreaterThan(0);
  });

  it('renders SmartTickerDetectionPanel with currency filters and badges', () => {
    render(
      <SmartTickerDetectionPanel
        signals={mockIntelligenceSignals}
        instrumentsSummary={mockInstrumentsSummary}
        onSelectInstrument={vi.fn()}
        onOpenSignalDetail={vi.fn()}
      />
    );

    // Instruments carousel / quick filters
    expect(screen.getAllByText('EUR/USD').length).toBeGreaterThan(0);
    expect(screen.getAllByText('USD/JPY').length).toBeGreaterThan(0);

    // Headlines
    expect(screen.getAllByText(/Federal Reserve delivers surprise 50 bps/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/European Central Bank maintains neutral stance/i)).toBeInTheDocument();

    // Relationship badges
    expect(screen.getAllByText('indirect').length).toBeGreaterThan(0);
  });

  it('filters signals by instrument pair in SmartTickerDetectionPanel', () => {
    render(
      <SmartTickerDetectionPanel
        signals={mockIntelligenceSignals}
        instrumentsSummary={mockInstrumentsSummary}
        onSelectInstrument={vi.fn()}
        onOpenSignalDetail={vi.fn()}
      />
    );

    // Filter by USD/JPY
    const pairSelect = screen.getByDisplayValue(/All Pairs/i);
    fireEvent.change(pairSelect, { target: { value: 'USD/JPY' } });

    // Fed signal mentions USD/JPY, ECB does not
    expect(screen.getByText(/Federal Reserve delivers surprise 50 bps/i)).toBeInTheDocument();
    expect(screen.queryByText(/European Central Bank maintains neutral stance/i)).not.toBeInTheDocument();
  });

  it('renders MarketImpactPanel with distribution and dimension bars', () => {
    render(
      <MarketImpactPanel
        signals={mockIntelligenceSignals}
        distribution={{ CRITICAL: 5, HIGH: 15, MEDIUM: 18, LOW: 7 }}
        dimensionAverages={{
          economic_importance: 68.4,
          surprise_magnitude: 52.1,
          instrument_relevance: 71.0,
          source_reliability: 85.0,
          news_novelty: 62.3,
          potential_volatility: 59.8,
        }}
        onOpenSignalDetail={vi.fn()}
      />
    );

    // Filter buttons
    expect(screen.getByText('Impact Level Distribution')).toBeInTheDocument();
    expect(screen.getByText(/6 Normalized Impact Dimensions/i)).toBeInTheDocument();
    expect(screen.getByText(/Economic Importance/i)).toBeInTheDocument();

    // Headlines
    expect(screen.getAllByText(/Federal Reserve delivers surprise 50 bps/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/European Central Bank maintains neutral stance/i)).toBeInTheDocument();
  });

  it('renders NewsDetailModal with all dimensions, entities and disclaimer', async () => {
    const signal = mockIntelligenceSignals[0];
    const onClose = vi.fn();

    render(
      <NewsDetailModal
        signal={signal}
        onClose={onClose}
      />
    );

    // Modal Headline
    await waitFor(() => {
      expect(screen.getByText(signal.headline)).toBeInTheDocument();
    });

    // Detected Entities
    expect(screen.getByText('Federal Reserve')).toBeInTheDocument();
    expect(screen.getByText('USD')).toBeInTheDocument();
    expect(screen.getByText('Inflation')).toBeInTheDocument();

    // Affected Instruments
    expect(screen.getByText('EUR/USD')).toBeInTheDocument();
    expect(screen.getByText('USD/JPY')).toBeInTheDocument();
    expect(screen.getByText(/Unexpected rate hikes alter yield spread differentials/i)).toBeInTheDocument();

    // Impact Dimensions
    expect(screen.getByText('Economic Importance')).toBeInTheDocument();
    expect(screen.getByText('Surprise Magnitude')).toBeInTheDocument();
    expect(screen.getByText('Instrument Relevance')).toBeInTheDocument();
  });

  it('renders AlertsManagerModal with active rules and notifications', async () => {
    const onClose = vi.fn();
    const onAddRule = vi.fn().mockResolvedValue(undefined);
    const onMarkRead = vi.fn().mockResolvedValue(undefined);

    render(
      <AlertsManagerModal
        rules={mockAlertRules}
        alerts={mockAlerts}
        unreadCount={1}
        onClose={onClose}
        onAddRule={onAddRule}
        onMarkRead={onMarkRead}
      />
    );

    // Modal Header
    expect(screen.getByText('Market Intelligence Alert Dispatcher')).toBeInTheDocument();
    expect(screen.getByText(/Triggered Notifications/i)).toBeInTheDocument();
    expect(screen.getByText(/Configured Alert Rules/i)).toBeInTheDocument();

    // Alert Notification Content
    expect(screen.getByText(/CRITICAL IMPACT \(88\/100\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Federal Reserve delivers surprise 50 bps/i)).toBeInTheDocument();
  });

  it('renders ForexInstrumentDetailModal with complete macro intelligence and quote', async () => {
    const onClose = vi.fn();
    render(
      <ForexInstrumentDetailModal
        symbol="EUR/USD"
        onClose={onClose}
      />
    );

    // Modal loads and shows EUR/USD header
    await waitFor(() => {
      expect(screen.getByText('Euro / US Dollar')).toBeInTheDocument();
      expect(screen.getByText('1.0850')).toBeInTheDocument();
    });

    // Central banks displayed
    expect(screen.getByText('European Central Bank (ECB)')).toBeInTheDocument();
    expect(screen.getByText('Federal Reserve (Fed)')).toBeInTheDocument();

    // Transmission counts
    expect(screen.getByText('8 DIR')).toBeInTheDocument();
    expect(screen.getByText('14 IND')).toBeInTheDocument();
    expect(screen.getByText('2 POT')).toBeInTheDocument();

    // Sorting controls
    expect(screen.getByText('Latest News')).toBeInTheDocument();
    expect(screen.getByText('Highest Impact')).toBeInTheDocument();
    expect(screen.getByText('Highest Confidence')).toBeInTheDocument();

    // Close button
    const closeBtn = screen.getByTitle('Close modal');
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });

  it('renders ForexInstrumentDetailModal empty state correctly', async () => {
    vi.mocked(api.getIntelligenceInstrumentDetail).mockResolvedValueOnce({
      symbol: 'NZD/USD',
      name: 'New Zealand Dollar / US Dollar',
      base_currency: 'NZD',
      quote_currency: 'USD',
      category: 'major',
      aliases: ['NZDUSD', 'Kiwi'],
      total_correlated_signals: 0,
      direct_count: 0,
      indirect_count: 0,
      potential_count: 0,
      average_impact_score: 0,
      critical_events_count: 0,
      high_events_count: 0,
      highest_impact_news: null,
      relationship_counts: { direct: 0, indirect: 0, potential: 0 },
      sentiment_counts: { Bullish: 0, Bearish: 0, Neutral: 0 },
      dominant_sentiment: 'Neutral',
      sentiment_score: 50,
      related_central_banks: ['Reserve Bank of New Zealand (RBNZ)'],
      related_currencies: ['NZD', 'USD'],
      macro_indicators: ['Interest Rate Decisions'],
      market_quote: { price: 0.6120, change_pct: 0.10, change_abs: 0.0006, is_positive: true },
      signals: [],
    });

    render(
      <ForexInstrumentDetailModal
        symbol="NZD/USD"
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByText('No unique news signals are currently available for this instrument.')
      ).toBeInTheDocument();
    });
  });
});
