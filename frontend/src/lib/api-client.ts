import type { KPIs, Signal, AppHealth, BenchmarkSummary, AppConfig, MarketTicker, StockDetail } from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  getHealth: () => fetchJson<AppHealth>(`${API_BASE}/health`),

  getKPIs: () => fetchJson<KPIs>(`${API_BASE}/kpis`),

  getSignals: (params?: {
    limit?: number;
    search?: string;
    sentiment?: string;
    policy_action?: string;
    review_status?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.search) query.set('search', params.search);
    if (params?.sentiment) query.set('sentiment', params.sentiment);
    if (params?.policy_action) query.set('policy_action', params.policy_action);
    if (params?.review_status) query.set('review_status', params.review_status);
    return fetchJson<Signal[]>(`${API_BASE}/signals?${query.toString()}`);
  },

  getSignal: (id: number) => fetchJson<Signal>(`${API_BASE}/signals/${id}`),

  fetchFeed: (feedName: string, maxItems: number = 6) =>
    fetchJson<{ processed_count: number; results: any[]; message: string }>(`${API_BASE}/news/fetch`, {
      method: 'POST',
      body: JSON.stringify({ feed_name: feedName, max_items: maxItems }),
    }),

  evaluateHeadline: (headline: string, publisher: string = 'Manual Input') =>
    fetchJson<Signal>(`${API_BASE}/news/evaluate-manual`, {
      method: 'POST',
      body: JSON.stringify({ headline, publisher }),
    }),

  getReviewQueue: () => fetchJson<Signal[]>(`${API_BASE}/review-queue`),

  confirmReview: (id: number) =>
    fetchJson<{ status: string; signal_id: number; gemini_result?: any }>(`${API_BASE}/review-queue/${id}/confirm`, {
      method: 'POST',
    }),

  reclassifyReview: (id: number, newLabel: string, notes: string = '') =>
    fetchJson<{ status: string; signal_id: number; corrected_label: string }>(
      `${API_BASE}/review-queue/${id}/reclassify`,
      {
        method: 'POST',
        body: JSON.stringify({ new_label: newLabel, notes }),
      }
    ),

  dismissReview: (id: number, notes: string = '') =>
    fetchJson<{ status: string; signal_id: number }>(`${API_BASE}/review-queue/${id}/dismiss`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    }),

  getFeeds: () => fetchJson<Record<string, string>>(`${API_BASE}/feeds`),

  addFeed: (name: string, url: string) =>
    fetchJson<Record<string, string>>(`${API_BASE}/feeds`, {
      method: 'POST',
      body: JSON.stringify({ name, url }),
    }),

  deleteFeed: (name: string) =>
    fetchJson<Record<string, string>>(`${API_BASE}/feeds/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    }),

  runBenchmark: (invokeLiveGemini: boolean = false) =>
    fetchJson<BenchmarkSummary>(`${API_BASE}/benchmarks/run`, {
      method: 'POST',
      body: JSON.stringify({ invoke_live_gemini: invokeLiveGemini }),
    }),

  getConfig: () => fetchJson<AppConfig>(`${API_BASE}/config`),

  updateConfig: (data: { min_confidence_threshold?: number; gemini_model_id?: string }) =>
    fetchJson<AppConfig>(`${API_BASE}/config`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMarketTickers: () => fetchJson<MarketTicker[]>(`${API_BASE}/market/tickers`),

  getMarketQuote: (symbol: string) =>
    fetchJson<StockDetail>(`${API_BASE}/market/quote/${encodeURIComponent(symbol)}`),
};
