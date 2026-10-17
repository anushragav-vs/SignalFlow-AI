"""
SignalFlow AI - Real RSS Feed Ingestion & Deduplication Module
Fetches, normalizes, and deduplicates real financial news articles from multiple RSS feeds.
"""

import re
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict

import feedparser

from config import config


@dataclass
class NormalizedArticle:
    headline: str
    normalized_headline: str
    canonical_url: str
    publisher: str
    description: str
    published_at: str
    dedup_hash: str
    is_live: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RSSIngestionService:
    """
    Manages live financial news feeds with canonical URL and headline deduplication.
    """

    def __init__(self, feeds: Optional[Dict[str, str]] = None):
        self.feeds: Dict[str, str] = feeds.copy() if feeds else config.rss_feeds.copy()
        if "Yahoo Finance Top Stories" not in self.feeds and "Yahoo Finance Markets" in self.feeds:
            self.feeds["Yahoo Finance Top Stories"] = self.feeds["Yahoo Finance Markets"]
        self._seen_hashes: Set[str] = set()

    def add_feed(self, name: str, url: str):
        self.feeds[name] = url.strip()

    def remove_feed(self, name: str):
        if name in self.feeds:
            del self.feeds[name]

    def get_feeds(self) -> Dict[str, str]:
        return self.feeds.copy()

    @staticmethod
    def normalize_headline(text: str) -> str:
        """
        Strips whitespace, symbols, and casing to create comparable string for deduplication.
        """
        clean = re.sub(r"[^\w\s]", "", text.lower())
        return " ".join(clean.split())

    @staticmethod
    def canonicalize_url(url: str) -> str:
        """
        Strips tracking parameters (utm_*, ref, etc.) from feed URLs.
        """
        if not url:
            return ""
        clean = url.split("?")[0].split("#")[0].strip().rstrip("/")
        return clean.lower()

    def compute_hash(self, headline: str, url: str) -> str:
        norm_h = self.normalize_headline(headline)
        can_url = self.canonicalize_url(url)
        content = f"{norm_h}|{can_url}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def is_financial_headline(headline: str, description: str = "") -> bool:
        """
        Determines whether an article is materially related to financial markets,
        economics, public companies, equities, or monetary policy.
        Filters out non-financial lifestyle, celebrity gossip, sports, recipes,
        and entertainment trivia.
        """
        text = f"{headline} {description}".lower()

        # Non-financial disqualifiers (drop immediately)
        disqualifiers = [
            r"\b(recipe|cocktail|diet|smoothie|skincare|dating|wardrobe|spotted in|met gala)\b",
            r"\b(box office|trailer|oscar|grammy|emmy|hollywood star|super bowl halftime)\b",
            r"\b(horoscope|astrology|zodiac|beauty routine|royal family|prince harry|meghan)\b",
            r"\b(nfl score|nba highlights|premier league|touchdown|grand slam|tennis match)\b",
            r"\b(celebrity chef|luxury watch gala|vacation destination|travel tips)\b",
            r"\b(best restaurants|fashion week|movie review|album review|actor buys)\b",
        ]
        for pattern in disqualifiers:
            if re.search(pattern, text):
                return False

        return True

    def fetch_feed(self, feed_name: str, max_items: int = 10) -> List[NormalizedArticle]:
        """
        Fetches and normalizes articles from a single named feed with fast timeout-guarded HTTP requests.
        """
        if feed_name in ("All Feeds", "All Sources", "All Live Feeds", "Multi-Stream"):
            return self.fetch_all_feeds(max_per_feed=max(2, max_items // 2))

        # Handle legacy alias
        if feed_name == "Yahoo Finance Top Stories" and "Yahoo Finance Top Stories" not in self.feeds:
            url = self.feeds.get("Yahoo Finance Markets")
        else:
            url = self.feeds.get(feed_name)

        if not url:
            # Match case-insensitively
            for k, v in self.feeds.items():
                if k.lower() == feed_name.lower():
                    url = v
                    feed_name = k
                    break
        if not url:
            return []

        try:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SignalFlowAI/2.0",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            }
            try:
                resp = requests.get(url, headers=headers, timeout=8)
                if resp.status_code == 200 and resp.content:
                    feed = feedparser.parse(resp.content)
                else:
                    feed = feedparser.parse(url, agent=headers["User-Agent"])
            except Exception:
                feed = feedparser.parse(url, agent=headers["User-Agent"])

            if getattr(feed, "bozo", 0) and not getattr(feed, "entries", None):
                # Bozo set and no entries indicates network or XML parsing failure
                return []

            articles = []
            for entry in getattr(feed, "entries", []):
                if len(articles) >= max_items:
                    break

                raw_title = getattr(entry, "title", "").strip()
                if not raw_title:
                    continue

                raw_desc = getattr(entry, "summary", getattr(entry, "description", "")).strip()

                # Filter out obvious non-financial noise
                if not self.is_financial_headline(raw_title, raw_desc):
                    continue

                raw_link = getattr(entry, "link", "").strip()
                pub_date = getattr(entry, "published", getattr(entry, "updated", datetime.now(timezone.utc).isoformat()))

                norm_h = self.normalize_headline(raw_title)
                can_u = self.canonicalize_url(raw_link)
                item_hash = self.compute_hash(raw_title, raw_link)

                # Skip duplicates seen in this session
                if item_hash in self._seen_hashes:
                    continue
                self._seen_hashes.add(item_hash)

                articles.append(NormalizedArticle(
                    headline=raw_title,
                    normalized_headline=norm_h,
                    canonical_url=can_u,
                    publisher=feed_name,
                    description=raw_desc[:300] if raw_desc else "",
                    published_at=str(pub_date),
                    dedup_hash=item_hash,
                    is_live=True,
                ))

            return articles

        except Exception:
            return []

    def fetch_all_feeds(self, max_per_feed: int = 5) -> List[NormalizedArticle]:
        """
        Fetches from all configured feeds and merges deduplicated articles.
        """
        all_articles = []
        for name in list(self.feeds.keys()):
            # Skip duplicate aliases
            if name == "Yahoo Finance Top Stories" and "Yahoo Finance Markets" in self.feeds:
                continue
            items = self.fetch_feed(name, max_items=max_per_feed)
            all_articles.extend(items)
        return all_articles

    def normalize_manual_input(self, headline: str, publisher: str = "Manual Input") -> NormalizedArticle:
        norm_h = self.normalize_headline(headline)
        item_hash = self.compute_hash(headline, "manual-input")
        return NormalizedArticle(
            headline=headline.strip(),
            normalized_headline=norm_h,
            canonical_url="manual://direct-input",
            publisher=publisher,
            description="Submitted via manual input field.",
            published_at=datetime.now(timezone.utc).isoformat(),
            dedup_hash=item_hash,
            is_live=False,
        )
