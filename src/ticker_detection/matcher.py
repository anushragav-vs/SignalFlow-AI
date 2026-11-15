"""
SignalFlow AI - Deterministic Financial Entity & Forex Instrument Matcher
Performs high-precision deterministic dictionary matching, alias normalization,
ambiguity filtering, and deduplication against the supported instrument registry.
"""

import os
import re
import json
import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from pathlib import Path

from src.ticker_detection.registry import instrument_registry, InstrumentRegistry
from src.ticker_detection.models import DetectedEntity, EntityType, MentionType

logger = logging.getLogger(__name__)

DEFAULT_DICTIONARY_PATH = Path(__file__).parent / "entity_dictionary.json"


class DeterministicEntityMatcher:
    """
    High-precision deterministic matcher for financial entities and forex aliases.
    Loads externalized dictionary and enforces strict word boundaries and context validation.
    """

    def __init__(
        self,
        dictionary_path: Optional[Path] = None,
        registry: Optional[InstrumentRegistry] = None,
    ):
        self.dict_path = dictionary_path or DEFAULT_DICTIONARY_PATH
        self.registry = registry or instrument_registry
        self.dictionary_data: Dict[str, Any] = {}
        self._compiled_forex_patterns: List[Tuple[re.Pattern, str]] = []
        self._compiled_central_bank_patterns: List[Tuple[re.Pattern, str, str, str]] = []  # pattern, name, currency, region
        self._compiled_currency_patterns: List[Tuple[re.Pattern, str, str]] = []  # pattern, code, name
        self._compiled_economic_patterns: List[Tuple[re.Pattern, str, str, str]] = []  # pattern, name, category, event_type
        self.load_dictionary()

    def load_dictionary(self):
        """Loads and compiles regex patterns from the external JSON entity dictionary."""
        if not os.path.exists(self.dict_path):
            raise FileNotFoundError(f"Entity dictionary not found at {self.dict_path}")

        with open(self.dict_path, "r", encoding="utf-8") as f:
            self.dictionary_data = json.load(f)

        self._compile_patterns()

    def _compile_patterns(self):
        self._compiled_forex_patterns.clear()
        self._compiled_central_bank_patterns.clear()
        self._compiled_currency_patterns.clear()
        self._compiled_economic_patterns.clear()

        # 1. Compile Forex Pair Aliases
        pair_aliases = self.dictionary_data.get("forex_pair_aliases", {})
        for canonical_sym, aliases in pair_aliases.items():
            if not self.registry.is_supported(canonical_sym):
                continue
            # Sort aliases by length descending so longer phrases match first
            sorted_aliases = sorted(aliases, key=len, reverse=True)
            for alias in sorted_aliases:
                escaped = re.escape(alias)
                # Word boundary check
                pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
                self._compiled_forex_patterns.append((pattern, canonical_sym))

        # 2. Compile Central Banks
        for cb in self.dictionary_data.get("central_banks", []):
            name = cb["name"]
            curr = cb.get("primary_currency", "")
            region = cb.get("region", "")
            requires_context = set(cb.get("requires_context", []))

            for alias in sorted(cb.get("aliases", []), key=len, reverse=True):
                escaped = re.escape(alias)
                if alias in requires_context:
                    # Ambiguous alias like "Fed" requires strict casing or prefix
                    # e.g., "Fed", "the Fed", "Fed's" but not lowercase "fed"
                    pattern = re.compile(rf"(?<!\w)(?:The\s+)?{escaped}(?:'s)?(?!\w)")
                else:
                    pattern = re.compile(rf"(?<!\w){escaped}(?:'s)?(?!\w)", re.IGNORECASE)
                self._compiled_central_bank_patterns.append((pattern, name, curr, region))

        # 3. Compile Currencies
        for cur in self.dictionary_data.get("currencies", []):
            code = cur["code"]
            name = cur["name"]
            requires_context = set(cur.get("requires_context", []))

            # Add currency code itself with strict word boundary
            if code in requires_context or code in ("CAD", "AUD", "NZD", "CHF", "USD", "EUR", "GBP", "JPY", "XAU"):
                # Currency code must be uppercase to avoid collisions (e.g. CAD != computer aided design)
                code_pattern = re.compile(rf"(?<!\w){code}(?!\w)")
                self._compiled_currency_patterns.append((code_pattern, code, name))

            for alias in sorted(cur.get("aliases", []), key=len, reverse=True):
                escaped = re.escape(alias)
                if alias in requires_context:
                    # Must be capitalized
                    pattern = re.compile(rf"(?<!\w){escaped}(?!\w)")
                else:
                    pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
                self._compiled_currency_patterns.append((pattern, code, name))

        # 4. Compile Economic Entities
        for ec in self.dictionary_data.get("economic_entities", []):
            name = ec["name"]
            category = ec.get("category", "")
            event_type = ec.get("event_type", "")
            requires_context = set(ec.get("requires_context", []))

            for alias in sorted(ec.get("aliases", []), key=len, reverse=True):
                escaped = re.escape(alias)
                if alias in requires_context or alias in ("CPI", "PPI", "GDP", "NFP", "PMI"):
                    # Strict uppercase for acronyms
                    pattern = re.compile(rf"(?<!\w){escaped}(?!\w)")
                else:
                    pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
                self._compiled_economic_patterns.append((pattern, name, category, event_type))

    def match(self, text: str) -> Dict[str, Any]:
        """
        Executes deterministic matching across the provided text.
        Returns:
            - detected_entities: List[DetectedEntity]
            - explicit_instruments: List[str] (canonical symbols explicitly in text)
            - currencies: List[str] (ISO currency codes)
            - economic_events: List[str] (event category strings)
            - central_banks: List[Dict[str, str]] (name, currency, region)
        """
        if not text or not text.strip():
            return {
                "detected_entities": [],
                "explicit_instruments": [],
                "currencies": [],
                "economic_events": [],
                "central_banks": [],
            }

        detected_entities: List[DetectedEntity] = []
        seen_entity_keys: Set[Tuple[str, str]] = set()  # (entity_type, name)
        explicit_instruments: Set[str] = set()
        currencies: Set[str] = set()
        economic_events: Set[str] = set()
        central_banks: List[Dict[str, str]] = []
        seen_cbs: Set[str] = set()

        # 1. Match Explicit Forex Pairs
        for pattern, canonical_sym in self._compiled_forex_patterns:
            for match_obj in pattern.finditer(text):
                matched_str = match_obj.group(0)
                # Verify that canonical symbol is valid in registry
                norm = self.registry.normalize_symbol(canonical_sym)
                if norm and (("forex_pair", norm) not in seen_entity_keys):
                    seen_entity_keys.add(("forex_pair", norm))
                    explicit_instruments.add(norm)
                    detected_entities.append(
                        DetectedEntity(
                            name=norm,
                            entity_type="forex_pair",
                            mention_type="explicit",
                            raw_match=matched_str,
                            confidence=1.0,
                        )
                    )
                    # Automatically add the constituent currencies
                    inst_def = self.registry.get_instrument(norm)
                    if inst_def:
                        currencies.add(inst_def.base_currency)
                        currencies.add(inst_def.quote_currency)

        # 2. Match Central Banks
        for pattern, cb_name, curr, region in self._compiled_central_bank_patterns:
            for match_obj in pattern.finditer(text):
                matched_str = match_obj.group(0)
                if ("central_bank", cb_name) not in seen_entity_keys:
                    seen_entity_keys.add(("central_bank", cb_name))
                    detected_entities.append(
                        DetectedEntity(
                            name=cb_name,
                            entity_type="central_bank",
                            mention_type="explicit",
                            raw_match=matched_str,
                            confidence=1.0,
                        )
                    )
                    if curr:
                        currencies.add(curr)
                    if cb_name not in seen_cbs:
                        seen_cbs.add(cb_name)
                        central_banks.append({
                            "name": cb_name,
                            "currency": curr,
                            "region": region,
                        })

        # 3. Match Currencies
        for pattern, code, cur_name in self._compiled_currency_patterns:
            for match_obj in pattern.finditer(text):
                matched_str = match_obj.group(0)
                currencies.add(code)
                if ("currency", code) not in seen_entity_keys:
                    seen_entity_keys.add(("currency", code))
                    detected_entities.append(
                        DetectedEntity(
                            name=f"{code} ({cur_name})",
                            entity_type="currency",
                            mention_type="explicit",
                            raw_match=matched_str,
                            confidence=0.98,
                        )
                    )

        # 4. Match Economic Entities
        for pattern, name, category, event_type in self._compiled_economic_patterns:
            for match_obj in pattern.finditer(text):
                matched_str = match_obj.group(0)
                if event_type:
                    economic_events.add(event_type)
                if ("economic_indicator", name) not in seen_entity_keys:
                    seen_entity_keys.add(("economic_indicator", name))
                    detected_entities.append(
                        DetectedEntity(
                            name=name,
                            entity_type="economic_indicator",
                            mention_type="explicit",
                            raw_match=matched_str,
                            confidence=0.95,
                        )
                    )

        return {
            "detected_entities": detected_entities,
            "explicit_instruments": sorted(list(explicit_instruments)),
            "currencies": sorted(list(currencies)),
            "economic_events": sorted(list(economic_events)),
            "central_banks": central_banks,
        }

