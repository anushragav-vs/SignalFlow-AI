"""
Tests for End-to-End SignalFlow Pipeline
"""

import unittest
from unittest.mock import MagicMock

from src.pipeline import SignalFlowPipeline
from src.rss_service import NormalizedArticle
from src.classification_service import ClassificationService, ClassificationOutput, PolicyAction
from src.gemini_service import GeminiService, GeminiAnalysisResult, StructuredFinancialAnalysis
from src.database import SignalFlowDatabase


class TestSignalFlowPipeline(unittest.TestCase):
    def setUp(self):
        self.mock_classifier = MagicMock(spec=ClassificationService)
        self.mock_gemini = MagicMock(spec=GeminiService)
        self.db = SignalFlowDatabase(db_path=":memory:")
        self.pipeline = SignalFlowPipeline(
            classification_service=self.mock_classifier,
            gemini_service=self.mock_gemini,
            database=self.db,
        )

    def test_noise_pipeline_flow(self):
        article = NormalizedArticle(
            headline="Celebrity gala in the Hamptons",
            normalized_headline="celebrity gala in the hamptons",
            canonical_url="https://news.com/gala",
            publisher="Celebrity Feed",
            description="Lifestyle post",
            published_at="2026-10-16T00:00:00Z",
            dedup_hash="hash1",
            is_live=True,
        )
        self.mock_classifier.classify_headline.return_value = ClassificationOutput(
            headline=article.headline,
            decision="Noise",
            confidence=0.45,
            probabilities={"Noise": 0.45},
            policy_action=PolicyAction.BLOCK_NOISE,
            policy_reason="Dropped locally as noise",
            decider_latency_ms=10.0,
            model_id="test-decider",
            requires_review=False,
        )

        res = self.pipeline.process_article(article)
        self.assertEqual(res.classification.policy_action, PolicyAction.BLOCK_NOISE)
        self.assertIsNone(res.gemini_result)
        self.assertEqual(res.review_status, "NONE")
        self.mock_gemini.analyze_headline.assert_not_called()

        # Check DB
        signals = self.db.get_recent_signals(limit=1)
        self.assertEqual(signals[0]["policy_action"], "BLOCK_NOISE")

    def test_low_confidence_pipeline_flow(self):
        article = NormalizedArticle(
            headline="Rumor on bank acquisition",
            normalized_headline="rumor on bank acquisition",
            canonical_url="https://news.com/rumor",
            publisher="Rumor Feed",
            description="M&A post",
            published_at="2026-10-16T00:00:00Z",
            dedup_hash="hash2",
            is_live=True,
        )
        self.mock_classifier.classify_headline.return_value = ClassificationOutput(
            headline=article.headline,
            decision="Bullish",
            confidence=0.55,  # Below threshold
            probabilities={"Bullish": 0.55},
            policy_action=PolicyAction.REVIEW_QUEUE,
            policy_reason="Held in review queue",
            decider_latency_ms=12.0,
            model_id="test-decider",
            requires_review=True,
        )

        res = self.pipeline.process_article(article)
        self.assertEqual(res.classification.policy_action, PolicyAction.REVIEW_QUEUE)
        self.assertEqual(res.review_status, "PENDING")
        self.mock_gemini.analyze_headline.assert_not_called()

        # Check Review Queue
        pending = self.db.get_pending_reviews()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["headline"], article.headline)

    def test_high_conviction_pipeline_flow(self):
        article = NormalizedArticle(
            headline="Tesla Q3 net income surges 17%",
            normalized_headline="tesla q3 net income surges 17",
            canonical_url="https://news.com/tsla",
            publisher="Market News",
            description="Earnings beat",
            published_at="2026-10-16T00:00:00Z",
            dedup_hash="hash3",
            is_live=True,
        )
        self.mock_classifier.classify_headline.return_value = ClassificationOutput(
            headline=article.headline,
            decision="Bullish",
            confidence=0.96,
            probabilities={"Bullish": 0.96},
            policy_action=PolicyAction.APPROVE,
            policy_reason="Approved for cloud research",
            decider_latency_ms=15.0,
            model_id="test-decider",
            requires_review=False,
        )
        self.mock_gemini.analyze_headline.return_value = GeminiAnalysisResult(
            headline=article.headline,
            decision="Bullish",
            confidence=0.96,
            model_id="gemini-3.5-flash-lite",
            latency_ms=850.0,
            analysis=StructuredFinancialAnalysis(
                event_summary="Tesla earnings beat.",
                transmission_mechanism="Margin expansion",
                affected_assets=["TSLA"],
                raw_summary="Synthesized dossier",
            ),
            input_tokens=120,
            output_tokens=80,
            total_tokens=200,
            estimated_cost_usd=0.000033,
            status="success",
        )

        res = self.pipeline.process_article(article)
        self.assertEqual(res.classification.policy_action, PolicyAction.APPROVE)
        self.assertIsNotNone(res.gemini_result)
        self.assertEqual(res.gemini_result.status, "success")
        self.mock_gemini.analyze_headline.assert_called_once()

        signals = self.db.get_recent_signals(limit=1)
        self.assertEqual(signals[0]["gemini_status"], "success")
        self.assertEqual(signals[0]["total_tokens"], 200)

    def test_process_headline_custom_input(self):
        self.mock_classifier.classify_headline.return_value = ClassificationOutput(
            headline="NVIDIA announces new Blackwell Ultra architecture",
            decision="Bullish",
            confidence=0.95,
            probabilities={"Bullish": 0.95},
            policy_action=PolicyAction.APPROVE,
            policy_reason="Approved for cloud research",
            decider_latency_ms=10.0,
            model_id="test-decider",
            requires_review=False,
        )
        self.mock_gemini.analyze_headline.return_value = None

        res = self.pipeline.process_headline("NVIDIA announces new Blackwell Ultra architecture")
        self.assertIsNotNone(res)
        self.assertEqual(res.headline, "NVIDIA announces new Blackwell Ultra architecture")
        self.assertEqual(res.publisher, "Manual Input")
        self.assertEqual(res.classification.decision, "Bullish")
        self.assertGreater(res.signal_id, 0)


if __name__ == "__main__":
    unittest.main()
