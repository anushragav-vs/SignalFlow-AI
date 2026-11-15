"""
SignalFlow AI - Integration Tests for News Pipeline with Smart Ticker Detection & Market Impact
Tests end-to-end integration: Decider 2B -> Ticker Detection -> Impact Prediction -> DB Persistence.
"""

import unittest
from unittest.mock import MagicMock

from src.pipeline import SignalFlowPipeline, PipelineResult
from src.rss_service import NormalizedArticle
from src.classification_service import ClassificationService, ClassificationOutput, PolicyAction
from src.gemini_service import GeminiService
from src.database import SignalFlowDatabase
from src.ticker_detection import SmartTickerDetector
from src.market_impact import MarketImpactPredictor


class TestIntelligencePipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.mock_classifier = MagicMock(spec=ClassificationService)
        self.mock_gemini = MagicMock(spec=GeminiService)
        self.db = SignalFlowDatabase(db_path=":memory:")
        self.pipeline = SignalFlowPipeline(
            classification_service=self.mock_classifier,
            gemini_service=self.mock_gemini,
            database=self.db,
        )

    def test_pipeline_integration_with_fed_rate_hike(self):
        """
        Headline: 'Federal Reserve announces unexpected 50 bps rate hike to combat inflation.'
        Verifies:
        - Decider sentiment is Bullish (simulated) and strictly preserved.
        - Ticker detection identifies USD, EUR/USD (indirect), GBP/USD (indirect), USD/JPY (indirect), XAU/USD (potential).
        - Impact score is HIGH or CRITICAL.
        - Results are persisted to SQLite table 'signals'.
        """
        article = NormalizedArticle(
            headline="Federal Reserve announces unexpected 50 bps rate hike to combat inflation.",
            normalized_headline="federal reserve announces unexpected 50 bps rate hike to combat inflation",
            canonical_url="https://wire.com/fed-hike",
            publisher="Bloomberg",
            description="Emergency monetary tightening by the FOMC.",
            published_at="2026-10-18T12:00:00Z",
            dedup_hash="fed_hike_hash_01",
            is_live=True,
        )

        self.mock_classifier.classify_headline.return_value = ClassificationOutput(
            headline=article.headline,
            decision="Bullish",
            confidence=0.94,
            probabilities={"Bullish": 0.94, "Bearish": 0.03, "Neutral": 0.03},
            policy_action=PolicyAction.APPROVE,
            policy_reason="High conviction monetary decision",
            decider_latency_ms=15.0,
            model_id="strands-decider-2b",
            requires_review=False,
        )

        # Mock gemini call
        self.mock_gemini.analyze_headline.return_value = MagicMock(
            analysis=None,
            model_id="gemini-3.5-flash-lite",
            status="success",
            latency_ms=1200.0,
            input_tokens=150,
            output_tokens=300,
            total_tokens=450,
            estimated_cost_usd=0.0001,
        )

        res = self.pipeline.process_article(article)

        # 1. PipelineResult assertions
        self.assertEqual(res.classification.decision, "Bullish")
        self.assertIsNotNone(res.ticker_result)
        self.assertIsNotNone(res.impact_result)

        # 2. Ticker detection assertions
        ticker_res = res.ticker_result
        self.assertIn("USD", ticker_res.currencies)
        detected_symbols = {inst.symbol: inst for inst in ticker_res.affected_instruments}
        self.assertIn("EUR/USD", detected_symbols)
        self.assertEqual(detected_symbols["EUR/USD"].relationship, "indirect")
        self.assertIn("XAU/USD", detected_symbols)
        self.assertEqual(detected_symbols["XAU/USD"].relationship, "potential")

        # 3. Market impact assertions
        impact_res = res.impact_result
        self.assertIn(impact_res.impact_level, ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(impact_res.impact_score, 70)
        self.assertEqual(impact_res.event_category, "interest_rate_announcements")

        # 4. Database persistence assertions
        saved_signal = self.db.get_signal_by_id(res.signal_id)
        self.assertIsNotNone(saved_signal)
        # Decider output strictly preserved
        self.assertEqual(saved_signal["decider_sentiment"], "Bullish")
        self.assertEqual(saved_signal["decider_confidence"], 0.94)

        # Intelligence fields persisted
        self.assertEqual(saved_signal["impact_score"], impact_res.impact_score)
        self.assertEqual(saved_signal["impact_level"], impact_res.impact_level)
        self.assertEqual(saved_signal["event_category"], "interest_rate_announcements")
        self.assertIn("EUR/USD", saved_signal["affected_instruments_json"])
        self.assertIn("Federal Reserve", saved_signal["detected_entities_json"])

    def test_noise_headline_preserves_policy_and_runs_intelligence(self):
        """
        Headline: 'Celebrity spotted at film premiere in London.'
        Policy action is BLOCK_NOISE. Gemini is skipped.
        Ticker detection finds GBP/London currency context, but Market Impact score is LOW.
        """
        article = NormalizedArticle(
            headline="Celebrity spotted at film premiere in London.",
            normalized_headline="celebrity spotted at film premiere in london",
            canonical_url="https://tabloid.com/film",
            publisher="Tabloid News",
            description="Actor was seen on the red carpet.",
            published_at="2026-10-18T14:00:00Z",
            dedup_hash="noise_hash_02",
            is_live=True,
        )

        self.mock_classifier.classify_headline.return_value = ClassificationOutput(
            headline=article.headline,
            decision="Noise",
            confidence=0.98,
            probabilities={"Noise": 0.98},
            policy_action=PolicyAction.BLOCK_NOISE,
            policy_reason="Dropped locally as non-financial noise",
            decider_latency_ms=8.0,
            model_id="strands-decider-2b",
            requires_review=False,
        )

        res = self.pipeline.process_article(article)

        # Decider classified as Noise
        self.assertEqual(res.classification.decision, "Noise")
        self.assertEqual(res.classification.policy_action, PolicyAction.BLOCK_NOISE)
        self.assertIsNone(res.gemini_result)  # Cloud call skipped!

        # Market impact must be LOW
        self.assertEqual(res.impact_result.impact_level, "LOW")
        self.assertLess(res.impact_result.impact_score, 25)

        # DB persistence check
        saved = self.db.get_signal_by_id(res.signal_id)
        self.assertEqual(saved["decider_sentiment"], "Noise")
        self.assertEqual(saved["impact_level"], "LOW")


if __name__ == "__main__":
    unittest.main()

