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
    "ixic": "^IXIC",
    "gspc": "^GSPC",
    "dji": "^DJI",
    "nasdaq": "^IXIC",
    "nasdaq composite": "^IXIC",
    "nasdaq 100": "^IXIC",
    "ndx": "^IXIC",
    "technology sector equities": "^IXIC",
    "ai-related stocks": "NVDA",
    "s&p 500": "^GSPC",
    "s&p500": "^GSPC",
    "s&p": "^GSPC",
    "sp500": "^GSPC",
    "spx": "^GSPC",
    "dow jones": "^DJI",
    "dow": "^DJI",
    "djia": "^DJI",
    "oil": "CL=F",
    "crude oil": "CL=F",
    "cl": "CL=F",
    "wti": "CL=F",
    "brent": "BZ=F",
    "nvidia": "NVDA",
    "nvda": "NVDA",
    "tesla": "TSLA",
    "tsla": "TSLA",
    "apple": "AAPL",
    "aapl": "AAPL",
    "microsoft": "MSFT",
    "msft": "MSFT",
    "google": "GOOGL",
    "goog": "GOOGL",
    "googl": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "amzn": "AMZN",
    "meta": "META",
    "berkshire": "BRK-B",
    "citigroup": "C",
    "mastercard": "MA",
    "bitcoin": "BTC-USD",
    "btc": "BTC-USD",
    # Major Forex Pairs & Commodities
    "eur/usd": "EURUSD=X",
    "eurusd": "EURUSD=X",
    "gbp/usd": "GBPUSD=X",
    "gbpusd": "GBPUSD=X",
    "cable": "GBPUSD=X",
    "fiber": "EURUSD=X",
    "usd/jpy": "USDJPY=X",
    "usdjpy": "USDJPY=X",
    "aud/usd": "AUDUSD=X",
    "audusd": "AUDUSD=X",
    "usd/cad": "USDCAD=X",
    "usdcad": "USDCAD=X",
    "usd/chf": "USDCHF=X",
    "usdchf": "USDCHF=X",
    "nzd/usd": "NZDUSD=X",
    "nzdusd": "NZDUSD=X",
    "eur/gbp": "EURGBP=X",
    "eurgbp": "EURGBP=X",
    "eur/jpy": "EURJPY=X",
    "eurjpy": "EURJPY=X",
    "gbp/jpy": "GBPJPY=X",
    "gbpjpy": "GBPJPY=X",
    "aud/jpy": "AUDJPY=X",
    "audjpy": "AUDJPY=X",
    "xau/usd": "GC=F",
    "xauusd": "GC=F",
    "gold": "GC=F",
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

