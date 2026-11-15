"""
SignalFlow AI - Market Impact Predictor Typed Models
Strictly adheres to the output schema specified in Part 3.6.
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field

ImpactLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
VolatilityAssessment = Literal["low", "moderate", "elevated", "extreme"]
PotentialDirection = Literal["bullish", "bearish", "mixed", "uncertain"]

EventCategory = Literal[
    "central_bank_decisions",
    "interest_rate_announcements",
    "inflation_releases",
    "employment_reports",
    "gdp_releases",
    "geopolitical_events",
    "elections",
    "trade_restrictions",
    "financial_crises",
    "banking_events",
    "commodity_supply_disruptions",
    "unexpected_economic_announcements",
    "other_financial_events",
]


class ImpactDimensions(BaseModel):
    economic_importance: int = Field(..., ge=0, le=100, description="Macroeconomic scale of event (0-100)")
    surprise_magnitude: int = Field(..., ge=0, le=100, description="Deviation from market consensus (0-100)")
    instrument_relevance: int = Field(..., ge=0, le=100, description="Breadth and directness of affected instruments (0-100)")
    source_reliability: int = Field(..., ge=0, le=100, description="Credibility of news source / wire (0-100)")
    news_novelty: int = Field(..., ge=0, le=100, description="Freshness and non-repetitive character (0-100)")
    potential_volatility: int = Field(..., ge=0, le=100, description="Anticipated market dispersion and volatility (0-100)")


class AffectedImpactInstrument(BaseModel):
    symbol: str = Field(..., description="Canonical forex symbol e.g. EUR/USD")
    relationship: str = Field(..., description="direct, indirect, or potential")
    potential_direction: PotentialDirection = Field(default="uncertain", description="Directional bias: bullish, bearish, mixed, or uncertain")
    reason: str = Field(..., description="Economic reasoning for impact on this instrument")


class HistoricalReactionContext(BaseModel):
    has_historical_data: bool = Field(default=False)
    data_status: str = Field(default="historical_data_unavailable")
    methodology: str = Field(default="rule_based_estimate")
    windows: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    disclaimer: str = Field(
        default="Historical reaction reflects past post-event data when available; it is never used as a predictive guarantee of future price movements."
    )


class MarketImpactResult(BaseModel):
    article_id: str = Field(default="", description="Unique identifier of analyzed article")
    impact_score: int = Field(..., ge=0, le=100, description="Transparent weighted impact score (0-100)")
    impact_level: ImpactLevel = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    impact_dimensions: ImpactDimensions
    event_category: EventCategory
    affected_instruments: List[AffectedImpactInstrument] = Field(default_factory=list)
    volatility_assessment: VolatilityAssessment = Field(default="moderate")
    methodology: str = Field(default="rule_based", description="rule_based, calibrated_historical, or hybrid")
    explanation: str = Field(..., description="Clear explanation of estimated market impact")
    limitations: List[str] = Field(default_factory=list, description="Explicit modeling caveats and boundaries")
    historical_context: Optional[HistoricalReactionContext] = Field(default=None)
    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp"
    )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

