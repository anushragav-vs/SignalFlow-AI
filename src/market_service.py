"""
SignalFlow AI - Real-Time Market Ticker & Instrument Service
Provides live market quotes, daily price variations, sparkline metrics,
and mapping between news headline entities and exchange-traded symbols.
"""

import time
import re
import logging
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)

# Standard mapping from human names / headline terms to exchange tickers
SYMBOL_ALIASES = {
    "^ixic": "^IXIC",
    "^gspc": "^GSPC",
    "^dji": "^DJI",
    "cl=f": "CL=F",
    "nasdaq": "^IXIC",
    "nasdaq composite": "^IXIC",
    "nasdaq 100": "^IXIC",
    "technology sector equities": "^IXIC",
    "ai-related stocks": "NVDA",
    "s&p 500": "^GSPC",
    "s&p": "^GSPC",
    "sp500": "^GSPC",
    "dow jones": "^DJI",
    "dow": "^DJI",
    "djia": "^DJI",
    "oil": "CL=F",
    "crude oil": "CL=F",
    "wti": "CL=F",
    "brent": "BZ=F",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "berkshire": "BRK-B",
    "citigroup": "C",
    "mastercard": "MA",
    "bitcoin": "BTC-USD",
    "btc": "BTC-USD",
}

DEFAULT_TOP_TICKERS = [
    {"symbol": "^IXIC", "label": "NASDAQ", "category": "INDEX"},
    {"symbol": "^GSPC", "label": "S&P 500", "category": "INDEX"},
    {"symbol": "^DJI", "label": "DOW JONES", "category": "INDEX"},
    {"symbol": "NVDA", "label": "NVDA", "category": "EQUITY"},
    {"symbol": "TSLA", "label": "TSLA", "category": "EQUITY"},
    {"symbol": "AAPL", "label": "AAPL", "category": "EQUITY"},
    {"symbol": "MSFT", "label": "MSFT", "category": "EQUITY"},
    {"symbol": "CL=F", "label": "CRUDE OIL", "category": "COMMODITY"},
]

# Baseline fallback data in case external quote network is offline
FALLBACK_QUOTES = {
    "^IXIC": {"price": 26140.03, "change_pct": -2.14, "name": "NASDAQ Composite", "prev": 26713.03},
    "^GSPC": {"price": 5780.20, "change_pct": -1.09, "name": "S&P 500 Index", "prev": 5843.89},
    "^DJI": {"price": 42800.50, "change_pct": -0.34, "name": "Dow Jones Industrial Average", "prev": 42946.75},
    "NVDA": {"price": 214.13, "change_pct": -6.61, "name": "NVIDIA Corporation", "prev": 229.28},
    "TSLA": {"price": 218.60, "change_pct": -2.15, "name": "Tesla, Inc.", "prev": 223.40},
    "AAPL": {"price": 235.10, "change_pct": +0.43, "name": "Apple Inc.", "prev": 234.09},
    "MSFT": {"price": 418.50, "change_pct": -1.93, "name": "Microsoft Corporation", "prev": 426.73},
    "CL=F": {"price": 78.45, "change_pct": +2.61, "name": "Crude Oil Futures", "prev": 76.45},
}


