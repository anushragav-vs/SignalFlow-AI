"""
SignalFlow AI - FastAPI REST API Bridge
Provides high-performance, asynchronous REST endpoints for the React frontend
while strictly preserving the existing Python backend services and core logic.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import config, FINANCIAL_DISCLAIMER
from src.database import SignalFlowDatabase
from src.decider_client import DeciderClient
from src.classification_service import ClassificationService
from src.gemini_service import GeminiService
from src.pipeline import SignalFlowPipeline
from src.rss_service import RSSIngestionService
from src.review_service import ReviewService
from src.benchmarking import run_benchmark_comparison
from src.market_service import MarketTickerService
from src.ticker_detection import SmartTickerDetector, instrument_registry
from src.market_impact import MarketImpactPredictor
from src.alerts import AlertEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("signalflow-api")

app = FastAPI(
    title="SignalFlow AI REST API",
    description="Backend API for SignalFlow AI React Dashboard",
    version="1.0.0",
)

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singletons preserving existing backend
db = SignalFlowDatabase(config.sqlite_db_path)
decider = DeciderClient(server_url=config.decider_server_url, checkpoint=config.decider_checkpoint)
classifier = ClassificationService(decider_client=decider, min_confidence=config.min_confidence_threshold)
gemini = GeminiService(api_key=config.gemini_api_key, model_id=config.gemini_model_id)
ticker_detector = SmartTickerDetector(registry=instrument_registry)
impact_predictor = MarketImpactPredictor()
alert_engine = AlertEngine(db=db)
pipeline = SignalFlowPipeline(
    classification_service=classifier,
    gemini_service=gemini,
    database=db,
    ticker_detector=ticker_detector,
    impact_predictor=impact_predictor,
    alert_engine=alert_engine,
)
rss_service = RSSIngestionService()
review_service = ReviewService(db=db)
market_service = MarketTickerService()


# -----------------------------------------------------------------------------
# Request & Response Pydantic Models
# -----------------------------------------------------------------------------
class FetchFeedRequest(BaseModel):
    feed_name: str = Field(default="Yahoo Finance Markets")
    max_items: int = Field(default=6, ge=1, le=20)


class EvaluateHeadlineRequest(BaseModel):
    headline: str = Field(..., min_length=5)
    publisher: str = Field(default="Manual Input")
    url: Optional[str] = None


class ReclassifyRequest(BaseModel):
    new_label: str = Field(..., pattern="^(Bullish|Bearish|Neutral|Noise)$")
    notes: Optional[str] = ""


class DismissRequest(BaseModel):
    notes: Optional[str] = ""


class AddFeedRequest(BaseModel):
    name: str = Field(..., min_length=2)
    url: str = Field(..., pattern=r"^https?://")


class UpdateConfigRequest(BaseModel):
    min_confidence_threshold: Optional[float] = Field(None, ge=0.5, le=0.99)
    gemini_model_id: Optional[str] = None


class RunBenchmarkRequest(BaseModel):
    invoke_live_gemini: bool = False


class CreateAlertRuleRequest(BaseModel):
    name: str = Field(..., min_length=2)
    condition_type: str = Field(..., pattern="^(critical_impact|high_impact|currency_mention|watchlist_pair|central_bank_event)$")
    target_value: Optional[str] = None
    min_confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    enabled: bool = True


class AnalyzeArticleRequest(BaseModel):
    use_gemini: bool = False


# Helper to safely deserialize JSON fields
def deduplicate_signal_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates formatted signal dictionaries based on 3-tier identity priority:
    1. Provider article ID / fingerprint
    2. Canonical URL (if http/https)
    3. Normalized headline + publisher
    Preserves the most complete and earliest/authoritative record.
    """
    from src.deduplication import canonicalize_url, normalize_headline

    seen_keys = set()
    unique_records = []

    for r in records:
        can_u = canonicalize_url(r.get("canonical_url") or "")
        fp = r.get("article_fingerprint")
        norm_h = normalize_headline(r.get("headline") or "")
        pub = (r.get("publisher") or "").strip().lower()

        if can_u and can_u.startswith(("http://", "https://")):
            key = f"URL:{can_u}"
        elif fp and fp.startswith(("PID:", "URL:")):
            key = fp
        else:
            key = f"TEXT:{pub}|{norm_h}"

        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_records.append(r)

    return unique_records


