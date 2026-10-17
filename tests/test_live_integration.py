"""
SignalFlow AI - Optional Live Integration Tests
Tests real external service endpoints when credentials/servers are configured:
- Real Google AI Studio Gemini API call via official google-genai SDK
- Real Strands Decider 2B service endpoint (or fallback verification)
"""

import os
import unittest
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

from src.gemini_service import GeminiService
from src.decider_client import DeciderClient
from src.classification_service import ClassificationService
from config import config


class TestLiveIntegration(unittest.TestCase):
    """
    Live integration tests for external APIs and services.
    Skipped automatically in CI or environments without live credentials.
    """

    @unittest.skipIf(
        not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_google_ai_studio_api_key_here",
        "Skipping live Gemini test: GEMINI_API_KEY not configured with real credential."
    )
    def test_live_gemini_api_call(self):
        """Verify real Google AI Studio Gemini endpoint returns valid structured financial analysis."""
        service = GeminiService()
        status = service.check_credentials_status()
        self.assertTrue(status["configured"], "Credentials should be marked as configured")

        headline = "NVIDIA delivers record revenue up 94% year-over-year driven by data center compute demand."
        result = service.analyze_headline(
            headline=headline,
            decision="Bullish",
            confidence=0.965
        )

        self.assertEqual(result.status, "success", f"Expected success but got: {result.error_message}")
        self.assertIsNotNone(result.analysis)
        self.assertGreater(len(result.analysis.event_summary), 10)
        self.assertGreater(result.latency_ms, 0)
        self.assertIsNotNone(result.input_tokens)
        self.assertGreater(result.input_tokens, 0)
        self.assertGreaterEqual(result.estimated_cost_usd, 0.0)

    def test_decider_service_live_or_fallback(self):
        """Verify Decider client performs real decision extraction (HTTP server or in-process fallback)."""
        client = DeciderClient(server_url=config.decider_server_url, mode="auto")
        classification_service = ClassificationService(decider_client=client)

        headline = "Federal Reserve keeps benchmark interest rates unchanged at 5.25%-5.50% range."
        result = classification_service.classify_headline(headline)

        self.assertIn(result.decision, ["Bullish", "Bearish", "Neutral", "Noise"])
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertGreater(result.decider_latency_ms, 0.0)


if __name__ == "__main__":
    unittest.main()
