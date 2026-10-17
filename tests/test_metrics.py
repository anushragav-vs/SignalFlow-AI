"""
Tests for Latency, Cost, and Performance Metrics
"""

import unittest
from src.metrics import (
    compute_latency_distribution,
    compute_cloud_calls_avoided_pct,
    compute_cost_savings_pct,
    compile_benchmark_summary,
)


class TestMetrics(unittest.TestCase):
    def test_latency_distribution(self):
        latencies = [100.0, 200.0, 300.0, 400.0, 500.0]
        stats = compute_latency_distribution(latencies)
        self.assertEqual(stats["median"], 300.0)
        self.assertEqual(stats["mean"], 300.0)
        self.assertGreaterEqual(stats["p95"], 400.0)
        self.assertEqual(stats["count"], 5)

    def test_cloud_calls_avoided_pct(self):
        # 2 out of 10 forwarded to cloud -> 8 avoided (80.0%)
        avoided = compute_cloud_calls_avoided_pct(proposed_calls=2, baseline_calls=10)
        self.assertEqual(avoided, 80.0)

        # Baseline zero calls edge case
        self.assertEqual(compute_cloud_calls_avoided_pct(0, 0), 0.0)

    def test_cost_savings_pct(self):
        # Proposed spend: $0.20, Baseline spend: $1.00 -> 80% savings
        savings = compute_cost_savings_pct(proposed_spend=0.20, baseline_spend=1.00)
        self.assertEqual(savings, 80.0)

    def test_benchmark_compilation(self):
        b_records = [
            {"gemini_invoked": True, "cost_usd": 0.001, "cloud_latency_ms": 900.0},
            {"gemini_invoked": True, "cost_usd": 0.001, "cloud_latency_ms": 950.0},
        ]
        p_records = [
            {"gemini_invoked": True, "cost_usd": 0.001, "decider_latency_ms": 920.0, "cloud_latency_ms": 900.0, "e2e_latency_ms": 1820.0},
            {"gemini_invoked": False, "cost_usd": 0.0, "decider_latency_ms": 910.0, "cloud_latency_ms": 0.0, "e2e_latency_ms": 910.0},
        ]
        summary = compile_benchmark_summary(b_records, p_records)
        self.assertEqual(summary["baseline_cloud_calls"], 2)
        self.assertEqual(summary["proposed_cloud_calls"], 1)
        self.assertEqual(summary["cloud_calls_avoided_pct"], 50.0)
        self.assertEqual(summary["cost_savings_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()
