"""
Tests for RSS Ingestion, Normalization, and Deduplication
"""

import unittest
from src.rss_service import RSSIngestionService, NormalizedArticle


class TestRSSIngestion(unittest.TestCase):
    def setUp(self):
        self.service = RSSIngestionService(feeds={"TestFeed": "https://invalid.fake.url/rss"})

    def test_headline_normalization(self):
        h1 = "Tesla Q3 Earnings: Margins Surge to 19.8%!!"
        h2 = "tesla q3 earnings margins surge to 198"
        norm1 = self.service.normalize_headline(h1)
        norm2 = self.service.normalize_headline(h2)
        self.assertEqual(norm1, norm2)

    def test_canonicalize_url(self):
        u1 = "https://finance.yahoo.com/news/article.html?utm_source=twitter&ref=stocktwits"
        u2 = "https://finance.yahoo.com/news/article.html"
        self.assertEqual(self.service.canonicalize_url(u1), self.service.canonicalize_url(u2))

    def test_deduplication_hash(self):
        h = "NVIDIA signs APAC contract"
        u = "https://cnbc.com/article?id=123"
        hash1 = self.service.compute_hash(h, u)
        hash2 = self.service.compute_hash(h.upper(), u.split("?")[0])
        self.assertEqual(hash1, hash2)

    def test_manual_input_normalization(self):
        art = self.service.normalize_manual_input("Apple unveils M4 chip architecture")
        self.assertIsInstance(art, NormalizedArticle)
        self.assertEqual(art.headline, "Apple unveils M4 chip architecture")
        self.assertFalse(art.is_live)
        self.assertEqual(art.publisher, "Manual Input")

    def test_feed_management(self):
        self.service.add_feed("NewFeed", "https://newfeed.com/rss")
        self.assertIn("NewFeed", self.service.get_feeds())
        self.service.remove_feed("NewFeed")
        self.assertNotIn("NewFeed", self.service.get_feeds())


if __name__ == "__main__":
    unittest.main()
