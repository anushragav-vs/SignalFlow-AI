"""
SignalFlow AI - Unit Tests for Smart Ticker Detection
Tests deterministic matching, context-aware economic relationship classification,
explicit vs indirect distinctions, manual correction, and registry validation.
"""

import unittest
from unittest.mock import MagicMock
from src.ticker_detection.registry import InstrumentRegistry, DEFAULT_SUPPORTED_INSTRUMENTS
from src.ticker_detection.matcher import DeterministicEntityMatcher
from src.ticker_detection.relationship_engine import EconomicRelationshipEngine
from src.ticker_detection.gemini_extractor import GeminiEntityExtractor
from src.ticker_detection.detector import SmartTickerDetector
from src.ticker_detection.models import TickerDetectionResult, DetectedEntity, AffectedInstrument


class TestSmartTickerDetection(unittest.TestCase):
    def setUp(self):
        self.registry = InstrumentRegistry()
        self.matcher = DeterministicEntityMatcher(registry=self.registry)
        self.rel_engine = EconomicRelationshipEngine(registry=self.registry)
        self.detector = SmartTickerDetector(registry=self.registry)

    def test_eur_usd_explicit_detection(self):
        text = "EUR/USD edged higher today following European trade balance data."
        res = self.matcher.match(text)
        self.assertIn("EUR/USD", res["explicit_instruments"])
        self.assertIn("EUR", res["currencies"])
        self.assertIn("USD", res["currencies"])

    def test_eurusd_alias_detection(self):
        text = "EURUSD rallied 45 pips during the London morning session."
        res = self.matcher.match(text)
        self.assertIn("EUR/USD", res["explicit_instruments"])
        self.assertIn("EUR", res["currencies"])
        self.assertIn("USD", res["currencies"])

    def test_euro_dollar_and_fiber_aliases(self):
        text1 = "Euro Dollar holds steady ahead of key rate decision."
        res1 = self.matcher.match(text1)
        self.assertIn("EUR/USD", res1["explicit_instruments"])

        text2 = "Fiber tests key resistance at 1.0950."
        res2 = self.matcher.match(text2)
        self.assertIn("EUR/USD", res2["explicit_instruments"])

    def test_cable_alias_detection(self):
        text = "Cable slips below 1.3000 as Bank of England signals potential pause."
        res = self.matcher.match(text)
        self.assertIn("GBP/USD", res["explicit_instruments"])
        self.assertIn("GBP", res["currencies"])
        self.assertIn("USD", res["currencies"])
        cb_names = [cb["name"] for cb in res["central_banks"]]
        self.assertIn("Bank of England", cb_names)

    def test_dollar_yen_alias_detection(self):
        text = "Dollar Yen surges past 155.00 after Bank of Japan maintains yield curve policy."
        res = self.matcher.match(text)
        self.assertIn("USD/JPY", res["explicit_instruments"])
        self.assertIn("USD", res["currencies"])
        self.assertIn("JPY", res["currencies"])
        cb_names = [cb["name"] for cb in res["central_banks"]]
        self.assertIn("Bank of Japan", cb_names)

    def test_central_bank_detection_all_majors(self):
        banks_text = (
            "Federal Reserve and European Central Bank issue joint liquidity guidelines while "
            "Reserve Bank of Australia, Bank of Canada, and Swiss National Bank adjust reserves."
        )
        res = self.matcher.match(banks_text)
        cbs = [cb["name"] for cb in res["central_banks"]]
        self.assertIn("Federal Reserve", cbs)
        self.assertIn("European Central Bank", cbs)
        self.assertIn("Reserve Bank of Australia", cbs)
        self.assertIn("Bank of Canada", cbs)
        self.assertIn("Swiss National Bank", cbs)

    def test_economic_indicators_detection(self):
        text = "U.S. CPI and Core PPI print higher than expected, while NFP jobs report and Unemployment remain resilient."
        res = self.matcher.match(text)
        self.assertIn("cpi_release", res["economic_events"])
        self.assertIn("ppi_release", res["economic_events"])
        self.assertIn("nfp_release", res["economic_events"])
        self.assertIn("unemployment_rate", res["economic_events"])

    def test_duplicate_entity_removal(self):
        text = "The Federal Reserve Chair Jerome Powell spoke at the FOMC meeting. The Fed will monitor data."
        res = self.matcher.match(text)
        fed_entities = [e for e in res["detected_entities"] if e.name == "Federal Reserve"]
        self.assertEqual(len(fed_entities), 1, "Duplicate entity references must be deduplicated to 1 canonical entity")

    def test_ambiguity_handling_fed_casual_word(self):
        text = "The chef fed the guests at the restaurant event yesterday."
        res = self.matcher.match(text)
        cb_names = [cb["name"] for cb in res["central_banks"]]
        self.assertNotIn("Federal Reserve", cb_names)

    def test_ambiguity_handling_cad_acronym(self):
        text = "Architectural cad drawings were submitted for building approval."
        res = self.matcher.match(text)
        self.assertNotIn("CAD", res["currencies"])

    def test_unsupported_symbol_rejection(self):
        self.assertFalse(self.registry.is_supported("XYZ/ABC"))
        self.assertFalse(self.registry.is_supported("FABRICATED"))
        self.assertIsNone(self.registry.normalize_symbol("XYZ/ABC"))

    def test_gold_xau_supported(self):
        text = "Spot Gold and XAU/USD surge toward historic highs amid haven demand."
        res = self.matcher.match(text)
        self.assertIn("XAU/USD", res["explicit_instruments"])
        self.assertIn("XAU", res["currencies"])

    # --- Stage 3 Relationship Engine & Context Tests ---

    def test_fed_rate_hike_indirect_and_potential_relationships(self):
        """
        Tests example from Part 2.3:
        News: 'Federal Reserve announces a surprise interest rate increase.'
        Expected:
        - USD: Direct economic relevance
        - EUR/USD: Indirect relevance
        - GBP/USD: Indirect relevance
        - USD/JPY: Indirect relevance
        - XAU/USD: Potential relevance
        - Explicit flag is False for pairs not in text
        """
        headline = "Federal Reserve announces a surprise interest rate increase."
        res = self.detector.detect(headline=headline, article_id="art-fed-001")

        self.assertIn("USD", res.currencies)
        self.assertIn("interest_rate_decision", res.economic_events)

        instruments_by_symbol = {inst.symbol: inst for inst in res.affected_instruments}

        # Check EUR/USD is indirect
        self.assertIn("EUR/USD", instruments_by_symbol)
        eurusd = instruments_by_symbol["EUR/USD"]
        self.assertEqual(eurusd.relationship, "indirect")
        self.assertFalse(eurusd.mentioned_explicitly)
        self.assertGreater(eurusd.confidence, 0.80)
        self.assertIn("Federal Reserve", eurusd.reason)

        # Check GBP/USD is indirect
        self.assertIn("GBP/USD", instruments_by_symbol)
        gbpusd = instruments_by_symbol["GBP/USD"]
        self.assertEqual(gbpusd.relationship, "indirect")
        self.assertFalse(gbpusd.mentioned_explicitly)

        # Check USD/JPY is indirect
        self.assertIn("USD/JPY", instruments_by_symbol)
        usdjpy = instruments_by_symbol["USD/JPY"]
        self.assertEqual(usdjpy.relationship, "indirect")
        self.assertFalse(usdjpy.mentioned_explicitly)

        # Check XAU/USD is potential
        self.assertIn("XAU/USD", instruments_by_symbol)
        xauusd = instruments_by_symbol["XAU/USD"]
        self.assertEqual(xauusd.relationship, "potential")
        self.assertFalse(xauusd.mentioned_explicitly)
        self.assertIn("real yields", xauusd.reason.lower())

    def test_direct_vs_indirect_distinction(self):
        """
        When EUR/USD is explicitly in text and Fed is mentioned:
        EUR/USD should be DIRECT (mentioned_explicitly=True),
        while GBP/USD and USD/JPY should remain INDIRECT.
        """
        headline = "EUR/USD slides to monthly low as Federal Reserve signals hawkish terminal rate."
        res = self.detector.detect(headline=headline, article_id="art-mixed-002")

        instruments = {inst.symbol: inst for inst in res.affected_instruments}
        self.assertIn("EUR/USD", instruments)
        self.assertEqual(instruments["EUR/USD"].relationship, "direct")
        self.assertTrue(instruments["EUR/USD"].mentioned_explicitly)

        self.assertIn("GBP/USD", instruments)
        self.assertEqual(instruments["GBP/USD"].relationship, "indirect")
        self.assertFalse(instruments["GBP/USD"].mentioned_explicitly)

    def test_ecb_monetary_policy_transmission(self):
        """ECB rate cut should transmit indirectly to EUR/USD, EUR/GBP, EUR/JPY."""
        headline = "European Central Bank cuts deposit facility rate by 25 basis points amid slowing Eurozone inflation."
        res = self.detector.detect(headline=headline)

        instruments = {inst.symbol: inst for inst in res.affected_instruments}
        self.assertIn("EUR/USD", instruments)
        self.assertEqual(instruments["EUR/USD"].relationship, "indirect")
        self.assertIn("EUR/GBP", instruments)
        self.assertEqual(instruments["EUR/GBP"].relationship, "indirect")
        self.assertIn("EUR/JPY", instruments)
        self.assertEqual(instruments["EUR/JPY"].relationship, "indirect")

    def test_manual_correction_capability(self):
        """Part 2.5: Manual correction capability allows updating or removing affected instruments."""
        headline = "Federal Reserve announces a surprise interest rate increase."
        initial = self.detector.detect(headline=headline)

        # Human analyst overrides: promote XAU/USD to high-confidence direct, and remove USD/CHF
        corrections = {
            "affected_instruments": {
                "XAU/USD": {
                    "relationship": "direct",
                    "confidence": 0.99,
                    "reason": "Trader noted direct gold desk margin calls.",
                    "mentioned_explicitly": True,
                }
            },
            "remove_instruments": ["USD/CHF"],
        }
        corrected = self.detector.apply_manual_correction(initial, corrections)
        corrected_dict = {inst.symbol: inst for inst in corrected.affected_instruments}

        self.assertIn("XAU/USD", corrected_dict)
        self.assertEqual(corrected_dict["XAU/USD"].relationship, "direct")
        self.assertEqual(corrected_dict["XAU/USD"].confidence, 0.99)
        self.assertNotIn("USD/CHF", corrected_dict)

    def test_gemini_assisted_extractor_filters_hallucinated_symbols(self):
        """Ensures that even if Gemini returns an unsupported symbol (e.g. BTC/USDT or XYZ/USD), it is discarded."""
        mock_gemini = MagicMock()
        mock_gemini.check_credentials_status.return_value = {"configured": True}
        mock_client = MagicMock()
        mock_gemini._get_client.return_value = mock_client
        mock_gemini.model_id = "gemini-3.5-flash-lite"

        # Mock LLM returning valid pair AND unsupported hallucinated pair
        mock_response = MagicMock()
        mock_response.text = '''{
            "detected_entities": [{"name": "Bank of England", "entity_type": "central_bank", "mention_type": "explicit"}],
            "affected_instruments": [
                {"symbol": "GBP/USD", "relationship": "indirect", "confidence": 0.92, "reason": "UK rates affect Cable.", "mentioned_explicitly": false},
                {"symbol": "BTC/USDT", "relationship": "potential", "confidence": 0.50, "reason": "Crypto speculative move.", "mentioned_explicitly": false},
                {"symbol": "FABRICATED/XYZ", "relationship": "indirect", "confidence": 0.70, "reason": "Fake ticker.", "mentioned_explicitly": false}
            ],
            "currencies": ["GBP", "USD"],
            "economic_events": ["interest_rate_decision"]
        }'''
        mock_client.models.generate_content.return_value = mock_response

        extractor = GeminiEntityExtractor(gemini_service=mock_gemini, registry=self.registry)
        result = extractor.extract_with_gemini(headline="BoE unexpected hike")

        self.assertIsNotNone(result)
        symbols = [inst.symbol for inst in result.affected_instruments]
        self.assertIn("GBP/USD", symbols)
        self.assertNotIn("BTC/USDT", symbols, "Unsupported symbol must be rejected")
        self.assertNotIn("FABRICATED/XYZ", symbols, "Fabricated symbol must be rejected")


if __name__ == "__main__":
    unittest.main()
