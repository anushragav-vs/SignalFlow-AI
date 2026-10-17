export type MarketSentiment = 'Bullish' | 'Bearish' | 'Neutral' | 'Noise';

export type PolicyAction = 'APPROVE' | 'BLOCK_NOISE' | 'BLOCK_NEUTRAL' | 'REVIEW_QUEUE';

export type ReviewStatus = 'NONE' | 'PENDING' | 'CONFIRMED' | 'RECLASSIFIED' | 'DISMISSED';

export interface Signal {
  id: number;
  timestamp: string;
  headline: string;
  canonical_url: string;
  publisher: string;
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
