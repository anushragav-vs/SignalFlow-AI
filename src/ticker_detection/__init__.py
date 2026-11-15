"""
SignalFlow AI - Smart Ticker Detection Package
"""

from src.ticker_detection.registry import (
    InstrumentRegistry,
    InstrumentDefinition,
    instrument_registry,
    DEFAULT_SUPPORTED_INSTRUMENTS,
)
from src.ticker_detection.models import (
    DetectedEntity,
    AffectedInstrument,
    TickerDetectionResult,
    RelationshipType,
    MentionType,
    EntityType,
)
from src.ticker_detection.matcher import (
    DeterministicEntityMatcher,
)
from src.ticker_detection.relationship_engine import (
    EconomicRelationshipEngine,
)
from src.ticker_detection.gemini_extractor import (
    GeminiEntityExtractor,
)
from src.ticker_detection.detector import (
    SmartTickerDetector,
)

__all__ = [
    "InstrumentRegistry",
    "InstrumentDefinition",
    "instrument_registry",
    "DEFAULT_SUPPORTED_INSTRUMENTS",
    "DetectedEntity",
    "AffectedInstrument",
    "TickerDetectionResult",
    "RelationshipType",
    "MentionType",
    "EntityType",
    "DeterministicEntityMatcher",
    "EconomicRelationshipEngine",
    "GeminiEntityExtractor",
    "SmartTickerDetector",
]
