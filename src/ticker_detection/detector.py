"""
SignalFlow AI - Smart Ticker Detector Service
Combines deterministic dictionary matching, economic transmission modeling,
and selective Google Gemini assistance with strict schema validation.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone

from src.ticker_detection.registry import instrument_registry, InstrumentRegistry
from src.ticker_detection.matcher import DeterministicEntityMatcher
from src.ticker_detection.relationship_engine import EconomicRelationshipEngine
from src.ticker_detection.gemini_extractor import GeminiEntityExtractor
from src.ticker_detection.models import (
    TickerDetectionResult,
    DetectedEntity,
    AffectedInstrument,
)

logger = logging.getLogger(__name__)


class SmartTickerDetector:
    """
    Master service for smart financial entity extraction and forex instrument identification.
    """

    def __init__(
        self,
        registry: Optional[InstrumentRegistry] = None,
        matcher: Optional[DeterministicEntityMatcher] = None,
        relationship_engine: Optional[EconomicRelationshipEngine] = None,
        gemini_extractor: Optional[GeminiEntityExtractor] = None,
    ):
        self.registry = registry or instrument_registry
        self.matcher = matcher or DeterministicEntityMatcher(registry=self.registry)
        self.relationship_engine = relationship_engine or EconomicRelationshipEngine(registry=self.registry)
        self.gemini_extractor = gemini_extractor or GeminiEntityExtractor(registry=self.registry)

    def detect(
        self,
        headline: str,
        body: str = "",
        article_id: str = "",
        use_gemini: bool = False,
    ) -> TickerDetectionResult:
        """
        Analyzes headline and optional body text.
        Primary execution uses deterministic matching and economic transmission (< 5ms, $0 cost).
        Gemini is invoked only when explicitly requested or when entities require deep reasoning.
        """
        full_text = f"{headline}\n{body}".strip() if body else headline.strip()

        # Step 1: Deterministic dictionary & alias matching
        match_data = self.matcher.match(full_text)

        # Step 2: Context-aware economic transmission relationship evaluation
        affected_instruments = self.relationship_engine.evaluate_relationships(full_text, match_data)

        detected_entities = match_data.get("detected_entities", [])
        currencies = match_data.get("currencies", [])
        economic_events = match_data.get("economic_events", [])

        # Step 3: Optional Gemini-assisted extraction for ambiguous context
        is_ambiguous = len(affected_instruments) == 0 and len(detected_entities) > 0 and ("economy" in full_text.lower() or "market" in full_text.lower())
        if use_gemini or is_ambiguous:
            gemini_res = self.gemini_extractor.extract_with_gemini(
                headline=headline,
                body=body,
                article_id=article_id,
            )
            if gemini_res:
                # Merge entities safely without duplicates
                seen_entities = {e.name.lower() for e in detected_entities}
                for g_ent in gemini_res.detected_entities:
                    if g_ent.name.lower() not in seen_entities:
                        detected_entities.append(g_ent)
                        seen_entities.add(g_ent.name.lower())

                # Merge instruments safely, prioritizing validated registry entries
                seen_symbols = {inst.symbol for inst in affected_instruments}
                for g_inst in gemini_res.affected_instruments:
                    if g_inst.symbol not in seen_symbols and self.registry.is_supported(g_inst.symbol):
                        affected_instruments.append(g_inst)
                        seen_symbols.add(g_inst.symbol)

                # Merge currencies & events
                currencies = sorted(list(set(currencies).union(set(gemini_res.currencies))))
                economic_events = sorted(list(set(economic_events).union(set(gemini_res.economic_events))))

        # Strictly enforce that no unsupported symbol slips through
        validated_instruments = [
            inst for inst in affected_instruments if self.registry.is_supported(inst.symbol)
        ]

        return TickerDetectionResult(
            article_id=article_id,
            detected_entities=detected_entities,
            affected_instruments=validated_instruments,
            currencies=sorted(list(set(currencies))),
            economic_events=sorted(list(set(economic_events))),
            detection_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def apply_manual_correction(
        self,
        current_result: TickerDetectionResult,
        corrections: Dict[str, Any],
    ) -> TickerDetectionResult:
        """
        Supports manual correction capability (Part 2.5).
        Allows adding/removing affected instruments or modifying relationship types.
        """
        new_instruments: List[AffectedInstrument] = []
        existing_by_symbol = {inst.symbol: inst for inst in current_result.affected_instruments}

        # Apply modifications or additions
        for sym, details in corrections.get("affected_instruments", {}).items():
            norm_sym = self.registry.normalize_symbol(sym)
            if not norm_sym or not self.registry.is_supported(norm_sym):
                logger.warning(f"Cannot apply manual correction for unsupported symbol: {sym}")
                continue

            rel = details.get("relationship", "indirect")
            conf = float(details.get("confidence", 1.0))
            reason = details.get("reason", "Manually verified by human analyst.")
            explicit = bool(details.get("mentioned_explicitly", False))

            existing_by_symbol[norm_sym] = AffectedInstrument(
                symbol=norm_sym,
                relationship=rel,
                confidence=conf,
                reason=reason,
                mentioned_explicitly=explicit,
            )

        # Remove requested symbols
        for sym_to_remove in corrections.get("remove_instruments", []):
            norm_remove = self.registry.normalize_symbol(sym_to_remove)
            if norm_remove in existing_by_symbol:
                del existing_by_symbol[norm_remove]

        return TickerDetectionResult(
            article_id=current_result.article_id,
            detected_entities=current_result.detected_entities,
            affected_instruments=list(existing_by_symbol.values()),
            currencies=current_result.currencies,
            economic_events=current_result.economic_events,
            detection_timestamp=datetime.now(timezone.utc).isoformat(),
        )

