"""
SignalFlow AI - End-to-End Pipeline Orchestrator
Coordinates ingestion, Decider 2B classification, policy routing,
Gemini synthesis, review queue placement, and database persistence.
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
        }
        return d


class SignalFlowPipeline:
    """
    Complete algorithmic filtering pipeline.
    """

    def __init__(
        self,
        classification_service: Optional[ClassificationService] = None,
        gemini_service: Optional[GeminiService] = None,
        database: Optional[SignalFlowDatabase] = None,
    ):
        self.classifier = classification_service or ClassificationService()
        self.gemini = gemini_service or GeminiService()
        self.db = database or SignalFlowDatabase()

    def process_article(self, article: NormalizedArticle) -> PipelineResult:
        """
        Executes end-to-end processing for a single normalized article.
        """
        t_start = time.perf_counter()

        # Step 1: Strands Decider 2B Classification & Policy Check
        clf = self.classifier.classify_headline(article.headline)

        review_status = "NONE"
        gemini_res: Optional[GeminiAnalysisResult] = None

        if clf.policy_action == PolicyAction.APPROVE:
            # Step 2A: Cloud Synthesis via Google Gemini
            gemini_res = self.gemini.analyze_headline(
                headline=article.headline,
                decision=clf.decision,
                confidence=clf.confidence,
            )
            review_status = "NONE"
        elif clf.policy_action == PolicyAction.REVIEW_QUEUE:
            # Step 2B: Route to Review Queue
            review_status = "PENDING"
        else:
            # Step 2C: Local Drop / Neutral skip
            review_status = "NONE"

        # Step 3: Persistence to SQLite
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
        )

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
        normalizes input, classifies with Strands Decider 2B, applies policy routing,
        triggers Gemini synthesis if approved, and commits to SQLite.
        """
        from src.rss_service import RSSIngestionService
        rss = RSSIngestionService()
        article = rss.normalize_manual_input(headline=headline.strip(), publisher=publisher)
        if url:
            article.canonical_url = url
        return self.process_article(article)
