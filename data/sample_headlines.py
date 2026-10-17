"""
SignalFlow AI - Sample Headlines & Benchmark Fixtures
"""

import json
import os
from typing import List, Dict, Any, Optional

DATA_FILE = os.path.join(os.path.dirname(__file__), "sample_headlines.json")


def load_sample_headlines() -> List[Dict[str, Any]]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def get_sample_headline_match(headline: str) -> Optional[Dict[str, Any]]:
    headlines = load_sample_headlines()
    h_clean = headline.strip().lower()
    for item in headlines:
        if item.get("headline", "").strip().lower() == h_clean:
            return item
    return None