# Baseline fallback data in case external quote network is offline or unquoted
FALLBACK_QUOTES = {
    "^IXIC": {"price": 26140.03, "change_pct": -2.14, "name": "NASDAQ Composite", "prev": 26713.03, "label": "NASDAQ", "category": "INDEX", "exchange": "NIM"},
    "IXIC": {"price": 26140.03, "change_pct": -2.14, "name": "NASDAQ Composite", "prev": 26713.03, "label": "NASDAQ", "category": "INDEX", "exchange": "NIM"},
    "^GSPC": {"price": 7659.44, "change_pct": -1.09, "name": "S&P 500 Index", "prev": 7743.89, "label": "S&P 500", "category": "INDEX", "exchange": "SNP"},
    "GSPC": {"price": 7659.44, "change_pct": -1.09, "name": "S&P 500 Index", "prev": 7743.89, "label": "S&P 500", "category": "INDEX", "exchange": "SNP"},
    "^DJI": {"price": 52002.41, "change_pct": 0.67, "name": "Dow Jones Industrial Average", "prev": 51654.95, "label": "DOW JONES", "category": "INDEX", "exchange": "DJI"},
    "DJI": {"price": 52002.41, "change_pct": 0.67, "name": "Dow Jones Industrial Average", "prev": 51654.95, "label": "DOW JONES", "category": "INDEX", "exchange": "DJI"},
    "NVDA": {"price": 214.13, "change_pct": -6.61, "name": "NVIDIA Corporation", "prev": 229.28, "label": "NVDA", "category": "EQUITY", "exchange": "NMS"},
    "TSLA": {"price": 354.72, "change_pct": -7.31, "name": "Tesla, Inc.", "prev": 382.70, "label": "TSLA", "category": "EQUITY", "exchange": "NMS"},
    "AAPL": {"price": 343.46, "change_pct": 2.03, "name": "Apple Inc.", "prev": 336.64, "label": "AAPL", "category": "EQUITY", "exchange": "NMS"},
    "MSFT": {"price": 529.05, "change_pct": -1.13, "name": "Microsoft Corporation", "prev": 535.07, "label": "MSFT", "category": "EQUITY", "exchange": "NMS"},
    "CL=F": {"price": 99.02, "change_pct": 5.18, "name": "Crude Oil Futures", "prev": 94.14, "label": "CRUDE OIL", "category": "COMMODITY", "exchange": "NYM"},
    "CL": {"price": 99.02, "change_pct": 5.18, "name": "Crude Oil Futures", "prev": 94.14, "label": "CRUDE OIL", "category": "COMMODITY", "exchange": "NYM"},
    # Institutional Forex & Metal Fallbacks
    "EURUSD=X": {"price": 1.0850, "change_pct": 0.23, "name": "Euro / US Dollar", "prev": 1.0825, "label": "EUR/USD", "category": "FOREX", "exchange": "CCY"},
    "GBPUSD=X": {"price": 1.2980, "change_pct": 0.23, "name": "British Pound / US Dollar", "prev": 1.2950, "label": "GBP/USD", "category": "FOREX", "exchange": "CCY"},
    "USDJPY=X": {"price": 153.40, "change_pct": 0.33, "name": "US Dollar / Japanese Yen", "prev": 152.90, "label": "USD/JPY", "category": "FOREX", "exchange": "CCY"},
    "AUDUSD=X": {"price": 0.6590, "change_pct": 0.23, "name": "Australian Dollar / US Dollar", "prev": 0.6575, "label": "AUD/USD", "category": "FOREX", "exchange": "CCY"},
    "USDCAD=X": {"price": 1.3880, "change_pct": 0.14, "name": "US Dollar / Canadian Dollar", "prev": 1.3860, "label": "USD/CAD", "category": "FOREX", "exchange": "CCY"},
    "USDCHF=X": {"price": 0.8670, "change_pct": 0.17, "name": "US Dollar / Swiss Franc", "prev": 0.8655, "label": "USD/CHF", "category": "FOREX", "exchange": "CCY"},
    "NZDUSD=X": {"price": 0.5980, "change_pct": 0.34, "name": "New Zealand Dollar / US Dollar", "prev": 0.5960, "label": "NZD/USD", "category": "FOREX", "exchange": "CCY"},
    "EURGBP=X": {"price": 0.8355, "change_pct": 0.18, "name": "Euro / British Pound", "prev": 0.8340, "label": "EUR/GBP", "category": "FOREX", "exchange": "CCY"},
    "EURJPY=X": {"price": 166.45, "change_pct": 0.33, "name": "Euro / Japanese Yen", "prev": 165.90, "label": "EUR/JPY", "category": "FOREX", "exchange": "CCY"},
    "GBPJPY=X": {"price": 199.10, "change_pct": 0.35, "name": "British Pound / Japanese Yen", "prev": 198.40, "label": "GBP/JPY", "category": "FOREX", "exchange": "CCY"},
    "AUDJPY=X": {"price": 101.10, "change_pct": 0.35, "name": "Australian Dollar / Japanese Yen", "prev": 100.75, "label": "AUD/JPY", "category": "FOREX", "exchange": "CCY"},
    "GC=F": {"price": 2748.50, "change_pct": 0.49, "name": "Gold (XAU/USD)", "prev": 2735.00, "label": "XAU/USD", "category": "COMMODITY", "exchange": "CMX"},
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
        if "/" in cleaned:
            unslashed = cleaned.replace("/", "")
            if unslashed in SYMBOL_ALIASES:
                return SYMBOL_ALIASES[unslashed]
            return f"{unslashed.upper()}=X"
        no_dollar = cleaned.replace("$", "").strip()
        if no_dollar in SYMBOL_ALIASES:
            return SYMBOL_ALIASES[no_dollar]
        no_hat = cleaned.replace("^", "").strip()
        if no_hat in SYMBOL_ALIASES:
            return SYMBOL_ALIASES[no_hat]
        if query.startswith("^"):
            return query.upper().strip()
        if "=" in query:
            return query.upper().strip()
        match = re.search(r"\b([A-Z0-9\^=]{1,8})\b", query.upper())
        if match:
            matched_sym = match.group(1).lower()
            if matched_sym in SYMBOL_ALIASES:
                return SYMBOL_ALIASES[matched_sym]
            return match.group(1)
        return query.upper().strip()

    def fetch_live_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetches live market quote for a single symbol with caching."""
        sym = self.resolve_symbol(symbol)
        now = time.time()

        if sym in self._cache and (now - self._cache_time.get(sym, 0)) < self.cache_ttl_sec:
            cached = self._cache[sym]
            # Avoid serving bad 100.0 placeholder from old cache
            if cached.get("price") != 100.0 or sym in ["100", "HUND"]:
                return cached

        # Resolve realistic fallback for this ticker
        fallback = FALLBACK_QUOTES.get(sym, FALLBACK_QUOTES.get(sym.replace("^", ""), {
            "price": 250.0,
            "change_pct": 0.50,
            "name": sym,
            "prev": 248.75,
            "label": sym.replace("^", ""),
            "category": "EQUITY",
            "exchange": "US",
        }))

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
                    clean_closes = [round(float(c), 2) for c in raw_closes if c is not None and float(c) > 0]

                    raw_price = meta.get("regularMarketPrice")
                    if raw_price is not None and float(raw_price) > 0:
                        price = float(raw_price)
                    elif clean_closes:
                        price = clean_closes[-1]
                    else:
                        price = float(fallback["price"])

                    prev_raw = meta.get("chartPreviousClose") or meta.get("previousClose")
                    if prev_raw is not None and float(prev_raw) > 0:
                        prev = float(prev_raw)
                    elif len(clean_closes) >= 2:
                        prev = clean_closes[-2]
                    else:
                        prev = float(fallback.get("prev", price))

                    chg_pct = round(((price - prev) / prev * 100.0), 2) if prev else 0.0
                    chg_abs = round(price - prev, 2) if prev else 0.0

                    day_high = meta.get("regularMarketDayHigh") or round(price * 1.012, 2)
                    day_low = meta.get("regularMarketDayLow") or round(price * 0.988, 2)
                    year_high = meta.get("fiftyTwoWeekHigh") or round(price * 1.25, 2)
                    year_low = meta.get("fiftyTwoWeekLow") or round(price * 0.75, 2)
                    volume = meta.get("regularMarketVolume") or 25000000

                    if len(clean_closes) >= 2:
                        sparkline = clean_closes[-5:]
                    else:
                        # Generate smooth 5-point sparkline based on trend
                        step = (price - prev) / 4.0 if prev else 0.0
                        sparkline = [round(prev + (step * i), 2) for i in range(5)]

                    display_symbol = fallback.get("label") or sym.replace("^", "")
                    name = meta.get("shortName") or meta.get("longName") or fallback.get("name", sym)

                    quote_data = {
                        "symbol": sym,
                        "display_symbol": display_symbol,
                        "label": fallback.get("label", display_symbol),
                        "category": fallback.get("category", "MARKET ASSET"),
                        "name": name,
                        "price": round(float(price), 2),
                        "prev_close": round(float(prev), 2),
                        "change_abs": chg_abs,
                        "change_pct": chg_pct,
                        "is_positive": chg_pct >= 0,
                        "day_high": round(float(day_high), 2),
                        "day_low": round(float(day_low), 2),
                        "year_high": round(float(year_high), 2),
                        "year_low": round(float(year_low), 2),
                        "volume": volume,
                        "currency": meta.get("currency", "USD"),
                        "exchange": meta.get("exchangeName", fallback.get("exchange", "US")),
                        "sparkline": sparkline,
                        "updated_at": time.strftime("%H:%M:%S UTC", time.gmtime()),
                        "is_live": True,
                    }
                    self._cache[sym] = quote_data
                    self._cache_time[sym] = now
                    return quote_data
        except Exception as e:
            logger.debug(f"Failed to fetch live quote for {sym}: {e}")

        # Fallback to realistic cached data
        fallback_price = float(fallback["price"])
        fallback_prev = float(fallback.get("prev", fallback_price))
        fallback_chg_pct = float(fallback.get("change_pct", 0.0))
        quote_data = {
            "symbol": sym,
            "display_symbol": fallback.get("label", sym.replace("^", "")),
            "label": fallback.get("label", sym.replace("^", "")),
            "category": fallback.get("category", "MARKET ASSET"),
            "name": fallback.get("name", sym),
            "price": fallback_price,
            "prev_close": fallback_prev,
            "change_abs": round(fallback_price * (fallback_chg_pct / 100), 2),
            "change_pct": fallback_chg_pct,
            "is_positive": fallback_chg_pct >= 0,
            "day_high": round(fallback_price * 1.015, 2),
            "day_low": round(fallback_price * 0.985, 2),
            "year_high": round(fallback_price * 1.25, 2),
            "year_low": round(fallback_price * 0.75, 2),
            "volume": 25000000,
            "currency": "USD",
            "exchange": fallback.get("exchange", "US"),
            "sparkline": [
                round(fallback_price * (1 + (i - 2) * 0.005), 2) for i in range(5)
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
