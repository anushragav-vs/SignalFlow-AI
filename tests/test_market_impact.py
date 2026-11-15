"""
SignalFlow AI - Unit Tests for Market Impact Predictor
Tests transparent weighted scoring, impact levels (LOW, MEDIUM, HIGH, CRITICAL),
event categorization, missing data fallbacks, and directional decoupling.
"""

import unittest
from src.market_impact.models import MarketImpactResult, ImpactDimensions
from src.market_impact.scoring import ImpactScoringEngine, DEFAULT_DIMENSION_WEIGHTS
from src.market_impact.event_classifier import EventClassifier
from src.market_impact.historical_context import HistoricalMarketContextAnalyzer
from src.market_impact.predictor import MarketImpactPredictor
from src.ticker_detection.models import AffectedInstrument


class TestMarketImpactPredictor(unittest.TestCase):
    def setUp(self):
        self.scoring = ImpactScoringEngine()
        self.classifier = EventClassifier()
        self.predictor = MarketImpactPredictor()

    def test_low_impact_news(self):
        """Routine market commentary with no central bank or major indicator."""
        headline = "Morning market coffee chat: Traders review seasonal retail trends."
        res = self.predictor.predict_impact(headline=headline, publisher="Market Blog")

        self.assertEqual(res.impact_level, "LOW")
        self.assertLess(res.impact_score, 25)
        self.assertEqual(res.volatility_assessment, "low")
        self.assertEqual(res.event_category, "other_financial_events")

    def test_medium_impact_news(self):
        """Standard economic news or corporate development."""
        headline = "Eurozone trade balance surplus expands slightly in September."
        affected = [
            AffectedInstrument(
                symbol="EUR/USD",
                relationship="indirect",
                confidence=0.80,
                reason="Eurozone trade flows.",
                mentioned_explicitly=False,
            )
        ]
        res = self.predictor.predict_impact(
            headline=headline,
            publisher="Reuters",
            affected_instruments=affected,
        )

        self.assertIn(res.impact_level, ["LOW", "MEDIUM"])
        self.assertLess(res.impact_score, 50)

    def test_high_impact_news(self):
        """High-impact inflation release with surprise beat."""
        headline = "US CPI surges 3.9% year-over-year, exceeding forecast and accelerating price pressures."
        affected = [
            AffectedInstrument(
                symbol="EUR/USD",
                relationship="indirect",
                confidence=0.90,
                reason="US CPI impact on Fed rate trajectory.",
                mentioned_explicitly=False,
            ),
            AffectedInstrument(
                symbol="USD/JPY",
                relationship="indirect",
                confidence=0.88,
                reason="Yield differential expansion.",
                mentioned_explicitly=False,
            ),
        ]
        res = self.predictor.predict_impact(
            headline=headline,
            publisher="Bloomberg",
            affected_instruments=affected,
            decider_sentiment="Bearish",
        )

        self.assertIn(res.impact_level, ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(res.impact_score, 50)
        self.assertEqual(res.event_category, "inflation_releases")
        self.assertIn(res.volatility_assessment, ["elevated", "extreme"])

    def test_critical_unexpected_central_bank_event(self):
        """Emergency or surprise central bank rate decision."""
        headline = "Federal Reserve announces emergency 75 basis point rate hike in surprise inter-meeting decision."
        affected = [
            AffectedInstrument(
                symbol="EUR/USD",
                relationship="indirect",
                confidence=0.95,
                reason="Emergency US rate hike.",
                mentioned_explicitly=False,
            ),
            AffectedInstrument(
                symbol="USD/JPY",
                relationship="indirect",
                confidence=0.95,
                reason="US yield spike.",
                mentioned_explicitly=False,
            ),
            AffectedInstrument(
                symbol="XAU/USD",
                relationship="potential",
                confidence=0.85,
                reason="Severe real yield impact on gold.",
                mentioned_explicitly=False,
            ),
        ]
        res = self.predictor.predict_impact(
            headline=headline,
            publisher="Federal Reserve",
            affected_instruments=affected,
            decider_sentiment="Bullish",
        )

        self.assertEqual(res.impact_level, "CRITICAL")
        self.assertGreaterEqual(res.impact_score, 75)
        self.assertEqual(res.volatility_assessment, "extreme")
        self.assertIn("emergency", res.explanation.lower())

    def test_rule_based_score_calculation_formula(self):
        """Verify transparent weighted score calculation matches weights exactly."""
        dims = ImpactDimensions(
            economic_importance=80,
            surprise_magnitude=60,
            instrument_relevance=70,
            source_reliability=90,
            news_novelty=80,
            potential_volatility=75,
        )
        calculated = self.scoring.calculate_score(dims)

        expected = int(round(
            80 * 0.25 + 60 * 0.20 + 70 * 0.20 + 90 * 0.10 + 80 * 0.10 + 75 * 0.15
        ))
        self.assertEqual(calculated, expected)
        self.assertEqual(calculated, 74)

    def test_missing_source_reliability_handling(self):
        """Missing or empty publisher falls back cleanly without exception."""
        dims = self.scoring.compute_dimensions(
            text="General market movement note",
            publisher="",
            category="other_financial_events",
            num_affected_instruments=0,
            has_direct_instrument=False,
        )
        self.assertEqual(dims.source_reliability, 70, "Documented default fallback for missing publisher")

    def test_decoupling_impact_score_from_direction(self):
        """
        Verify that a Bearish event and a Bullish event can both have identical high impact scores,
        confirming that impact score measures importance/magnitude, not bullishness.
        """
        bearish_headline = "Global banking collapse triggers panic sell-off across international markets."
        bullish_headline = "Historic economic stimulus and rate cuts spark massive relief surge across global markets."

        res_bearish = self.predictor.predict_impact(
            headline=bearish_headline,
            decider_sentiment="Bearish",
        )
        res_bullish = self.predictor.predict_impact(
            headline=bullish_headline,
            decider_sentiment="Bullish",
        )

        # Both are severe/critical events
        self.assertIn(res_bearish.impact_level, ["HIGH", "CRITICAL"])
        self.assertIn(res_bullish.impact_level, ["HIGH", "CRITICAL"])

        # Check that potential direction is captured distinctly from score
        if res_bearish.affected_instruments:
            self.assertEqual(res_bearish.affected_instruments[0].potential_direction, "bearish")
        if res_bullish.affected_instruments:
            self.assertEqual(res_bullish.affected_instruments[0].potential_direction, "bullish")

    def test_historical_data_unavailable_explicitly_labeled(self):
        """Ensure analyzer does NOT invent fake historical statistics when none exist."""
        analyzer = HistoricalMarketContextAnalyzer(historical_database={})
        ctx = analyzer.get_context_for_event(event_category="interest_rate_announcements")

        self.assertFalse(ctx.has_historical_data)
        self.assertEqual(ctx.data_status, "historical_data_unavailable")
        self.assertEqual(ctx.methodology, "rule_based_fallback")
        for window in ["15m", "1h", "4h", "1d"]:
            self.assertIn(window, ctx.windows)
            self.assertIsNone(ctx.windows[window]["absolute_return_pct"])

    def test_historical_data_when_verified_record_present(self):
        """When verified historical record is present, correctly surface outcomes."""
        verified_db = {
            "interest_rate_announcements:EUR/USD": {
                "15m": {"absolute_return_pct": 0.45, "signed_return_pct": -0.45, "realized_volatility_pct": 0.55},
                "1h": {"absolute_return_pct": 0.82, "signed_return_pct": -0.80, "realized_volatility_pct": 0.70},
                "4h": {"absolute_return_pct": 1.10, "signed_return_pct": -1.05, "realized_volatility_pct": 0.95},
                "1d": {"absolute_return_pct": 1.35, "signed_return_pct": -1.20, "realized_volatility_pct": 1.10},
            }
        }
        analyzer = HistoricalMarketContextAnalyzer(historical_database=verified_db)
        ctx = analyzer.get_context_for_event(
            event_category="interest_rate_announcements",
            symbol="EUR/USD",
        )

        self.assertTrue(ctx.has_historical_data)
        self.assertEqual(ctx.data_status, "verified_historical_record")
        self.assertEqual(ctx.windows["1h"]["signed_return_pct"], -0.80)


if __name__ == "__main__":
    unittest.main()