class MarketTickerService:
    """
    Fetches, caches, and normalizes live market quotes from Yahoo Finance.
    Provides sub-second cached responses for the UI ribbon and detail modal.
    """

    def __init__(self, cache_ttl_sec: int = 30):
        self.cache_ttl_sec = cache_ttl_sec
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_time: Dict[str, float] = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SignalFlowAI/2.0"
        }

    def resolve_symbol(self, query: str) -> str:
        """Resolves a company name, index name, or asset mention to a standard ticker."""
        if not query:
            return "^IXIC"
        cleaned = query.strip().lower()
        if cleaned in SYMBOL_ALIASES:
            return SYMBOL_ALIASES[cleaned]
        no_dollar = cleaned.replace("$", "").strip()
        if no_dollar in SYMBOL_ALIASES:
            return SYMBOL_ALIASES[no_dollar]
        if query.startswith("^"):
            return query.upper().strip()
        if "=" in query:
            return query.upper().strip()
        match = re.search(r"\b([A-Z]{1,5})\b", query.upper())
        if match:
            return match.group(1)
        return query.upper().strip()

    def fetch_live_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetches live market quote for a single symbol with caching."""
        sym = self.resolve_symbol(symbol)
        now = time.time()

        if sym in self._cache and (now - self._cache_time.get(sym, 0)) < self.cache_ttl_sec:
            return self._cache[sym]

        try:
            import urllib.parse
            safe_sym = urllib.parse.quote(sym, safe="")
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{safe_sym}?interval=1d&range=5d"
            resp = requests.get(url, headers=self.headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                res = data.get("chart", {}).get("result", [])
                if res:
                    meta = res[0].get("meta", {})
                    indicators = res[0].get("indicators", {}).get("quote", [{}])[0]
                    raw_closes = indicators.get("close", [])
                    clean_closes = [round(float(c), 2) for c in raw_closes if c is not None]

                    price = meta.get("regularMarketPrice") or (clean_closes[-1] if clean_closes else 100.0)
                    prev = meta.get("chartPreviousClose") or meta.get("previousClose") or price
                    chg_pct = round(((price - prev) / prev * 100.0), 2) if prev else 0.0
                    chg_abs = round(price - prev, 2) if prev else 0.0

                    quote_data = {
                        "symbol": sym,
                        "display_symbol": sym.replace("^", ""),
                        "name": meta.get("shortName") or meta.get("longName") or sym,
                        "price": round(float(price), 2),
                        "prev_close": round(float(prev), 2),
                        "change_abs": chg_abs,
                        "change_pct": chg_pct,
                        "is_positive": chg_pct >= 0,
                        "day_high": meta.get("regularMarketDayHigh"),
                        "day_low": meta.get("regularMarketDayLow"),
                        "year_high": meta.get("fiftyTwoWeekHigh"),
                        "year_low": meta.get("fiftyTwoWeekLow"),
                        "volume": meta.get("regularMarketVolume"),
                        "currency": meta.get("currency", "USD"),
                        "exchange": meta.get("exchangeName", "US"),
                        "sparkline": clean_closes[-5:] if clean_closes else [price],
                        "updated_at": time.strftime("%H:%M:%S UTC", time.gmtime()),
                        "is_live": True,
                    }
                    self._cache[sym] = quote_data
                    self._cache_time[sym] = now
                    return quote_data
        except Exception as e:
            logger.debug(f"Failed to fetch live quote for {sym}: {e}")

        # Fallback to realistic cached data
        fallback = FALLBACK_QUOTES.get(sym, {
            "price": 100.0,
            "change_pct": 0.0,
            "name": sym,
            "prev": 100.0,
        })
        quote_data = {
            "symbol": sym,
            "display_symbol": sym.replace("^", ""),
            "name": fallback.get("name", sym),
            "price": fallback["price"],
            "prev_close": fallback.get("prev", fallback["price"]),
            "change_abs": round(fallback["price"] * (fallback["change_pct"] / 100), 2),
            "change_pct": fallback["change_pct"],
            "is_positive": fallback["change_pct"] >= 0,
            "day_high": round(fallback["price"] * 1.015, 2),
            "day_low": round(fallback["price"] * 0.985, 2),
            "year_high": round(fallback["price"] * 1.25, 2),
            "year_low": round(fallback["price"] * 0.75, 2),
            "volume": 25000000,
            "currency": "USD",
            "exchange": "US",
            "sparkline": [
                round(fallback["price"] * (1 + (i - 2) * 0.005), 2) for i in range(5)
            ],
            "updated_at": time.strftime("%H:%M:%S UTC", time.gmtime()),
            "is_live": False,
        }
        self._cache[sym] = quote_data
        self._cache_time[sym] = now
        return quote_data

    def get_top_market_tickers(self) -> List[Dict[str, Any]]:
        """Returns live quotes for top macro index and equity tickers."""
        results = []
        for item in DEFAULT_TOP_TICKERS:
            q = self.fetch_live_quote(item["symbol"])
            # Format display label
            card = dict(q)
            card["label"] = item["label"]
            card["category"] = item["category"]
            results.append(card)
        return results
