"""
Tests for Strands Decider Classification & Policy Routing
"""

import unittest
from unittest.mock import MagicMock

from src.decider_client import DeciderClient, DeciderResult
from src.classification_service import ClassificationService, PolicyAction


class TestClassificationService(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=DeciderClient)
        self.service = ClassificationService(decider_client=self.mock_client, min_confidence=0.80)

    def test_noise_dropped_locally(self):
        self.mock_client.ask.return_value = DeciderResult(
            headline="Celebrity sighting in Paris",
            selected_option="Noise",
            confidence=0.95,
            probabilities={"Noise": 0.95, "Neutral": 0.05},
            latency_ms=12.0,
            model_id="test-model",
            status="success",
        )
        res = self.service.classify_headline("Celebrity sighting in Paris")
        self.assertEqual(res.policy_action, PolicyAction.BLOCK_NOISE)
        self.assertFalse(res.requires_review)

    def test_neutral_stored_cloud_skipped(self):
        self.mock_client.ask.return_value = DeciderResult(
            headline="Fed leaves rates unchanged",
            selected_option="Neutral",
            confidence=0.88,
            probabilities={"Neutral": 0.88, "Bullish": 0.05, "Bearish": 0.07},
            latency_ms=15.0,
            model_id="test-model",
            status="success",
        )
        res = self.service.classify_headline("Fed leaves rates unchanged")
        self.assertEqual(res.policy_action, PolicyAction.BLOCK_NEUTRAL)
        self.assertFalse(res.requires_review)

    def test_high_confidence_bullish_approved(self):
        self.mock_client.ask.return_value = DeciderResult(
            headline="Tesla surges on record net income",
            selected_option="Bullish",
            confidence=0.96,
            probabilities={"Bullish": 0.96, "Bearish": 0.01},
            latency_ms=20.0,
            model_id="test-model",
            status="success",
        )
        res = self.service.classify_headline("Tesla surges on record net income")
        self.assertEqual(res.policy_action, PolicyAction.APPROVE)
        self.assertFalse(res.requires_review)

    def test_low_confidence_routes_to_review_queue(self):
        self.mock_client.ask.return_value = DeciderResult(
            headline="Acquisition rumor circulated",
            selected_option="Bullish",
            confidence=0.65,  # Below 0.80 threshold
            probabilities={"Bullish": 0.65, "Neutral": 0.25, "Noise": 0.10},
            latency_ms=18.0,
            model_id="test-model",
            status="success",
        )
        res = self.service.classify_headline("Acquisition rumor circulated")
        self.assertEqual(res.policy_action, PolicyAction.REVIEW_QUEUE)
        self.assertTrue(res.requires_review)

    def test_invalid_confidence_fails_safely_to_review(self):
        self.mock_client.ask.return_value = DeciderResult(
            headline="Ambiguous headline",
            selected_option="Bearish",
            confidence=-0.1,  # Invalid confidence
            probabilities={},
            latency_ms=10.0,
            model_id="test-model",
            status="success",
        )
        res = self.service.classify_headline("Ambiguous headline")
        self.assertEqual(res.policy_action, PolicyAction.REVIEW_QUEUE)
        self.assertTrue(res.requires_review)

    def test_decider_service_failure_routes_to_review(self):
        self.mock_client.ask.return_value = DeciderResult(
            headline="Network failure headline",
            selected_option="Unknown",
            confidence=0.0,
            probabilities={},
            latency_ms=50.0,
            model_id="test-model",
            status="error_connection",
            error_message="HTTP 500 Connection Refused",
        )
        res = self.service.classify_headline("Network failure headline")
        self.assertEqual(res.policy_action, PolicyAction.REVIEW_QUEUE)
        self.assertTrue(res.requires_review)
        self.assertEqual(res.status, "error_connection")


if __name__ == "__main__":
    unittest.main()
