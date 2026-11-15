"""
SignalFlow AI - Unit & Integration Tests for Market Intelligence REST API
Tests all /api/intelligence/* endpoints including ticker detection summaries,
impact profiles, drilldowns, alert rules, alert notifications, and aggregate stats.
"""

import unittest
from fastapi import HTTPException

from api import (
    db,
    get_intelligence_tickers,
    get_intelligence_impact,
    get_intelligence_news_detail,
    get_intelligence_instrument_detail,
    get_market_quote_detail,
    get_intelligence_alerts,
    create_or_update_alert_rule,
    mark_alert_as_read,
    analyze_article_intelligence,
    get_intelligence_statistics,
    CreateAlertRuleRequest,
    AnalyzeArticleRequest,
)


class TestIntelligenceAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Directly seed an intelligence signal in the test database
        cls.test_signal_id = db.insert_signal(
            headline="Federal Reserve announces surprise 50 bps interest rate hike to curb inflation.",
            publisher="Bloomberg",
            decider_sentiment="Bullish",
            decider_confidence=0.95,
            policy_action="APPROVE",
            policy_reason="High conviction monetary tightening",
            is_live=True,
        )

        db.update_intelligence_analysis(
            signal_id=cls.test_signal_id,
            detected_entities=[
                {"name": "Federal Reserve", "entity_type": "central_bank", "mention_type": "explicit"}
            ],
            affected_instruments=[
                {"symbol": "EUR/USD", "relationship": "indirect", "confidence": 0.89, "reason": "US monetary policy transmission to Euro.", "mentioned_explicitly": False},
                {"symbol": "GBP/USD", "relationship": "indirect", "confidence": 0.89, "reason": "US monetary policy transmission to Pound.", "mentioned_explicitly": False},
                {"symbol": "USD/JPY", "relationship": "indirect", "confidence": 0.89, "reason": "US yield expansion.", "mentioned_explicitly": False},
                {"symbol": "XAU/USD", "relationship": "potential", "confidence": 0.74, "reason": "Real yield pressure on gold.", "mentioned_explicitly": False},
            ],
            currencies=["USD", "EUR", "GBP", "JPY", "XAU"],
            economic_events=["interest_rate_decision", "inflation_overview"],
            impact_score=85,
            impact_level="CRITICAL",
            impact_dimensions={
                "economic_importance": 92,
                "surprise_magnitude": 88,
                "instrument_relevance": 90,
                "source_reliability": 95,
                "news_novelty": 80,
                "potential_volatility": 85,
            },
            event_category="interest_rate_announcements",
            volatility_assessment="extreme",
            impact_explanation="A critical interest rate announcement by the Federal Reserve.",
            impact_methodology="rule_based",
            impact_limitations=["Actual reaction depends on market expectations."],
        )

    def test_get_intelligence_tickers(self):
        """GET /api/intelligence/tickers returns supported universe and summaries."""
        data = get_intelligence_tickers()
        self.assertIn("supported_universe", data)
        self.assertIn("instruments_summary", data)
        self.assertGreaterEqual(data["total_supported"], 12)

        symbols = [item["symbol"] for item in data["supported_universe"]]
        self.assertIn("EUR/USD", symbols)
        self.assertIn("GBP/USD", symbols)
        self.assertIn("USD/JPY", symbols)
        self.assertIn("XAU/USD", symbols)

        # Check EUR/USD summary counts
        eur_summary = next((s for s in data["instruments_summary"] if s["symbol"] == "EUR/USD"), None)
        self.assertIsNotNone(eur_summary)
        self.assertGreaterEqual(eur_summary["indirect_count"], 1)

    def test_get_intelligence_impact(self):
        """GET /api/intelligence/impact returns distribution and dimension averages."""
        data = get_intelligence_impact(limit=50)
        self.assertIn("distribution", data)
        self.assertIn("dimension_averages", data)
        self.assertIn("signals", data)
        self.assertGreaterEqual(data["total_analyzed"], 1)
        self.assertGreaterEqual(data["distribution"]["CRITICAL"], 1)

    def test_get_intelligence_news_detail(self):
        """GET /api/intelligence/news/{article_id} returns complete intelligence profile."""
        data = get_intelligence_news_detail(article_id=self.test_signal_id)
        self.assertEqual(data["id"], self.test_signal_id)
        self.assertIn("detected_entities", data)
        self.assertIn("affected_instruments", data)
        self.assertEqual(data["impact_score"], 85)
        self.assertEqual(data["impact_level"], "CRITICAL")
        self.assertIn("historical_context", data)

    def test_get_intelligence_news_detail_not_found(self):
        """GET /api/intelligence/news/999999 raises 404."""
        with self.assertRaises(HTTPException) as cm:
            get_intelligence_news_detail(article_id=999999)
        self.assertEqual(cm.exception.status_code, 404)

    def test_get_intelligence_instrument_detail(self):
        """GET /api/intelligence/instruments/{symbol} returns pair breakdown."""
        data = get_intelligence_instrument_detail(symbol="EUR/USD")
        self.assertEqual(data["symbol"], "EUR/USD")
        self.assertIn("relationship_counts", data)
        self.assertIn("sentiment_counts", data)
        self.assertIn("signals", data)
        self.assertIn("related_central_banks", data)
        self.assertIn("European Central Bank (ECB)", data["related_central_banks"])
        self.assertIn("market_quote", data)
        self.assertGreater(data["market_quote"]["price"], 0)
        self.assertGreaterEqual(data["total_correlated_signals"], 1)

    def test_get_market_quote_detail_forex(self):
        """GET /api/market/quote/{symbol:path} supports forex pairs without 404."""
        quote = get_market_quote_detail(symbol="EUR/USD")
        self.assertEqual(quote["category"], "FOREX")
        self.assertGreater(quote["price"], 0)
        self.assertIn("sparkline", quote)
        self.assertIn("related_signals", quote)

    def test_get_intelligence_instrument_detail_alias(self):
        """Alias normalization e.g. EURUSD maps to EUR/USD."""
        data = get_intelligence_instrument_detail(symbol="EURUSD")
        self.assertEqual(data["symbol"], "EUR/USD")

    def test_get_intelligence_instrument_detail_unsupported(self):
        """Unsupported symbol raises 404."""
        with self.assertRaises(HTTPException) as cm:
            get_intelligence_instrument_detail(symbol="FABRICATED-PAIR")
        self.assertEqual(cm.exception.status_code, 404)

    def test_get_intelligence_alerts(self):
        """GET /api/intelligence/alerts returns rules and generated alerts."""
        data = get_intelligence_alerts()
        self.assertIn("rules", data)
        self.assertIn("alerts", data)
        self.assertIn("unread_count", data)

    def test_create_alert_rule_and_mark_read(self):
        """POST /api/intelligence/alerts/rules and read status toggle."""
        req = CreateAlertRuleRequest(
            name="Bank of England Monitoring",
            condition_type="central_bank_event",
            target_value="Bank of England",
            min_confidence=0.75,
            enabled=True,
        )
        res = create_or_update_alert_rule(req)
        self.assertEqual(res["status"], "success")
        self.assertIn("rule_id", res)

        # Insert and mark alert read
        alert_id = db.insert_alert(
            signal_id=self.test_signal_id,
            rule_id=res["rule_id"],
            alert_type="central_bank_event",
            title="BoE Alert",
            message="BoE meeting notes",
            severity="warning",
        )
        read_res = mark_alert_as_read(alert_id=alert_id)
        self.assertEqual(read_res["status"], "success")

    def test_reanalyze_article_endpoint(self):
        """POST /api/intelligence/analyze/{article_id} triggers re-analysis."""
        req = AnalyzeArticleRequest(use_gemini=False)
        data = analyze_article_intelligence(article_id=self.test_signal_id, req=req)
        self.assertEqual(data["id"], self.test_signal_id)
        self.assertGreater(data["impact_score"], 0)
        self.assertIn("affected_instruments", data)

    def test_get_intelligence_statistics(self):
        """GET /api/intelligence/statistics returns dashboard stats."""
        data = get_intelligence_statistics()
        self.assertIn("total_analyzed", data)
        self.assertIn("avg_impact_score", data)
        self.assertIn("top_events", data)
        self.assertIn("total_alerts", data)


if __name__ == "__main__":
    unittest.main()
