"""
SignalFlow AI - Centralized News Article Deduplication & Identity Engine
Implements strict 3-tier identity priority:
  Tier 1: Original provider article ID (when available)
  Tier 2: Canonicalized original article URL (when available)
  Tier 3: Fallback fingerprint (normalized headline + source/publisher + publication date)
"""

import re
import hashlib
from typing import Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime, timezone


def normalize_headline(text: str) -> str:
    """
    Normalizes news headline by trimming whitespace, lowercasing,
    collapsing multiple spaces, and removing punctuation differences.
    """
    if not text:
        return ""

    # Normalize unicode quotation marks, dashes, and ellipses
    t = (
        text.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("—", "-")
        .replace("–", "-")
        .replace("−", "-")
        .replace("…", "...")
    )

    # Convert to lowercase
    t = t.lower()

    # Remove all punctuation except alphanumeric and spaces
    clean = re.sub(r"[^\w\s]", "", t)

    # Collapse multiple whitespace characters into single space
    return " ".join(clean.split()).strip()


def canonicalize_url(url: str) -> str:
    """
    Strips query parameters (tracking, sessions, ids) and fragments from URLs,
    normalizing scheme and host to lowercase and stripping trailing slashes.
    """
    if not url or not isinstance(url, str):
        return ""

    url_str = url.strip()
    if not url_str or url_str.startswith("manual://"):
        return url_str

    clean = url_str.split("?")[0].split("#")[0].strip().rstrip("/")
    return clean.lower()


def extract_published_date(published_at: Optional[str]) -> str:
    """
    Extracts standard YYYY-MM-DD date string from date strings to prevent
    minor timestamp or timezone differences from splitting the same article.
    """
    if not published_at or not isinstance(published_at, str):
        return ""

    s = published_at.strip()
    # Try ISO date match YYYY-MM-DD
    match = re.search(r"(\d{4}-\d{2}-\d{2})", s)
    if match:
        return match.group(1)

    # Try common RSS date formats e.g. "Mon, 18 Oct 2026 12:00:00"
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(s)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return s[:10]


def compute_article_fingerprint(
    provider_article_id: Optional[str] = None,
    canonical_url: Optional[str] = None,
    headline: str = "",
    publisher: str = "",
    published_at: Optional[str] = None,
) -> str:
    """
    Computes a deterministic SHA-256 identity fingerprint following priority:
    1. Provider article ID (when valid and non-generic)
    2. Canonical URL (when valid http/https)
    3. Fallback: Normalized Headline + Publisher + Publication Date (YYYY-MM-DD)
    """
    # Priority 1: Provider Article ID
    if provider_article_id and isinstance(provider_article_id, str):
        pid = provider_article_id.strip()
        # Ensure it's not a generic placeholder
        if pid and pid not in ("manual-input", "none", "null", "undefined"):
            content = f"PID:{pid}"
            return hashlib.sha256(content.encode("utf-8")).hexdigest()

    # Priority 2: Canonical URL
    can_url = canonicalize_url(canonical_url or "")
    if can_url and can_url.startswith(("http://", "https://")):
        content = f"URL:{can_url}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    # Priority 3: Normalized Headline + Publisher + Date
    norm_h = normalize_headline(headline)
    norm_pub = (publisher or "unknown").strip().lower()
    date_str = extract_published_date(published_at)

    content = f"FALLBACK:{norm_pub}|{date_str}|{norm_h}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
