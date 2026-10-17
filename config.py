"""
SignalFlow AI - Centralized Application Configuration
Provides strongly-typed, environment-aware configuration across local and cloud services.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

FINANCIAL_DISCLAIMER = (
    "Research and educational purposes only. This is not financial advice or an automated trading system. "
    "SignalFlow AI does not execute trades or provide guaranteed returns."
)

DEFAULT_RSS_FEEDS = {
    "Yahoo Finance Markets": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC",
    "Yahoo Finance Tech Stocks": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=NVDA,AAPL,MSFT,TSLA,GOOGL",
    "Yahoo Finance Top Stories": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC",
    "CNBC Market News": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "MarketWatch Top Stories": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "Wall Street Journal Markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
}


@dataclass
class AppConfig:
    # Local System One Decision Engine
    decider_checkpoint: str = os.environ.get(
        "STRANDS_DECIDER_CHECKPOINT",
        "StrandsAgents/strands-decider-2B-qwen3.5-v1-2610"
    )
    decider_server_url: str = os.environ.get(
        "STRANDS_DECIDER_SERVER_URL",
        "http://localhost:8000/ask"
    )
    decider_device: str = os.environ.get("STRANDS_DEVICE", "cpu")

    # Policy Routing Thresholds
    min_confidence_threshold: float = float(
        os.environ.get("MIN_CONFIDENCE_THRESHOLD", "0.80")
    )

    # System Two Google AI Studio Cloud Analysis
    gemini_api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")
    gemini_model_id: str = os.environ.get("GEMINI_MODEL_ID", "gemini-3.5-flash-lite")
    gemini_timeout_sec: int = int(os.environ.get("GEMINI_TIMEOUT_SEC", "30"))

    # Persistence
    sqlite_db_path: str = os.environ.get("SQLITE_DB_PATH", "signalflow.db")

    # RSS Configuration
    rss_feeds: Dict[str, str] = field(default_factory=lambda: DEFAULT_RSS_FEEDS.copy())
    max_items_per_feed: int = int(os.environ.get("MAX_ITEMS_PER_FEED", "10"))

    # Disclaimers & Tags
    disclaimer: str = FINANCIAL_DISCLAIMER
    project_tags: List[str] = field(
        default_factory=lambda: ["#strands-decider-2b", "#policy", "#google-gemini", "#fintech"]
    )

    def is_gemini_configured(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.strip())

    def get_masked_api_key(self) -> str:
        """
        Returns masked representation of API key for health check display.
        Never reveals the full key.
        """
        if not self.gemini_api_key or not self.gemini_api_key.strip():
            return "NOT_CONFIGURED"
        k = self.gemini_api_key.strip()
        if len(k) <= 8:
            return "********"
        return f"{k[:4]}...{k[-4:]} ({len(k)} chars)"


config = AppConfig()
