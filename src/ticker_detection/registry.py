"""
SignalFlow AI - Supported Forex Instruments Registry
Defines the configurable universe of supported forex currency pairs and commodities,
their base/quote currency decomposition, and symbol normalization helpers.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass(frozen=True)
class InstrumentDefinition:
    symbol: str  # Standard format e.g. "EUR/USD"
    base_currency: str  # e.g. "EUR"
    quote_currency: str  # e.g. "USD"
    name: str  # e.g. "Euro / US Dollar"
    category: str  # "major", "cross", "commodity_metal"
    pip_decimal: int = 4
    is_active: bool = True
    aliases: List[str] = field(default_factory=list)


# Supported instruments registry as defined in Part 2.1
DEFAULT_SUPPORTED_INSTRUMENTS: Dict[str, InstrumentDefinition] = {
    "EUR/USD": InstrumentDefinition(
        symbol="EUR/USD",
        base_currency="EUR",
        quote_currency="USD",
        name="Euro / US Dollar",
        category="major",
        pip_decimal=4,
        aliases=["EURUSD", "EUR/USD", "Euro Dollar", "Euro versus US Dollar", "EUR-USD", "Fiber"],
    ),
    "GBP/USD": InstrumentDefinition(
        symbol="GBP/USD",
        base_currency="GBP",
        quote_currency="USD",
        name="British Pound / US Dollar",
        category="major",
        pip_decimal=4,
        aliases=["GBPUSD", "GBP/USD", "Cable", "Pound Dollar", "GBP-USD", "Sterling Dollar"],
    ),
    "USD/JPY": InstrumentDefinition(
        symbol="USD/JPY",
        base_currency="USD",
        quote_currency="JPY",
        name="US Dollar / Japanese Yen",
        category="major",
        pip_decimal=2,
        aliases=["USDJPY", "USD/JPY", "Dollar Yen", "USD-JPY", "Gopher"],
    ),
    "AUD/USD": InstrumentDefinition(
        symbol="AUD/USD",
        base_currency="AUD",
        quote_currency="USD",
        name="Australian Dollar / US Dollar",
        category="major",
        pip_decimal=4,
        aliases=["AUDUSD", "AUD/USD", "Aussie Dollar", "Aussie", "AUD-USD"],
    ),
    "USD/CAD": InstrumentDefinition(
        symbol="USD/CAD",
        base_currency="USD",
        quote_currency="CAD",
        name="US Dollar / Canadian Dollar",
        category="major",
        pip_decimal=4,
        aliases=["USDCAD", "USD/CAD", "Dollar Loonie", "Loonie", "USD-CAD"],
    ),
    "USD/CHF": InstrumentDefinition(
        symbol="USD/CHF",
        base_currency="USD",
        quote_currency="CHF",
        name="US Dollar / Swiss Franc",
        category="major",
        pip_decimal=4,
        aliases=["USDCHF", "USD/CHF", "Dollar Swiss", "Swissie", "USD-CHF"],
    ),
    "NZD/USD": InstrumentDefinition(
        symbol="NZD/USD",
        base_currency="NZD",
        quote_currency="USD",
        name="New Zealand Dollar / US Dollar",
        category="major",
        pip_decimal=4,
        aliases=["NZDUSD", "NZD/USD", "Kiwi Dollar", "Kiwi", "NZD-USD"],
    ),
    "EUR/GBP": InstrumentDefinition(
        symbol="EUR/GBP",
        base_currency="EUR",
        quote_currency="GBP",
        name="Euro / British Pound",
        category="cross",
        pip_decimal=4,
        aliases=["EURGBP", "EUR/GBP", "Euro Sterling", "EUR-GBP", "Chunnel"],
    ),
    "EUR/JPY": InstrumentDefinition(
        symbol="EUR/JPY",
        base_currency="EUR",
        quote_currency="JPY",
        name="Euro / Japanese Yen",
        category="cross",
        pip_decimal=2,
        aliases=["EURJPY", "EUR/JPY", "Euro Yen", "EUR-JPY", "Eppy"],
    ),
    "GBP/JPY": InstrumentDefinition(
        symbol="GBP/JPY",
        base_currency="GBP",
        quote_currency="JPY",
        name="British Pound / Japanese Yen",
        category="cross",
        pip_decimal=2,
        aliases=["GBPJPY", "GBP/JPY", "Pound Yen", "GBP-JPY", "Guppy", "Geppy"],
    ),
    "AUD/JPY": InstrumentDefinition(
        symbol="AUD/JPY",
        base_currency="AUD",
        quote_currency="JPY",
        name="Australian Dollar / Japanese Yen",
        category="cross",
        pip_decimal=2,
        aliases=["AUDJPY", "AUD/JPY", "Aussie Yen", "AUD-JPY"],
    ),
    "XAU/USD": InstrumentDefinition(
        symbol="XAU/USD",
        base_currency="XAU",
        quote_currency="USD",
        name="Gold / US Dollar",
        category="commodity_metal",
        pip_decimal=2,
        aliases=["XAUUSD", "XAU/USD", "Gold Dollar", "Spot Gold", "Gold Spot", "XAU-USD"],
    ),
}


class InstrumentRegistry:
    """
    Configurable registry for supported forex instruments and related commodities.
    Enforces validation against unsupported or fabricated symbols.
    """

    def __init__(self, instruments: Optional[Dict[str, InstrumentDefinition]] = None):
        self._registry: Dict[str, InstrumentDefinition] = (
            instruments.copy() if instruments else DEFAULT_SUPPORTED_INSTRUMENTS.copy()
        )
        self._symbol_lookup: Dict[str, str] = {}
        self._build_lookup_cache()

    def _build_lookup_cache(self):
        self._symbol_lookup.clear()
        for canonical, item in self._registry.items():
            if not item.is_active:
                continue
            # Self and normalized
            clean_canonical = canonical.upper().replace(" ", "")
            self._symbol_lookup[clean_canonical] = canonical
            self._symbol_lookup[clean_canonical.replace("/", "")] = canonical
            self._symbol_lookup[clean_canonical.replace("/", "-")] = canonical

            for alias in item.aliases:
                clean_alias = alias.upper().strip()
                self._symbol_lookup[clean_alias] = canonical
                self._symbol_lookup[clean_alias.replace(" ", "")] = canonical
                self._symbol_lookup[clean_alias.replace("/", "")] = canonical
                self._symbol_lookup[clean_alias.replace("-", "")] = canonical

    def is_supported(self, symbol: str) -> bool:
        """Check if a symbol (or alias) is supported by the registry."""
        if not symbol:
            return False
        clean = symbol.upper().strip()
        return clean in self._symbol_lookup or symbol in self._registry

    def normalize_symbol(self, symbol: str) -> Optional[str]:
        """
        Normalizes any supported alias or variant (e.g. 'EURUSD', 'Cable', 'euro dollar')
        to canonical registry format ('EUR/USD'). Returns None if unsupported.
        """
        if not symbol:
            return None
        clean = symbol.upper().strip()
        if clean in self._symbol_lookup:
            return self._symbol_lookup[clean]
        clean_no_slash = clean.replace("/", "").replace("-", "").replace(" ", "")
        if clean_no_slash in self._symbol_lookup:
            return self._symbol_lookup[clean_no_slash]
        return None

    def get_instrument(self, canonical_symbol: str) -> Optional[InstrumentDefinition]:
        return self._registry.get(canonical_symbol)

    def get_all_supported_symbols(self) -> List[str]:
        return [sym for sym, item in self._registry.items() if item.is_active]

    def get_instruments_for_currency(self, currency_code: str) -> List[InstrumentDefinition]:
        """Returns all registered pairs containing the specified currency code."""
        code = currency_code.upper().strip()
        return [
            inst for inst in self._registry.values()
            if inst.is_active and (inst.base_currency == code or inst.quote_currency == code)
        ]

    def register_instrument(self, definition: InstrumentDefinition):
        """Allows dynamically registering or updating an instrument configuration."""
        self._registry[definition.symbol] = definition
        self._build_lookup_cache()

    def unregister_instrument(self, symbol: str):
        if symbol in self._registry:
            del self._registry[symbol]
            self._build_lookup_cache()


# Default singleton instance
instrument_registry = InstrumentRegistry()

