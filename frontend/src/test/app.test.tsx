import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { TopMarketRibbon } from '../components/layout/TopMarketRibbon';
import { Header } from '../components/layout/Header';
import { Sidebar } from '../components/layout/Sidebar';
import { NewsStreamPage } from '../features/news/NewsStreamPage';
import { PerformancePage } from '../features/performance/PerformancePage';
import { ReviewQueuePage } from '../features/review-queue/ReviewQueuePage';
import type { Signal, KPIs, AppHealth } from '../types';

const mockSignals: Signal[] = [
  {
    id: 1,
    timestamp: '2026-10-16T12:00:00Z',
    headline: 'Nvidia reports record earnings as AI data center demand surges',
    canonical_url: 'https://example.com/nvda',
    publisher: 'Yahoo Finance',
    is_live: 1,
    decider_sentiment: 'Bullish',
    decider_confidence: 0.95,
    probabilities: { Bullish: 0.95, Bearish: 0.02, Neutral: 0.02, Noise: 0.01 },
    decider_latency_ms: 1800,
    decider_model_id: 'strands-decider-2B',
    policy_action: 'APPROVE',
    policy_reason: 'High confidence bullish signal',
    review_status: 'NONE',
    affected_assets: ['NVDA', 'Semiconductors'],
    uncertainties: ['Supply chain capacity'],
    reported_facts: ['Record quarterly net income up 94%'],
    analytical_hypotheses: ['Continued gross margin expansion in Q4'],
    cloud_latency_ms: 850,
    estimated_cost_usd: 0.000085,
    event_summary: 'Nvidia achieved record data center revenue driven by Blackwell architecture demand.',
    gemini_status: 'success',
  },
  {
    id: 2,
    timestamp: '2026-10-16T12:05:00Z',
    headline: 'Celebrity spotted wearing luxury watch in Paris',
    canonical_url: 'https://example.com/lifestyle',
    publisher: 'Entertainment Weekly',
    is_live: 1,
    decider_sentiment: 'Noise',
    decider_confidence: 0.92,
    probabilities: { Bullish: 0.01, Bearish: 0.01, Neutral: 0.06, Noise: 0.92 },
    decider_latency_ms: 1650,
    decider_model_id: 'strands-decider-2B',
    policy_action: 'BLOCK_NOISE',
    policy_reason: 'Non-actionable noise',
    review_status: 'NONE',
    affected_assets: [],
    uncertainties: [],
    reported_facts: [],
    analytical_hypotheses: [],
    cloud_latency_ms: 0,
    estimated_cost_usd: 0,
  },
  {
    id: 3,
    timestamp: '2026-10-16T12:10:00Z',
    headline: 'Unconfirmed rumor of regional bank merger talks',
    canonical_url: 'https://example.com/rumor',
    publisher: 'Market Rumors',
    is_live: 1,
    decider_sentiment: 'Bullish',
    decider_confidence: 0.62,
    probabilities: { Bullish: 0.62, Bearish: 0.18, Neutral: 0.15, Noise: 0.05 },
    decider_latency_ms: 1720,
    decider_model_id: 'strands-decider-2B',
    policy_action: 'REVIEW_QUEUE',
    policy_reason: 'Confidence below 0.80 safety threshold',
    review_status: 'PENDING',
    affected_assets: [],
    uncertainties: [],
    reported_facts: [],
    analytical_hypotheses: [],
    cloud_latency_ms: 0,
    estimated_cost_usd: 0,
  },
];

describe('SignalFlow AI - Frontend Component Test Suite', () => {
  it('renders the TopMarketRibbon with macro indexes', () => {
    render(<TopMarketRibbon />);
    expect(screen.getByText('NASDAQ')).toBeInTheDocument();
    expect(screen.getByText('S&P 500')).toBeInTheDocument();
    expect(screen.getByText('DOW JONES')).toBeInTheDocument();
    expect(screen.getByText('NVDA')).toBeInTheDocument();
  });

  it('renders Header with integration badges and active status', () => {
    const mockHealth: AppHealth = {
      status: 'healthy',
      system_one: { model: 'strands-decider-2B', server_url: 'http://localhost:8000', status: 'active' },
      system_two: { provider: 'Google AI Studio', model: 'gemini-3.5-flash-lite', configured: true, masked_key: 'AIzaSy...4xQ' },
      database: { path: 'signalflow.db', status: 'connected' },
      disclaimer: 'Research and educational purposes only.',
      timestamp: '2026-10-16T12:00:00Z',
    };

    render(<Header health={mockHealth} isBackendConnected={true} />);
    expect(screen.getByText('SignalFlow AI')).toBeInTheDocument();
    expect(screen.getByText('Strands Decider 2B')).toBeInTheDocument();
    expect(screen.getByText('gemini-3.5-flash-lite')).toBeInTheDocument();
    expect(screen.getByText('API Live')).toBeInTheDocument();
  });

  it('renders Sidebar with active tab and pending review count badge', () => {
    const onSelectTab = vi.fn();
    render(
      <Sidebar
        activeTab="news"
        onSelectTab={onSelectTab}
        pendingReviewCount={3}
        collapsed={false}
        onToggleCollapse={vi.fn()}
      />
    );

    expect(screen.getByText('News Stream')).toBeInTheDocument();
    expect(screen.getByText('Review Queue')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument(); // Badge count
  });

  it('filters news headlines by search query in NewsStreamPage', () => {
    render(
      <NewsStreamPage
        signals={mockSignals}
        feeds={{ 'Yahoo Finance Top Stories': 'https://example.com/rss' }}
        onRefreshSignals={vi.fn()}
      />
    );

    // Initial state shows both headlines
    expect(screen.getByText(/Nvidia reports record earnings/i)).toBeInTheDocument();
    expect(screen.getByText(/Celebrity spotted/i)).toBeInTheDocument();

    // Type in search query
    const searchInput = screen.getByPlaceholderText(/Search Ticker or Headline/i);
    fireEvent.change(searchInput, { target: { value: 'Nvidia' } });

    // Only Nvidia should remain visible
    expect(screen.getByText(/Nvidia reports record earnings/i)).toBeInTheDocument();
    expect(screen.queryByText(/Celebrity spotted/i)).not.toBeInTheDocument();
  });

  it('renders PerformancePage with recommended Strands Decider 2B card', () => {
    render(<PerformancePage />);
    expect(screen.getAllByText('Strands Decider 2B').length).toBeGreaterThan(0);
    expect(screen.getByText('★ Recommended Gatekeeper')).toBeInTheDocument();
    expect(screen.getByText('Google Gemini 3.5 Flash Lite')).toBeInTheDocument();
    expect(screen.getByText('Baseline (100% Cloud Invocations)')).toBeInTheDocument();
  });

  it('renders ReviewQueuePage with pending item and triage buttons', () => {
    const pendingItem = mockSignals.filter((s) => s.review_status === 'PENDING');
    render(<ReviewQueuePage pendingItems={pendingItem} onRefreshReviewQueue={vi.fn()} />);

    expect(screen.getByText(/Unconfirmed rumor of regional bank merger talks/i)).toBeInTheDocument();
    expect(screen.getByText('Approve & Send to Gemini')).toBeInTheDocument();
    expect(screen.getByText('Dismiss as Noise')).toBeInTheDocument();
    expect(screen.getByText('Save Reclassification')).toBeInTheDocument();
  });
});
