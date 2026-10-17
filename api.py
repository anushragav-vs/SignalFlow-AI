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
pipeline = SignalFlowPipeline(classification_service=classifier, gemini_service=gemini, database=db)
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


# Helper to safely deserialize JSON fields
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

    # Safe defaults
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
) -> List[Dict[str, Any]]:
    """Returns recent financial signals with optional filtering."""
    raw_signals = db.get_recent_signals(limit=limit)
    formatted = [format_signal_record(s) for s in raw_signals]

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


@app.get("/api/market/quote/{symbol}")
def get_market_quote_detail(symbol: str = Path(...)) -> Dict[str, Any]:
    """Returns live stock quote, sparkline, and correlated news signals from SQLite."""
    quote = market_service.fetch_live_quote(symbol)
    disp = quote.get("display_symbol", symbol)
    name = quote.get("name", symbol)

    # Correlate signals matching this ticker or company name
    raw_signals = db.get_recent_signals(limit=100)
    related = []
    bullish = 0
    bearish = 0
    neutral = 0

    for s in raw_signals:
        headline = (s.get("headline") or "").lower()
        assets_json = (s.get("affected_assets_json") or "").lower()
        symbol_lower = symbol.lower().replace("^", "")
        disp_lower = disp.lower()
        name_lower = name.lower()

        # Check for symbol or name in headline or affected assets
        if (
            symbol_lower in headline
            or disp_lower in headline
            or name_lower in headline
            or symbol_lower in assets_json
            or disp_lower in assets_json
            or name_lower in assets_json
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8008, reload=False)
