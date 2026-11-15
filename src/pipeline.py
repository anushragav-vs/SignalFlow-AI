"""
SignalFlow AI - End-to-End Pipeline Orchestrator
Coordinates ingestion, Decider 2B classification, policy routing,
Smart Ticker Detection, Market Impact Prediction, Gemini synthesis,
review queue placement, and SQLite persistence.
"""

import time
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List

from src.decider_client import DeciderClient
from src.classification_service import ClassificationService, PolicyAction, ClassificationOutput
from src.gemini_service import GeminiService, GeminiAnalysisResult
from src.database import SignalFlowDatabase
from src.rss_service import NormalizedArticle
from src.ticker_detection import SmartTickerDetector, TickerDetectionResult
from src.market_impact import MarketImpactPredictor, MarketImpactResult
from src.alerts import AlertEngine

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    headline: str
    publisher: str
    canonical_url: str
    is_live: bool
    classification: ClassificationOutput
    gemini_result: Optional[GeminiAnalysisResult]
    review_status: str
    end_to_end_latency_ms: float
    signal_id: int
    ticker_result: Optional[TickerDetectionResult] = None
    impact_result: Optional[MarketImpactResult] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "signal_id": self.signal_id,
            "headline": self.headline,
            "publisher": self.publisher,
            "canonical_url": self.canonical_url,
            "is_live": self.is_live,
            "classification": self.classification.to_dict(),
            "gemini_result": self.gemini_result.to_dict() if self.gemini_result else None,
            "review_status": self.review_status,
            "end_to_end_latency_ms": self.end_to_end_latency_ms,
            "ticker_result": self.ticker_result.to_dict() if self.ticker_result else None,
            "impact_result": self.impact_result.to_dict() if self.impact_result else None,
        }
        return d


