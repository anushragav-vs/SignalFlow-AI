"""
SignalFlow AI - Context-Aware Economic Relationship Engine
Evaluates macroeconomic transmission channels to classify currency pair relevance into:
- DIRECT: explicitly mentioned in the text.
- INDIRECT: defensible economic transmission relationship (e.g., central bank policy, major economic print).
- POTENTIAL: secondary spillover or uncertain correlation (e.g., gold safe haven, risk cross-spillover).
Strictly enforces supported registry validation and transparent economic reasoning.
"""

import logging
from typing import Dict, List, Set, Any, Optional

from src.ticker_detection.registry import instrument_registry, InstrumentRegistry
from src.ticker_detection.models import AffectedInstrument, RelationshipType

logger = logging.getLogger(__name__)

# Primary pairs for major currencies when high-impact central bank or macro event occurs
PRIMARY_CURRENCY_PAIRS: Dict[str, List[str]] = {
    "USD": ["EUR/USD", "GBP/USD", "USD/JPY"],
    "EUR": ["EUR/USD", "EUR/GBP", "EUR/JPY"],
    "GBP": ["GBP/USD", "EUR/GBP", "GBP/JPY"],
    "JPY": ["USD/JPY", "EUR/JPY", "GBP/JPY"],
    "AUD": ["AUD/USD", "AUD/JPY"],
    "CAD": ["USD/CAD"],
    "CHF": ["USD/CHF"],
    "NZD": ["NZD/USD"],
    "XAU": ["XAU/USD"],
}

# Secondary / spillover pairs
SECONDARY_CURRENCY_PAIRS: Dict[str, List[str]] = {
    "USD": ["USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD"],
    "EUR": [],
    "GBP": [],
    "JPY": ["AUD/JPY"],
    "AUD": [],
    "CAD": [],
    "CHF": [],
    "NZD": [],
    "XAU": [],
}


class EconomicRelationshipEngine:
    """
    Classifies relationship types (DIRECT, INDIRECT, POTENTIAL) and generates
    defensible economic justifications without implying guaranteed returns.
    """

    def __init__(self, registry: Optional[InstrumentRegistry] = None):
        self.registry = registry or instrument_registry

    def evaluate_relationships(
        self,
        text: str,
        match_result: Dict[str, Any],
    ) -> List[AffectedInstrument]:
        """
        Takes deterministic match results and constructs validated AffectedInstrument records.
        """
        explicit_instruments = set(match_result.get("explicit_instruments", []))
        detected_currencies = set(match_result.get("currencies", []))
        central_banks = match_result.get("central_banks", [])
        economic_events = set(match_result.get("economic_events", []))

        affected: List[AffectedInstrument] = []
        assigned_symbols: Set[str] = set()

        # 1. DIRECT: Explicitly mentioned instruments
        for sym in explicit_instruments:
            norm_sym = self.registry.normalize_symbol(sym)
            if not norm_sym:
                continue

            inst = self.registry.get_instrument(norm_sym)
            inst_name = inst.name if inst else norm_sym
            affected.append(
                AffectedInstrument(
                    symbol=norm_sym,
                    relationship="direct",
                    confidence=0.98,
                    reason=f"{inst_name} is explicitly identified and referenced in the report.",
                    mentioned_explicitly=True,
                )
            )
            assigned_symbols.add(norm_sym)

        # 2. INDIRECT: Central bank and major macro indicators transmission
        # If a central bank is detected, its primary currency drives clear indirect impact on primary pairs
        has_monetary_policy_event = any(
            ev in economic_events
            for ev in ("interest_rate_decision", "cpi_release", "ppi_release", "nfp_release", "gdp_release", "inflation_overview")
        )

        for cb in central_banks:
            cb_name = cb.get("name", "Central Bank")
            cb_currency = cb.get("currency", "")
            region = cb.get("region", "domestic")

            if not cb_currency or cb_currency not in PRIMARY_CURRENCY_PAIRS:
                continue

            for primary_sym in PRIMARY_CURRENCY_PAIRS[cb_currency]:
                if primary_sym in assigned_symbols:
                    continue  # Already direct
                if not self.registry.is_supported(primary_sym):
                    continue

                inst = self.registry.get_instrument(primary_sym)
                base = inst.base_currency if inst else "Base"
                quote = inst.quote_currency if inst else "Quote"

                confidence = 0.89 if has_monetary_policy_event else 0.82
                reason = (
                    f"Actions and policy guidance from the {cb_name} directly alter {cb_currency} "
                    f"yield expectations and capital flows relative to {quote if base == cb_currency else base}."
                )

                affected.append(
                    AffectedInstrument(
                        symbol=primary_sym,
                        relationship="indirect",
                        confidence=confidence,
                        reason=reason,
                        mentioned_explicitly=False,
                    )
                )
                assigned_symbols.add(primary_sym)

            # Gold (XAU/USD) is potentially affected by USD central bank policy
            if cb_currency == "USD" and "XAU/USD" not in assigned_symbols and self.registry.is_supported("XAU/USD"):
                affected.append(
                    AffectedInstrument(
                        symbol="XAU/USD",
                        relationship="potential",
                        confidence=0.74,
                        reason=(
                            f"US monetary policy decisions influence real yields and the US Dollar, "
                            f"which typically exhibit inverse transmission to spot gold valuations."
                        ),
                        mentioned_explicitly=False,
                    )
                )
                assigned_symbols.add("XAU/USD")

        # 3. Macroeconomic releases without explicit central bank mentions
        # (e.g. "US CPI surged 3.8%" or "German GDP contracted")
        if not central_banks and has_monetary_policy_event:
            for curr in detected_currencies:
                if curr in PRIMARY_CURRENCY_PAIRS:
                    for primary_sym in PRIMARY_CURRENCY_PAIRS[curr]:
                        if primary_sym in assigned_symbols:
                            continue
                        if not self.registry.is_supported(primary_sym):
                            continue

                        inst = self.registry.get_instrument(primary_sym)
                        other = inst.quote_currency if inst.base_currency == curr else inst.base_currency

                        affected.append(
                            AffectedInstrument(
                                symbol=primary_sym,
                                relationship="indirect",
                                confidence=0.84,
                                reason=(
                                    f"Key macroeconomic indicators in {curr} impact interest rate differentials "
                                    f"and valuation trends against {other}."
                                ),
                                mentioned_explicitly=False,
                            )
                        )
                        assigned_symbols.add(primary_sym)

        # 4. POTENTIAL: Secondary pairs or commodity spillovers when strong driver exists
        # Add secondary pairs with lower confidence and cautious explanation
        for cb in central_banks:
            cb_currency = cb.get("currency", "")
            for sec_sym in SECONDARY_CURRENCY_PAIRS.get(cb_currency, []):
                if sec_sym in assigned_symbols or not self.registry.is_supported(sec_sym):
                    continue
                inst = self.registry.get_instrument(sec_sym)
                affected.append(
                    AffectedInstrument(
                        symbol=sec_sym,
                        relationship="potential",
                        confidence=0.68,
                        reason=(
                            f"Secondary currency transmission from {cb_currency} monetary developments "
                            f"may influence {sec_sym}, but direct volatility depends on broader market liquidity."
                        ),
                        mentioned_explicitly=False,
                    )
                )
                assigned_symbols.add(sec_sym)

        # Sort: DIRECT first, then INDIRECT, then POTENTIAL; then by confidence descending
        relationship_order = {"direct": 0, "indirect": 1, "potential": 2}
        affected.sort(key=lambda x: (relationship_order.get(x.relationship, 3), -x.confidence))

        return affected

