"""
Tests for Google Gemini Service using official google-genai SDK
"""

import os
import json
import unittest
from unittest.mock import MagicMock, patch

from src.gemini_service import GeminiService, StructuredFinancialAnalysis, GeminiAnalysisResult
from google.genai.errors import APIError, ClientError, ServerError


class TestGeminiService(unittest.TestCase):
    def test_missing_api_key_fails_gracefully(self):
        with patch.dict(os.environ, {}, clear=True):
            service = GeminiService(api_key="")
            cred_status = service.check_credentials_status()
            self.assertFalse(cred_status["configured"])

            result = service.analyze_headline("Headline", "Bullish", 0.95)
            self.assertEqual(result.status, "error_missing_key")
            self.assertIn("GEMINI_API_KEY is not configured", result.error_message)

    @patch("src.gemini_service.genai.Client")
    def test_gemini_success_mocked(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_resp = MagicMock()
        mock_resp.text = json.dumps({
            "event_summary": "Tesla net income surged 17% in Q3 beating estimates.",
            "transmission_mechanism": "Operating leverage and cost improvements expanded automotive margins.",
            "affected_assets": ["TSLA", "Consumer Discretionary"],
            "directional_implications": "Bullish near-term equity repricing.",
            "uncertainties_and_risks": ["Price war sustainability in Europe"],
            "reported_facts": ["17% surge in net income", "Automotive margins reached 19.8%"],
            "analytical_hypotheses": ["Gross margins likely troughed in Q2"],
        })
        mock_resp.usage_metadata.prompt_token_count = 150
        mock_resp.usage_metadata.candidates_token_count = 95
        mock_resp.usage_metadata.total_token_count = 245

        mock_client.models.generate_content.return_value = mock_resp

        service = GeminiService(api_key="mock_key")
        result = service.analyze_headline("Tesla reports Q3 net income surges 17%", "Bullish", 0.96)

        self.assertEqual(result.status, "success")
        self.assertIsNotNone(result.analysis)
        self.assertEqual(len(result.analysis.reported_facts), 2)
        self.assertEqual(len(result.analysis.affected_assets), 2)
        self.assertEqual(result.input_tokens, 150)
        self.assertEqual(result.output_tokens, 95)
        self.assertGreater(result.estimated_cost_usd, 0.0)

    @patch("src.gemini_service.genai.Client")
    def test_gemini_timeout_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = TimeoutError("Request timed out after 30s")

        service = GeminiService(api_key="mock_key")
        result = service.analyze_headline("Headline", "Bullish", 0.95)

        self.assertEqual(result.status, "error_timeout")
        self.assertIn("timed out", result.error_message.lower())

    @patch("src.gemini_service.genai.Client")
    def test_gemini_api_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = APIError(
            429, {"error": {"message": "Resource exhausted"}}, None
        )

        service = GeminiService(api_key="mock_key")
        result = service.analyze_headline("Headline", "Bullish", 0.95)

        self.assertEqual(result.status, "error_api")
        self.assertIn("Resource exhausted", result.error_message)

    @patch("src.gemini_service.genai.Client")
    def test_gemini_malformed_response_fallback(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_resp = MagicMock()
        mock_resp.text = "Plain unformatted string from model without JSON tags."
        mock_resp.usage_metadata.prompt_token_count = 50
        mock_resp.usage_metadata.candidates_token_count = 20
        mock_resp.usage_metadata.total_token_count = 70

        mock_client.models.generate_content.return_value = mock_resp

        service = GeminiService(api_key="mock_key")
        result = service.analyze_headline("Headline", "Bullish", 0.95)

        self.assertEqual(result.status, "success")
        self.assertIn("Plain unformatted string", result.analysis.raw_summary)


if __name__ == "__main__":
    unittest.main()