def format_signal_record(s: Dict[str, Any]) -> Dict[str, Any]:
    formatted = dict(s)
    # Parse probabilities
    if formatted.get("probabilities_json"):
        try:
            formatted["probabilities"] = json.loads(formatted["probabilities_json"])
        except Exception:
            formatted["probabilities"] = {}
    else:
        formatted["probabilities"] = {}

    # Parse Gemini JSON lists
    for k in ["affected_assets", "reported_facts", "uncertainties", "analytical_hypotheses", "catalyst_watchpoints", "peer_impact"]:
        json_key = f"{k}_json"
        if formatted.get(json_key):
            try:
                formatted[k] = json.loads(formatted[json_key])
            except Exception:
                formatted[k] = []
        else:
            formatted[k] = []

    # Parse Intelligence JSON fields
    for k in ["detected_entities", "affected_instruments", "currencies", "economic_events", "impact_limitations"]:
        json_key = f"{k}_json"
        if formatted.get(json_key):
            try:
                formatted[k] = json.loads(formatted[json_key])
            except Exception:
                formatted[k] = []
        else:
            formatted[k] = []

    if formatted.get("impact_dimensions_json"):
        try:
            formatted["impact_dimensions"] = json.loads(formatted["impact_dimensions_json"])
        except Exception:
            formatted["impact_dimensions"] = {}
    else:
        formatted["impact_dimensions"] = {}

    # Safe defaults
    formatted["impact_score"] = formatted.get("impact_score") if formatted.get("impact_score") is not None else 0
    formatted["impact_level"] = formatted.get("impact_level") or "LOW"
    formatted["event_category"] = formatted.get("event_category") or "other_financial_events"
    formatted["volatility_assessment"] = formatted.get("volatility_assessment") or "low"
    formatted["impact_explanation"] = formatted.get("impact_explanation") or ""
    formatted["impact_methodology"] = formatted.get("impact_methodology") or "rule_based"
    formatted["cloud_latency_ms"] = formatted.get("cloud_latency_ms") or 0.0
    formatted["decider_latency_ms"] = formatted.get("decider_latency_ms") or 0.0
    formatted["estimated_cost_usd"] = formatted.get("estimated_cost_usd") or 0.0
    formatted["market_impact_horizon"] = formatted.get("market_impact_horizon") or ""
    formatted["institutional_risk_level"] = formatted.get("institutional_risk_level") or ""
    formatted["directional_implications"] = formatted.get("directional_implications") or ""
    return formatted


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Returns application, Decider 2B, and Gemini health status."""
    cred_status = gemini.check_credentials_status()
    return {
        "status": "healthy",
        "system_one": {
            "model": config.decider_checkpoint,
            "server_url": config.decider_server_url,
            "status": "active",
        },
        "system_two": {
            "provider": "Google AI Studio",
            "model": gemini.model_id,
            "configured": cred_status["configured"],
            "masked_key": config.get_masked_api_key(),
        },
        "database": {
            "path": config.sqlite_db_path,
            "status": "connected",
        },
        "disclaimer": FINANCIAL_DISCLAIMER,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/kpis")
def get_kpis() -> Dict[str, Any]:
    """Returns real-time KPIs and audit metrics from SQLite."""
    return db.get_kpis()


@app.get("/api/signals")
def get_signals(
    limit: int = Query(default=60, ge=1, le=200),
    search: Optional[str] = Query(default=None),
    sentiment: Optional[str] = Query(default=None),
    policy_action: Optional[str] = Query(default=None),
    review_status: Optional[str] = Query(default=None),
    filter_non_financial: bool = Query(default=True),
) -> List[Dict[str, Any]]:
    """Returns recent financial signals with automatic non-financial noise avoidance."""
    raw_signals = db.get_recent_signals(limit=limit)
    formatted = [format_signal_record(s) for s in raw_signals]

    if filter_non_financial and (not sentiment or sentiment.lower() != "noise"):
        # Strictly exclude non-financial noise
        formatted = [s for s in formatted if s.get("decider_sentiment", "").lower() != "noise"]

    if search:
        q = search.lower().strip()
        formatted = [s for s in formatted if q in s["headline"].lower() or q in s.get("publisher", "").lower()]

    if sentiment:
        formatted = [s for s in formatted if s.get("decider_sentiment", "").lower() == sentiment.lower()]

    if policy_action:
        formatted = [s for s in formatted if s.get("policy_action", "").lower() == policy_action.lower()]

    if review_status:
        formatted = [s for s in formatted if s.get("review_status", "").lower() == review_status.lower()]

    return formatted


@app.get("/api/signals/{signal_id}")
def get_signal_detail(signal_id: int = Path(..., ge=1)) -> Dict[str, Any]:
    """Returns detailed signal record including full Gemini research breakdown."""
    sig = db.get_signal_by_id(signal_id)
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")
    return format_signal_record(sig)


@app.post("/api/news/fetch")
def fetch_and_process_feed(req: FetchFeedRequest) -> Dict[str, Any]:
    """Ingests articles from an RSS feed and processes them through the Decider policy pipeline."""
    articles = rss_service.fetch_feed(req.feed_name, max_items=req.max_items)
    if not articles:
        return {"processed_count": 0, "results": [], "message": f"No articles fetched from {req.feed_name}"}

    results = pipeline.process_batch(articles)
    return {
        "processed_count": len(results),
        "results": [r.to_dict() for r in results],
        "message": f"Successfully processed {len(results)} articles through Decider 2B",
    }


@app.post("/api/news/evaluate-manual")
def evaluate_manual_headline(req: EvaluateHeadlineRequest) -> Dict[str, Any]:
    """Evaluates a single user-submitted headline through the pipeline."""
    res = pipeline.process_headline(
        headline=req.headline,
        publisher=req.publisher,
        url=req.url,
    )
    sig = db.get_signal_by_id(res.signal_id)
    if sig:
        return format_signal_record(sig)
    return res.to_dict()


@app.get("/api/review-queue")
def get_review_queue() -> List[Dict[str, Any]]:
    """Returns items currently pending human oversight in the Review Queue."""
    items = review_service.get_pending_items()
    return [format_signal_record(i) for i in items]


@app.post("/api/review-queue/{signal_id}/confirm")
def confirm_and_send_to_gemini(signal_id: int = Path(..., ge=1)) -> Dict[str, Any]:
    """Approves a review-queue item and routes it to Google Gemini for deep research."""
    sig = db.get_signal_by_id(signal_id)
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")

    res = review_service.approve_and_send_to_gemini(signal_id, gemini_service=gemini)
    return res


@app.post("/api/review-queue/{signal_id}/reclassify")
def reclassify_signal(signal_id: int = Path(..., ge=1), req: ReclassifyRequest = ...) -> Dict[str, Any]:
    """Reclassifies a signal while strictly preserving the original model decision."""
    sig = db.get_signal_by_id(signal_id)
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")

    review_service.reclassify_item(signal_id, new_label=req.new_label, notes=req.notes)
    return {"status": "success", "signal_id": signal_id, "corrected_label": req.new_label}


@app.post("/api/review-queue/{signal_id}/dismiss")
def dismiss_signal(signal_id: int = Path(..., ge=1), req: DismissRequest = ...) -> Dict[str, Any]:
    """Dismisses an item in the review queue as noise."""
    sig = db.get_signal_by_id(signal_id)
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")

    review_service.dismiss_item(signal_id, notes=req.notes)
    return {"status": "success", "signal_id": signal_id}


@app.get("/api/feeds")
def list_feeds() -> Dict[str, str]:
    """Returns the list of configured RSS feeds."""
    return rss_service.get_feeds()


@app.post("/api/feeds")
def add_feed(req: AddFeedRequest) -> Dict[str, str]:
    """Adds a new RSS feed to the ingestion configuration."""
    rss_service.add_feed(req.name, req.url)
    return rss_service.get_feeds()


@app.delete("/api/feeds/{feed_name}")
def delete_feed(feed_name: str = Path(...)) -> Dict[str, str]:
    """Removes an RSS feed from the ingestion configuration."""
    rss_service.remove_feed(feed_name)
    return rss_service.get_feeds()


@app.get("/api/market/tickers")
def get_market_tickers() -> List[Dict[str, Any]]:
    """Returns live macro index and equity quotes for the top ticker ribbon."""
    return market_service.get_top_market_tickers()


@app.get("/api/market/quote/{symbol:path}")
def get_market_quote_detail(symbol: str = Path(...)) -> Dict[str, Any]:
    """Returns live stock quote, sparkline, and correlated news signals from SQLite."""
    quote = market_service.fetch_live_quote(symbol)
    disp = quote.get("display_symbol", symbol)
    name = quote.get("name", symbol)

    # Correlate signals matching this ticker, company name, or forex pair
    raw_signals = db.get_recent_signals(limit=100)
    related = []
    bullish = 0
    bearish = 0
    neutral = 0

    norm_symbol = instrument_registry.normalize_symbol(symbol) if instrument_registry else None

    for s in raw_signals:
        headline = (s.get("headline") or "").lower()
        assets_json = (s.get("affected_assets_json") or "").lower()
        instruments_json = (s.get("affected_instruments_json") or "").lower()
        symbol_lower = symbol.lower().replace("^", "")
        disp_lower = disp.lower()
        name_lower = name.lower()
        norm_lower = norm_symbol.lower() if norm_symbol else ""

        # Check for symbol or name in headline, affected assets, or affected instruments
        if (
            symbol_lower in headline
            or disp_lower in headline
            or name_lower in headline
            or (norm_lower and norm_lower in headline)
            or symbol_lower in assets_json
            or disp_lower in assets_json
            or name_lower in assets_json
            or (norm_lower and norm_lower in instruments_json)
        ):
            formatted_s = format_signal_record(s)
            related.append(formatted_s)
            sent = formatted_s.get("decider_sentiment", "")
            if sent == "Bullish":
                bullish += 1
            elif sent == "Bearish":
                bearish += 1
            elif sent == "Neutral":
                neutral += 1

    total = len(related)
    sentiment_score = 50
    if total > 0:
        sentiment_score = int(50 + ((bullish - bearish) / total) * 50)
        sentiment_score = max(5, min(95, sentiment_score))

    quote["related_signals"] = related[:12]
    quote["related_signals_count"] = total
    quote["sentiment_stats"] = {
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "sentiment_score": sentiment_score,
        "sentiment_label": "Bullish" if sentiment_score >= 60 else "Bearish" if sentiment_score <= 40 else "Neutral",
    }
    return quote


@app.post("/api/benchmarks/run")
def run_benchmark(req: RunBenchmarkRequest) -> Dict[str, Any]:
    """Executes the reproducible head-to-head benchmark suite."""
    return run_benchmark_comparison(invoke_live_gemini=req.invoke_live_gemini)


@app.get("/api/config")
def get_config() -> Dict[str, Any]:
    """Returns public configuration settings and active policies."""
    return {
        "min_confidence_threshold": classifier.min_confidence,
        "gemini_model_id": gemini.model_id,
        "decider_checkpoint": config.decider_checkpoint,
        "decider_server_url": config.decider_server_url,
        "sqlite_db_path": config.sqlite_db_path,
        "masked_api_key": config.get_masked_api_key(),
        "disclaimer": FINANCIAL_DISCLAIMER,
        "tags": config.project_tags,
    }


@app.post("/api/config")
def update_config(req: UpdateConfigRequest) -> Dict[str, Any]:
    """Updates active policy threshold or model ID in memory."""
    if req.min_confidence_threshold is not None:
        classifier.min_confidence = req.min_confidence_threshold
    if req.gemini_model_id:
        gemini.model_id = req.gemini_model_id

    return {
        "status": "success",
        "min_confidence_threshold": classifier.min_confidence,
        "gemini_model_id": gemini.model_id,
    }


# -----------------------------------------------------------------------------
# Market Intelligence Endpoints (Part 6)
# -----------------------------------------------------------------------------
@app.get("/api/intelligence/tickers")
def get_intelligence_tickers() -> Dict[str, Any]:
    """Returns supported forex instruments and aggregation of detected mentions across recent signals."""
    supported = []
    for sym in instrument_registry.get_all_supported_symbols():
        inst = instrument_registry.get_instrument(sym)
        if inst:
            supported.append({
                "symbol": inst.symbol,
                "name": inst.name,
                "base_currency": inst.base_currency,
                "quote_currency": inst.quote_currency,
                "category": inst.category,
                "aliases": inst.aliases,
            })

    raw_signals = db.get_recent_signals(limit=150)
    formatted = [format_signal_record(s) for s in raw_signals]
    unique_signals = deduplicate_signal_records(formatted)

    instruments_summary: Dict[str, Dict[str, Any]] = {}
    for s_item in supported:
        sym = s_item["symbol"]
        instruments_summary[sym] = {
            "symbol": sym,
            "name": s_item["name"],
            "base_currency": s_item["base_currency"],
            "quote_currency": s_item["quote_currency"],
            "total_mentions": 0,
            "direct_count": 0,
            "indirect_count": 0,
            "potential_count": 0,
            "impact_scores": [],
            "sentiments": {"Bullish": 0, "Bearish": 0, "Neutral": 0},
        }

    priority_map = {"direct": 3, "indirect": 2, "potential": 1}

    for sig in unique_signals:
        aff = sig.get("affected_instruments") or []
        sent = sig.get("decider_sentiment", "Neutral")
        score = sig.get("impact_score", 0)

        # Ensure each symbol in a unique article is counted at most once
        best_for_symbol: Dict[str, str] = {}
        for item in aff:
            sym = item.get("symbol")
            if not sym or sym not in instruments_summary:
                continue
            rel = (item.get("relationship") or "indirect").lower()
            curr_best = best_for_symbol.get(sym)
            if not curr_best or priority_map.get(rel, 0) > priority_map.get(curr_best, 0):
                best_for_symbol[sym] = rel

        for sym, best_rel in best_for_symbol.items():
            instruments_summary[sym]["total_mentions"] += 1
            if best_rel == "direct":
                instruments_summary[sym]["direct_count"] += 1
            elif best_rel == "indirect":
                instruments_summary[sym]["indirect_count"] += 1
            elif best_rel == "potential":
                instruments_summary[sym]["potential_count"] += 1

            instruments_summary[sym]["impact_scores"].append(score)
            if sent in instruments_summary[sym]["sentiments"]:
                instruments_summary[sym]["sentiments"][sent] += 1

    summary_list = []
    for sym, data in instruments_summary.items():
        scores = data.pop("impact_scores")
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        sents = data["sentiments"]
        data["avg_impact_score"] = avg_score
        data["dominant_sentiment"] = (
            "Bullish" if sents["Bullish"] > sents["Bearish"] and sents["Bullish"] > sents["Neutral"]
            else "Bearish" if sents["Bearish"] > sents["Bullish"] and sents["Bearish"] > sents["Neutral"]
            else "Neutral"
        )
        summary_list.append(data)

    summary_list.sort(key=lambda x: -x["total_mentions"])

    return {
        "supported_universe": supported,
        "instruments_summary": summary_list,
        "total_supported": len(supported),
    }


@app.get("/api/intelligence/impact")
def get_intelligence_impact(
    limit: int = Query(default=60, ge=1, le=150),
    min_level: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """Returns impact distribution, score dimensions, and recent high/critical signals."""
    limit_val = limit if isinstance(limit, int) else 60
    min_lvl_val = min_level if isinstance(min_level, str) else None

    raw_signals = db.get_recent_signals(limit=limit_val)
    formatted = [format_signal_record(s) for s in raw_signals if s.get("impact_score") is not None]

    dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    dim_sums = {
        "economic_importance": 0.0,
        "surprise_magnitude": 0.0,
        "instrument_relevance": 0.0,
        "source_reliability": 0.0,
        "news_novelty": 0.0,
        "potential_volatility": 0.0,
    }
    dim_count = 0

    filtered_signals = []
    for sig in formatted:
        lvl = sig.get("impact_level", "LOW")
        if lvl in dist:
            dist[lvl] += 1

        dims = sig.get("impact_dimensions") or {}
        if dims:
            dim_count += 1
            for k in dim_sums:
                dim_sums[k] += dims.get(k, 0)

        if not min_lvl_val:
            filtered_signals.append(sig)
        else:
            ml = min_lvl_val.upper()
            if ml == "CRITICAL" and lvl == "CRITICAL":
                filtered_signals.append(sig)
            elif ml == "HIGH" and lvl in ("HIGH", "CRITICAL"):
                filtered_signals.append(sig)
            elif ml == "MEDIUM" and lvl in ("MEDIUM", "HIGH", "CRITICAL"):
                filtered_signals.append(sig)
            elif ml == "LOW":
                filtered_signals.append(sig)

    dim_averages = {
        k: round(v / dim_count, 1) if dim_count > 0 else 0.0 for k, v in dim_sums.items()
    }

    return {
        "distribution": dist,
        "dimension_averages": dim_averages,
        "total_analyzed": len(formatted),
        "signals": filtered_signals,
    }


@app.get("/api/intelligence/news/{article_id}")
def get_intelligence_news_detail(article_id: int = Path(..., ge=1)) -> Dict[str, Any]:
    """Returns deep intelligence profile for a single signal including detected entities, impact, and context."""
    sig = db.get_signal_by_id(article_id)
    if not sig:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")

    formatted = format_signal_record(sig)

    # Attach historical context analyzer evaluation
    primary_sym = None
    if formatted.get("affected_instruments"):
        primary_sym = formatted["affected_instruments"][0].get("symbol")

    hist_analyzer = impact_predictor.historical_analyzer
    hist_ctx = hist_analyzer.get_context_for_event(
        event_category=formatted.get("event_category", "other_financial_events"),
        symbol=primary_sym,
    )
    formatted["historical_context"] = hist_ctx.model_dump()
    return formatted


@app.get("/api/intelligence/instruments/{symbol:path}")
def get_intelligence_instrument_detail(symbol: str = Path(...)) -> Dict[str, Any]:
    """Returns intelligence details, sentiment distribution, and correlated signals for a specific forex pair."""
    norm_symbol = instrument_registry.normalize_symbol(symbol)
    if not norm_symbol or not instrument_registry.is_supported(norm_symbol):
        raise HTTPException(status_code=404, detail=f"Unsupported forex instrument symbol: '{symbol}'")

    inst = instrument_registry.get_instrument(norm_symbol)
    raw_signals = db.get_recent_signals(limit=150)
    formatted = [format_signal_record(s) for s in raw_signals]
    unique_signals = deduplicate_signal_records(formatted)

    priority_map = {"direct": 3, "indirect": 2, "potential": 1}

    correlated = []
    relationship_counts = {"direct": 0, "indirect": 0, "potential": 0}
    sentiment_counts = {"Bullish": 0, "Bearish": 0, "Neutral": 0}
    impact_scores = []

    for s in unique_signals:
        aff = s.get("affected_instruments") or []
        matches = [item for item in aff if item.get("symbol") == norm_symbol]
        if not matches:
            continue

        best_rel = "indirect"
        best_p = 0
        reasons = []
        is_explicit = False

        for m in matches:
            rel = (m.get("relationship") or "indirect").lower()
            p = priority_map.get(rel, 1)
            if p > best_p:
                best_p = p
                best_rel = rel
            r = (m.get("reason") or "").strip()
            if r and r not in reasons:
                reasons.append(r)
            if m.get("mentioned_explicitly"):
                is_explicit = True

        article_copy = dict(s)
        article_copy["primary_relationship"] = best_rel
        article_copy["primary_reason"] = (
            " ; ".join(reasons)
            if reasons
            else (s.get("impact_explanation") or "Macro transmission channel evaluated by market impact model.")
        )
        article_copy["mentioned_explicitly"] = is_explicit

        correlated.append(article_copy)

        if best_rel in relationship_counts:
            relationship_counts[best_rel] += 1

        sent = s.get("decider_sentiment", "Neutral")
        if sent in sentiment_counts:
            sentiment_counts[sent] += 1

        if s.get("impact_score") is not None:
            impact_scores.append(s["impact_score"])

    # Deterministic ordering: latest timestamp, highest ID
    correlated.sort(
        key=lambda x: (x.get("timestamp") or "", x.get("id") or 0),
        reverse=True,
    )

    critical_count = 0
    high_count = 0
    highest_impact_signal = None
    max_impact = -1

    for s in correlated:
        lvl = s.get("impact_level", "LOW")
        score = s.get("impact_score", 0)
        if lvl == "CRITICAL":
            critical_count += 1
        elif lvl == "HIGH":
            high_count += 1
        if score > max_impact:
            max_impact = score
            highest_impact_signal = s

    total = len(correlated)
    avg_score = round(sum(impact_scores) / len(impact_scores), 1) if impact_scores else 0.0

    # Dominant sentiment calculation
    bull = sentiment_counts.get("Bullish", 0)
    bear = sentiment_counts.get("Bearish", 0)
    neu = sentiment_counts.get("Neutral", 0)
    dominant_sent = "Neutral"
    if bull > bear and bull >= neu:
        dominant_sent = "Bullish"
    elif bear > bull and bear >= neu:
        dominant_sent = "Bearish"

    sentiment_score = 50
    if total > 0:
        sentiment_score = int(50 + ((bull - bear) / total) * 50)
        sentiment_score = max(5, min(95, sentiment_score))

    # Central bank mapping based on currencies
    cb_map = {
        "USD": "Federal Reserve (Fed)",
        "EUR": "European Central Bank (ECB)",
        "GBP": "Bank of England (BoE)",
        "JPY": "Bank of Japan (BoJ)",
        "AUD": "Reserve Bank of Australia (RBA)",
        "CAD": "Bank of Canada (BoC)",
        "CHF": "Swiss National Bank (SNB)",
        "NZD": "Reserve Bank of New Zealand (RBNZ)",
    }
    related_cbs = []
    base_curr = inst.base_currency if inst else ""
    quote_curr = inst.quote_currency if inst else ""
    if base_curr in cb_map and cb_map[base_curr] not in related_cbs:
        related_cbs.append(cb_map[base_curr])
    if quote_curr in cb_map and cb_map[quote_curr] not in related_cbs:
        related_cbs.append(cb_map[quote_curr])

    # Fetch live quote with graceful fallback
    live_quote = market_service.fetch_live_quote(norm_symbol)

    # Historical reaction context
    hist_analyzer = impact_predictor.historical_analyzer
    hist_ctx = hist_analyzer.get_context_for_event(
        event_category="interest_rate_announcements" if "rate" in norm_symbol.lower() else "central_bank_decisions",
        symbol=norm_symbol,
    )

    return {
        "symbol": norm_symbol,
        "name": inst.name if inst else norm_symbol,
        "base_currency": base_curr,
        "quote_currency": quote_curr,
        "category": inst.category if inst else "major",
        "aliases": inst.aliases if inst else [],
        "total_correlated_signals": total,
        "direct_count": relationship_counts.get("direct", 0),
        "indirect_count": relationship_counts.get("indirect", 0),
        "potential_count": relationship_counts.get("potential", 0),
        "average_impact_score": avg_score,
        "critical_events_count": critical_count,
        "high_events_count": high_count,
        "highest_impact_news": highest_impact_signal,
        "relationship_counts": relationship_counts,
        "sentiment_counts": sentiment_counts,
        "dominant_sentiment": dominant_sent,
        "sentiment_score": sentiment_score,
        "related_central_banks": related_cbs,
        "related_currencies": [c for c in [base_curr, quote_curr] if c],
        "macro_indicators": ["Interest Rate Decisions", "Inflation (CPI/PPI)", "Employment (NFP)", "GDP Growth", "Trade Balance"],
        "historical_reaction": hist_ctx.model_dump(),
        "market_quote": live_quote,
        "signals": correlated[:25],
    }


@app.get("/api/intelligence/alerts")
def get_intelligence_alerts(
    limit: int = Query(default=50, ge=1, le=150),
    unread_only: bool = Query(default=False),
) -> Dict[str, Any]:
    """Returns active alert rules and generated alerts."""
    limit_val = limit if isinstance(limit, int) else 50
    unread_val = unread_only if isinstance(unread_only, bool) else False

    rules = db.get_alert_rules()
    alerts = db.get_alerts(limit=limit_val, unread_only=unread_val)
    unread_count = sum(1 for a in alerts if not a.get("is_read", 0))

    return {
        "rules": rules,
        "alerts": alerts,
        "unread_count": unread_count,
    }


@app.post("/api/intelligence/alerts/rules")
def create_or_update_alert_rule(req: CreateAlertRuleRequest) -> Dict[str, Any]:
    """Creates a new user alert condition."""
    rule_id = db.save_alert_rule(
        name=req.name,
        condition_type=req.condition_type,
        target_value=req.target_value,
        min_confidence=req.min_confidence,
        enabled=req.enabled,
    )
    return {
        "status": "success",
        "rule_id": rule_id,
        "rules": db.get_alert_rules(),
    }


@app.post("/api/intelligence/alerts/{alert_id}/read")
def mark_alert_as_read(alert_id: int = Path(..., ge=1)) -> Dict[str, Any]:
    """Marks an alert notification as read."""
    db.mark_alert_read(alert_id)
    return {"status": "success", "alert_id": alert_id}


@app.post("/api/intelligence/analyze/{article_id}")
def analyze_article_intelligence(
    article_id: int = Path(..., ge=1),
    req: AnalyzeArticleRequest = AnalyzeArticleRequest(),
) -> Dict[str, Any]:
    """Re-runs or initiates intelligence detection and impact prediction for an existing signal record."""
    sig = db.get_signal_by_id(article_id)
    if not sig:
        raise HTTPException(status_code=404, detail=f"Signal {article_id} not found")

    headline = sig.get("headline", "")
    publisher = sig.get("publisher", "Manual Input")
    is_live = bool(sig.get("is_live", 1))
    sentiment = sig.get("decider_sentiment", "Neutral")
    confidence = float(sig.get("decider_confidence", 0.85))

    ticker_res = ticker_detector.detect(
        headline=headline,
        article_id=str(article_id),
        use_gemini=req.use_gemini,
    )

    impact_res = impact_predictor.predict_impact(
        headline=headline,
        publisher=publisher,
        is_live=is_live,
        article_id=str(article_id),
        decider_sentiment=sentiment,
        affected_instruments=ticker_res.affected_instruments,
    )

    db.update_intelligence_analysis(
        signal_id=article_id,
        detected_entities=[e.model_dump() for e in ticker_res.detected_entities],
        affected_instruments=[inst.model_dump() for inst in ticker_res.affected_instruments],
        currencies=ticker_res.currencies,
        economic_events=ticker_res.economic_events,
        impact_score=impact_res.impact_score,
        impact_level=impact_res.impact_level,
        impact_dimensions=impact_res.impact_dimensions.model_dump(),
        event_category=impact_res.event_category,
        volatility_assessment=impact_res.volatility_assessment,
        impact_explanation=impact_res.explanation,
        impact_methodology=impact_res.methodology,
        impact_limitations=impact_res.limitations,
    )

    alert_engine.evaluate_and_record_alerts(
        signal_id=article_id,
        headline=headline,
        decider_confidence=confidence,
        ticker_result=ticker_res,
        impact_result=impact_res,
    )

    updated = db.get_signal_by_id(article_id)
    return format_signal_record(updated)


@app.get("/api/intelligence/statistics")
def get_intelligence_statistics() -> Dict[str, Any]:
    """Returns high-level statistics across all intelligence signals and alerts."""
    return db.get_intelligence_statistics()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8008, reload=False)
