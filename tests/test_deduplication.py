"""
SignalFlow AI - Unit & Integration Tests for Deduplication Engine
Tests 3-tier identity priority, headline normalization, idempotent database insertion,
and instrument relationship merging.
"""

import unittest
from src.deduplication import (
    normalize_headline,
    canonicalize_url,
    extract_published_date,
    compute_article_fingerprint,
)
from src.database import SignalFlowDatabase


class TestDeduplicationEngine(unittest.TestCase):
    def setUp(self):
        self.db = SignalFlowDatabase(db_path=":memory:")

    def test_headline_normalization_rules(self):
        h1 = "  Federal Reserve: Announces 50 Bps Rate Hike!  "
        h2 = "federal reserve announces 50 bps rate hike"
        self.assertEqual(normalize_headline(h1), normalize_headline(h2))

        # Unicode quotes and dashes
        h3 = "“ECB Holds Rates” — Lagarde Signals Neutral Stance…"
        h4 = '"ecb holds rates" - lagarde signals neutral stance...'
        self.assertEqual(normalize_headline(h3), normalize_headline(h4))

    def test_canonicalize_url_strips_tracking(self):
        u1 = "https://www.bloomberg.com/markets/rates?utm_source=rss&utm_medium=feed&ref=home#top"
        u2 = "https://www.bloomberg.com/markets/rates"
        self.assertEqual(canonicalize_url(u1), canonicalize_url(u2))

    def test_identity_priority_provider_id_takes_precedence(self):
        fp1 = compute_article_fingerprint(
            provider_article_id="BBG-12345",
            canonical_url="https://bloomberg.com/1",
            headline="Fed Hikes",
            publisher="Bloomberg",
        )
        fp2 = compute_article_fingerprint(
            provider_article_id="BBG-12345",
            canonical_url="https://reuters.com/syndicated",
            headline="Fed Hikes Rates Higher",
            publisher="Bloomberg",
        )
        self.assertEqual(fp1, fp2)

    def test_identity_priority_canonical_url_when_no_provider_id(self):
        fp1 = compute_article_fingerprint(
            canonical_url="https://reuters.com/markets/fed-hike?utm_campaign=daily",
            headline="Headline Variant A",
            publisher="Reuters",
        )
        fp2 = compute_article_fingerprint(
            canonical_url="https://reuters.com/markets/fed-hike",
            headline="Headline Variant B",
            publisher="Reuters",
        )
        self.assertEqual(fp1, fp2)

    def test_two_different_articles_with_similar_headlines_not_merged(self):
        # Different sources and dates
        fp1 = compute_article_fingerprint(
            headline="Gold prices settle lower amid dollar strength",
            publisher="Bloomberg",
            published_at="2026-10-15T10:00:00Z",
        )
        fp2 = compute_article_fingerprint(
            headline="Gold prices settle lower amid dollar strength",
            publisher="Reuters",
            published_at="2026-10-18T10:00:00Z",
        )
        self.assertNotEqual(fp1, fp2)

    def test_idempotent_database_insertion(self):
        id1 = self.db.insert_signal(
            headline="Federal Reserve raises benchmark rate by 25 bps",
            publisher="Reuters",
            decider_sentiment="Bullish",
            decider_confidence=0.92,
            policy_action="APPROVE",
            policy_reason="Rate hike approved",
            canonical_url="https://reuters.com/fed-25bps",
            published_at="2026-10-18T14:00:00Z",
        )

        # Ingest same article again in next polling cycle
        id2 = self.db.insert_signal(
            headline="Federal Reserve raises benchmark rate by 25 bps",
            publisher="Reuters",
            decider_sentiment="Bullish",
            decider_confidence=0.92,
            policy_action="APPROVE",
            policy_reason="Rate hike approved",
            canonical_url="https://reuters.com/fed-25bps?utm_source=rss",
            published_at="2026-10-18T14:00:00Z",
        )

        self.assertEqual(id1, id2)

        # Database should still contain exactly 1 signal
        with self.db._get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
            self.assertEqual(count, 1)

    def test_merge_affected_instruments_upgrades_priority(self):
        existing_json = '[{"symbol": "EUR/USD", "relationship": "indirect", "confidence": 0.80, "reason": "Monetary transmission."}]'
        new_instruments = [
            {"symbol": "EUR/USD", "relationship": "direct", "confidence": 0.95, "reason": "Explicit mention in FOMC minutes.", "mentioned_explicitly": True},
            {"symbol": "USD/JPY", "relationship": "indirect", "confidence": 0.85, "reason": "Bilateral rate differential."},
        ]

        merged = self.db.merge_affected_instruments(existing_json, new_instruments)
        self.assertEqual(len(merged), 2)

        eur_usd = next(m for m in merged if m["symbol"] == "EUR/USD")
        self.assertEqual(eur_usd["relationship"], "direct")
        self.assertEqual(eur_usd["confidence"], 0.95)
        self.assertTrue(eur_usd["mentioned_explicitly"])

    def test_merge_affected_instruments_groups_duplicate_relationships(self):
        # When one article has multiple relationship records for same instrument
        existing_json = '[{"symbol": "EUR/USD", "relationship": "indirect", "confidence": 0.85, "reason": "Rate spread"}]'
        new_instruments = [
            {"symbol": "EUR/USD", "relationship": "potential", "confidence": 0.70, "reason": "Uncertain capital flow"},
        ]
        merged = self.db.merge_affected_instruments(existing_json, new_instruments)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["relationship"], "indirect")  # indirect > potential

