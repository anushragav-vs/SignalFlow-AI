export type MarketSentiment = 'Bullish' | 'Bearish' | 'Neutral' | 'Noise';

export type PolicyAction = 'APPROVE' | 'BLOCK_NOISE' | 'BLOCK_NEUTRAL' | 'REVIEW_QUEUE';

export type ReviewStatus = 'NONE' | 'PENDING' | 'CONFIRMED' | 'RECLASSIFIED' | 'DISMISSED';

export interface Signal {
  id: number;
  timestamp: string;
  headline: string;
  canonical_url: string;
  publisher: string;
  article_body?: string;
  is_live: number | boolean;
  decider_sentiment: MarketSentiment;
  decider_confidence: number;
  probabilities: Record<string, number>;
  decider_latency_ms: number;
  decider_model_id: string;
  policy_action: PolicyAction;
  policy_reason: string;
  review_status: ReviewStatus;
  reviewer_action?: string;
  reviewer_notes?: string;
  corrected_label?: string;
  reviewed_at?: string;
  gemini_model_id?: string;
  gemini_status?: string;
  raw_summary?: string;
  event_summary?: string;
  transmission_mechanism?: string;
  affected_assets: string[];
  directional_implications?: string;
  uncertainties: string[];
  reported_facts: string[];
  analytical_hypotheses: string[];
  catalyst_watchpoints?: string[];
  market_impact_horizon?: string;
  institutional_risk_level?: string;
  peer_impact?: string[];
  cloud_latency_ms: number;
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  estimated_cost_usd: number;

  // Market Intelligence & Smart Ticker Detection
  detected_entities?: DetectedEntity[];
  affected_instruments?: AffectedInstrument[];
  currencies?: string[];
  economic_events?: string[];
  impact_score?: number;
  impact_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  impact_dimensions?: ImpactDimensions;
  event_category?: string;
  volatility_assessment?: 'low' | 'moderate' | 'elevated' | 'extreme';
  impact_explanation?: string;
  impact_methodology?: string;
  impact_limitations?: string[];
  historical_context?: HistoricalContext;
}

export interface DetectedEntity {
  name: string;
  entity_type: 'forex_pair' | 'currency' | 'central_bank' | 'economic_indicator' | 'commodity' | string;
  mention_type: 'explicit' | 'implicit' | 'contextual' | string;
  raw_match?: string;
  confidence?: number;
}

export interface AffectedInstrument {
  symbol: string;
  relationship: 'direct' | 'indirect' | 'potential';
  confidence: number;
  reason: string;
  mentioned_explicitly: boolean;
  potential_direction?: 'bullish' | 'bearish' | 'mixed' | 'uncertain';
}

export interface ImpactDimensions {
  economic_importance: number;
  surprise_magnitude: number;
  instrument_relevance: number;
  source_reliability: number;
  news_novelty: number;
  potential_volatility: number;
}

export interface HistoricalReactionWindow {
  status: string;
  absolute_return_pct?: number | null;
  signed_return_pct?: number | null;
  realized_volatility_pct?: number | null;
  max_favorable_move_pct?: number | null;
  max_adverse_move_pct?: number | null;
}

export interface HistoricalContext {
  has_historical_data: boolean;
  data_status: string;
  methodology: string;
  windows: Record<string, HistoricalReactionWindow>;
  disclaimer: string;
}

export interface MarketAlert {
  id: number;
  signal_id: number;
  rule_id?: number;
  alert_type: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'critical';
  created_at: string;
  is_read: boolean;
}

export interface AlertRule {
  id: number;
  name: string;
  condition_type: string;
  target_value?: string | null;
  min_confidence: number;
  enabled: boolean;
  created_at: string;
}

export interface SupportedInstrument {
  symbol: string;
  name: string;
  base_currency: string;
  quote_currency: string;
  category: string;
  aliases: string[];
}

export interface InstrumentSummary {
  symbol: string;
  name: string;
  base_currency: string;
  quote_currency: string;
  total_mentions: number;
  direct_count: number;
  indirect_count: number;
  potential_count: number;
  avg_impact_score: number;
  dominant_sentiment: string;
  sentiments: Record<string, number>;
}

export interface ForexInstrumentDetail {
  symbol: string;
  name: string;
  base_currency: string;
  quote_currency: string;
  category: string;
  aliases: string[];
  total_correlated_signals: number;
  direct_count: number;
  indirect_count: number;
  potential_count: number;
  average_impact_score: number;
  critical_events_count: number;
  high_events_count: number;
  highest_impact_news?: Signal | null;
  relationship_counts: Record<string, number>;
  sentiment_counts: Record<string, number>;
  dominant_sentiment: string;
  sentiment_score: number;
  related_central_banks: string[];
  related_currencies: string[];
  macro_indicators: string[];
  historical_reaction?: HistoricalContext | null;
  market_quote?: any;
  signals: Signal[];
}

export interface IntelligenceStats {
  total_analyzed: number;
  avg_impact_score: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  top_events: Array<{ category: string; count: number }>;
  total_alerts: number;
  unread_alerts: number;
}

export interface MarketTicker {
  symbol: string;
  display_symbol: string;
  label: string;
  category: string;
  name: string;
  price: number;
  prev_close: number;
  change_abs: number;
  change_pct: number;
  is_positive: boolean;
  day_high?: number;
  day_low?: number;
  year_high?: number;
  year_low?: number;
  volume?: number;
  currency: string;
  exchange: string;
  sparkline: number[];
  updated_at: string;
  is_live: boolean;
}

export interface StockDetail extends MarketTicker {
  related_signals: Signal[];
  related_signals_count: number;
  sentiment_stats: {
    bullish: number;
    bearish: number;
    neutral: number;
    sentiment_score: number;
    sentiment_label: 'Bullish' | 'Bearish' | 'Neutral';
  };
}

export interface KPIs {
  total_received: number;
  unique_processed: number;
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
  noise_count: number;
  escalated_for_review: number;
  sent_to_gemini: number;
  successful_analyses: number;
  failed_analyses: number;
  cloud_calls_avoided_count: number;
  cloud_calls_avoided_pct: number;
  total_cloud_spend_usd: number;
  avg_decider_latency_ms: number;
  avg_cloud_latency_ms: number;
}

export interface AppHealth {
  status: string;
  system_one: {
    model: string;
    server_url: string;
    status: string;
  };
  system_two: {
    provider: string;
    model: string;
    configured: boolean;
    masked_key: string;
  };
  database: {
    path: string;
    status: string;
  };
  disclaimer: string;
  timestamp: string;
}

export interface LatencyStats {
  mean: number;
  median: number;
  p95: number;
}

export interface BenchmarkSummary {
  dataset_size: number;
  baseline_cloud_calls: number;
  proposed_cloud_calls: number;
  cloud_calls_avoided_pct: number;
  baseline_estimated_spend_usd: number;
  proposed_estimated_spend_usd: number;
  cost_savings_pct: number;
  decider_latency_stats: LatencyStats;
  cloud_latency_stats: LatencyStats;
}

export interface AppConfig {
  min_confidence_threshold: number;
  gemini_model_id: string;
  decider_checkpoint: string;
  decider_server_url: string;
  sqlite_db_path: string;
  masked_api_key: string;
  disclaimer: string;
  tags?: string[];
}
