"""
SignalFlow AI - Smart Ticker Detection Typed Schemas & Models
Strictly adheres to the output schema specified in Part 2.4.
"""

from typing import List, Optional, Literal, Dict, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pydantic import BaseModel, Field


RelationshipType = Literal["direct", "indirect", "potential"]
MentionType = Literal["explicit", "implicit", "contextual"]
EntityType = Literal["forex_pair", "currency", "central_bank", "economic_indicator", "commodity"]


class DetectedEntity(BaseModel):
    name: str = Field(..., description="Canonical name of the detected entity")
    entity_type: EntityType = Field(..., description="Category of entity")
    mention_type: MentionType = Field(default="explicit", description="How the entity was referenced")
    raw_match: Optional[str] = Field(default=None, description="Actual string fragment matched in text")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence of entity detection")


class AffectedInstrument(BaseModel):
    symbol: str = Field(..., description="Canonical supported forex symbol e.g. EUR/USD")
    relationship: RelationshipType = Field(..., description="direct, indirect, or potential relationship")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection / transmission confidence score")
    reason: str = Field(..., description="Defensible economic justification for the relationship")
    mentioned_explicitly: bool = Field(default=False, description="True if symbol was directly referenced in text")


class TickerDetectionResult(BaseModel):
    article_id: str = Field(default="", description="Unique identifier of the analyzed article")
    detected_entities: List[DetectedEntity] = Field(default_factory=list)
    affected_instruments: List[AffectedInstrument] = Field(default_factory=list)
    currencies: List[str] = Field(default_factory=list, description="Unique ISO currency codes involved")
    economic_events: List[str] = Field(default_factory=list, description="Categories of economic events identified")
    detection_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp of analysis"
    )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

