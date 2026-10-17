"""
Tests for SQLite Persistence and Audit Trail
"""

import unittest
from src.database import SignalFlowDatabase


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = SignalFlowDatabase(db_path=":memory:")

    def test_insert_and_retrieve_signal(self):
        sig_id = self.db.insert_signal(
            headline="Tesla reports record margins",
            publisher="Bloomberg",
            decider_sentiment="Bullish",
            decider_confidence=0.96,
            policy_action="APPROVE",
            policy_reason="High conviction",
            decider_latency_ms=950.0,
        )
        self.assertGreater(sig_id, 0)

        signals = self.db.get_recent_signals(limit=10)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["headline"], "Tesla reports record margins")
        self.assertEqual(signals[0]["decider_sentiment"], "Bullish")

    def test_review_queue_and_human_action_preserves_original(self):
        sig_id = self.db.insert_signal(
            headline="Ambiguous rumor on regional bank",
            publisher="Reuters",
            decider_sentiment="Bullish",
            decider_confidence=0.55,
            policy_action="REVIEW_QUEUE",
            policy_reason="Low confidence",
            review_status="PENDING",
        )

        pending = self.db.get_pending_reviews()
        self.assertEqual(len(pending), 1)

        # Human reclassifies as Neutral
        self.db.record_review_action(
            signal_id=sig_id,
            action="RECLASSIFIED",
            corrected_label="Neutral",
            notes="Rumor appears non-material upon human review.",
        )

        # Queue should now be empty
        self.assertEqual(len(self.db.get_pending_reviews()), 0)

        # Original decider_sentiment MUST NOT be overwritten
        signals = self.db.get_recent_signals(limit=1)
        self.assertEqual(signals[0]["decider_sentiment"], "Bullish")  # Preserved!
        self.assertEqual(signals[0]["corrected_label"], "Neutral")    # Human correction logged
        self.assertEqual(signals[0]["review_status"], "RECLASSIFIED")

    def test_kpis_calculation(self):
        self.db.insert_signal("H1", "Pub", "Bullish", 0.95, "APPROVE", "OK")
        self.db.insert_signal("H2", "Pub", "Noise", 0.40, "BLOCK_NOISE", "Drop")
        self.db.insert_signal("H3", "Pub", "Neutral", 0.85, "BLOCK_NEUTRAL", "Skip")

        kpis = self.db.get_kpis()
        self.assertEqual(kpis["total_received"], 3)
        self.assertEqual(kpis["bullish_count"], 1)
        self.assertEqual(kpis["noise_count"], 1)
        self.assertEqual(kpis["neutral_count"], 1)
        self.assertEqual(kpis["cloud_calls_avoided_count"], 2)


if __name__ == "__main__":
    unittest.main()