class SignalFlowPipeline:
    """
    Complete algorithmic filtering pipeline with Smart Ticker Detection
    and Market Impact Predictor integration.
    """

    def __init__(
        self,
        classification_service: Optional[ClassificationService] = None,
        gemini_service: Optional[GeminiService] = None,
        database: Optional[SignalFlowDatabase] = None,
        ticker_detector: Optional[SmartTickerDetector] = None,
        impact_predictor: Optional[MarketImpactPredictor] = None,
        alert_engine: Optional[AlertEngine] = None,
    ):
        self.classifier = classification_service or ClassificationService()
        self.gemini = gemini_service or GeminiService()
        self.db = database or SignalFlowDatabase()
        self.ticker_detector = ticker_detector or SmartTickerDetector()
        self.impact_predictor = impact_predictor or MarketImpactPredictor()
        self.alert_engine = alert_engine or AlertEngine(db=self.db)

    def process_article(self, article: NormalizedArticle) -> PipelineResult:
        """
        Executes end-to-end processing for a single normalized article:
        1. Strands Decider 2B local classification (never overwritten)
        2. Smart Ticker Detection (forex pairs, aliases, economic relationships)
        3. Market Impact Predictor (6 dimensions, transparent score 0-100, level)
        4. Conditional Gemini institutional synthesis
        5. SQLite persistence & audit logging
        """
        t_start = time.perf_counter()

        # Step 1: Strands Decider 2B Classification & Policy Check
        clf = self.classifier.classify_headline(article.headline)

        # Step 2: Smart Ticker Detection
        ticker_res = self.ticker_detector.detect(
            headline=article.headline,
            body=article.description,
            article_id=str(article.dedup_hash),
        )

        # Step 3: Market Impact Predictor
        impact_res = self.impact_predictor.predict_impact(
            headline=article.headline,
            body=article.description,
            publisher=article.publisher,
            is_live=article.is_live,
            article_id=str(article.dedup_hash),
            decider_sentiment=clf.decision,
            affected_instruments=ticker_res.affected_instruments,
        )

        review_status = "NONE"
        gemini_res: Optional[GeminiAnalysisResult] = None

        if clf.policy_action == PolicyAction.APPROVE:
            # Step 4A: Cloud Synthesis via Google Gemini
            gemini_res = self.gemini.analyze_headline(
                headline=article.headline,
                decision=clf.decision,
                confidence=clf.confidence,
            )
            review_status = "NONE"
        elif clf.policy_action == PolicyAction.REVIEW_QUEUE:
            # Step 4B: Route to Review Queue
            review_status = "PENDING"
        else:
            # Step 4C: Local Drop / Neutral skip
            review_status = "NONE"

        # Step 5: Persistence to SQLite (Idempotent Deduplication)
        sig_id = self.db.insert_signal(
            headline=article.headline,
            publisher=article.publisher,
            canonical_url=article.canonical_url,
            is_live=article.is_live,
            decider_sentiment=clf.decision,
            decider_confidence=clf.confidence,
            probabilities=clf.probabilities,
            decider_latency_ms=clf.decider_latency_ms,
            decider_model_id=clf.model_id,
            policy_action=clf.policy_action.value,
            policy_reason=clf.policy_reason,
            review_status=review_status,
            provider_article_id=getattr(article, "provider_article_id", None),
            published_at=article.published_at,
            article_fingerprint=article.dedup_hash,
        )

        # Step 6: Store Intelligence Analysis (Tickers & Market Impact)
        self.db.update_intelligence_analysis(
            signal_id=sig_id,
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

        # Step 7: Trigger Configurable Alerts
        try:
            self.alert_engine.evaluate_and_record_alerts(
                signal_id=sig_id,
                headline=article.headline,
                decider_confidence=clf.confidence,
                ticker_result=ticker_res,
                impact_result=impact_res,
            )
        except Exception as e:
            logger.warning(f"Failed to evaluate alert rules for signal {sig_id}: {e}")

        # Update Gemini fields if invoked
        if gemini_res:
            analysis = gemini_res.analysis
            facts = analysis.reported_facts if analysis else []
            mech = analysis.transmission_mechanism if analysis else ""
            assets = analysis.affected_assets if analysis else []
            imps = analysis.directional_implications if analysis else ""
            risks = analysis.uncertainties_and_risks if analysis else []
            hyps = analysis.analytical_hypotheses if analysis else []
            watchpoints = analysis.catalyst_watchpoints if analysis else []
            horizon = analysis.market_impact_horizon if analysis else ""
            risk_level = analysis.institutional_risk_level if analysis else ""
            peers = analysis.peer_impact if analysis else []

            self.db.update_gemini_analysis(
                signal_id=sig_id,
                gemini_model_id=gemini_res.model_id,
                gemini_status=gemini_res.status,
                raw_summary=analysis.raw_summary if analysis else "",
                event_summary=analysis.event_summary if analysis else "",
                transmission_mechanism=mech,
                affected_assets=assets,
                directional_implications=imps,
                uncertainties=risks,
                reported_facts=facts,
                analytical_hypotheses=hyps,
                cloud_latency_ms=gemini_res.latency_ms,
                input_tokens=gemini_res.input_tokens,
                output_tokens=gemini_res.output_tokens,
                total_tokens=gemini_res.total_tokens,
                estimated_cost_usd=gemini_res.estimated_cost_usd,
                catalyst_watchpoints=watchpoints,
                market_impact_horizon=horizon,
                institutional_risk_level=risk_level,
                peer_impact=peers,
            )

        e2e_latency = (time.perf_counter() - t_start) * 1000.0

        return PipelineResult(
            headline=article.headline,
            publisher=article.publisher,
            canonical_url=article.canonical_url,
            is_live=article.is_live,
            classification=clf,
            gemini_result=gemini_res,
            review_status=review_status,
            end_to_end_latency_ms=round(e2e_latency, 2),
            signal_id=sig_id,
            ticker_result=ticker_res,
            impact_result=impact_res,
        )

    def process_batch(self, articles: List[NormalizedArticle]) -> List[PipelineResult]:
        return [self.process_article(a) for a in articles]

    def process_headline(
        self,
        headline: str,
        publisher: str = "Manual Input",
        url: Optional[str] = None,
    ) -> PipelineResult:
        """
        Evaluates a single custom/manual headline through the pipeline:
        normalizes input, classifies with Strands Decider 2B, runs Ticker Detection,
        calculates Market Impact, triggers Gemini synthesis if approved, and commits to SQLite.
        """
        from src.rss_service import RSSIngestionService
        rss = RSSIngestionService()
        article = rss.normalize_manual_input(headline=headline.strip(), publisher=publisher)
        if url:
            article.canonical_url = url
        return self.process_article(article)
