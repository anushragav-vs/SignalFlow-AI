"""
SignalFlow AI - Latency, Cost & Performance Metrics Calculation
Implements mandatory hackathon formulas and statistical distributions without fabricated figures.
"""

from typing import List, Dict, Any, Optional
import numpy as np


def compute_latency_distribution(latencies_ms: List[float]) -> Dict[str, float]:
    """
    Computes mean, median, and p95 latency.
    Requires at least one measurement; reports 0.0 if empty.
    """
    if not latencies_ms:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0, "count": 0}

    arr = np.array(latencies_ms)
    return {
        "mean": round(float(np.mean(arr)), 1),
        "median": round(float(np.median(arr)), 1),
        "p95": round(float(np.percentile(arr, 95)), 1),
        "min": round(float(np.min(arr)), 1),
        "max": round(float(np.max(arr)), 1),
        "count": len(arr),
    }


def compute_cloud_calls_avoided_pct(proposed_calls: int, baseline_calls: int) -> float:
    """
    Formula: 100 * (1 - proposed cloud calls / baseline cloud calls)
    """
    if baseline_calls <= 0:
        return 0.0
    val = 100.0 * (1.0 - (float(proposed_calls) / float(baseline_calls)))
    return round(max(0.0, min(100.0, val)), 1)


def compute_cost_savings_pct(proposed_spend: float, baseline_spend: float) -> float:
    """
    Formula: 100 * (1 - proposed estimated spend / baseline estimated spend)
    """
    if baseline_spend <= 0.0:
        return 0.0
    val = 100.0 * (1.0 - (proposed_spend / baseline_spend))
    return round(max(0.0, min(100.0, val)), 1)


def compile_benchmark_summary(
    baseline_records: List[Dict[str, Any]],
    proposed_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compares baseline (all sent to cloud) against proposed pipeline (Decider 2B gatekeeper).
    """
    n = len(baseline_records)
    if n == 0:
        return {}

    b_cloud_calls = sum(1 for r in baseline_records if r.get("gemini_invoked"))
    p_cloud_calls = sum(1 for r in proposed_records if r.get("gemini_invoked"))

    b_spend = sum(r.get("cost_usd", 0.0) for r in baseline_records)
    p_spend = sum(r.get("cost_usd", 0.0) for r in proposed_records)

    p_decider_latencies = [r.get("decider_latency_ms", 0.0) for r in proposed_records if r.get("decider_latency_ms")]
    p_cloud_latencies = [r.get("cloud_latency_ms", 0.0) for r in proposed_records if r.get("cloud_latency_ms")]
    p_e2e_latencies = [r.get("e2e_latency_ms", 0.0) for r in proposed_records if r.get("e2e_latency_ms")]

    calls_avoided_pct = compute_cloud_calls_avoided_pct(p_cloud_calls, b_cloud_calls)
    savings_pct = compute_cost_savings_pct(p_spend, b_spend)

    return {
        "dataset_size": n,
        "baseline_cloud_calls": b_cloud_calls,
        "proposed_cloud_calls": p_cloud_calls,
        "cloud_calls_avoided_pct": calls_avoided_pct,
        "baseline_estimated_spend_usd": round(b_spend, 6),
        "proposed_estimated_spend_usd": round(p_spend, 6),
        "cost_savings_pct": savings_pct,
        "decider_latency_stats": compute_latency_distribution(p_decider_latencies),
        "cloud_latency_stats": compute_latency_distribution(p_cloud_latencies),
        "e2e_latency_stats": compute_latency_distribution(p_e2e_latencies),
    }
