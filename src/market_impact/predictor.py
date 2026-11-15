"""
SignalFlow AI - Market Impact Predictor Engine
Coordinates event classification, transparent dimension scoring, instrument direction mapping,
and historical context analysis without fabricating market statistics.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from src.market_impact.models import (
    MarketImpactResult,
    ImpactDimensions,
    ImpactLevel,
    VolatilityAssessment,
    PotentialDirection,
    EventCategory,
    AffectedImpactInstrument,
)
from src.market_impact.event_classifier import EventClassifier
from src.market_impact.scoring import ImpactScoringEngine
from src.market_impact.historical_context import HistoricalMarketContextAnalyzer
from src.ticker_detection.models import AffectedInstrument

logger = logging.getLogger(__name__)


class MarketImpactPredictor:
    """
    Evaluates the potential market impact magnitude of financial news.
    Strictly decouples event significance from bullish/bearish price direction.
    """

    def __init__(
        self,
        scoring_engine: Optional[ImpactScoringEngine] = None,
        event_classifier: Optional[EventClassifier] = None,
        historical_analyzer: Optional[HistoricalMarketContextAnalyzer] = None,
    ):
        self.scoring = scoring_engine or ImpactScoringEngine()
        self.classifier = event_classifier or EventClassifier()
        self.historical_analyzer = historical_analyzer or HistoricalMarketContextAnalyzer()

    def predict_impact(
        self,
        headline: str,
        body: str = "",
        publisher: str = "Financial Wire",
        is_live: bool = True,
        article_id: str = "",
        decider_sentiment: Optional[str] = None,
        affected_instruments: Optional[List[AffectedInstrument]] = None,
    ) -> MarketImpactResult:
        full_text = f"{headline}\n{body}".strip() if body else headline.strip()

        # Step 1: Categorize macro event
        category = self.classifier.classify_event(full_text)

        # Step 2: Instrument relevance inputs
        instruments = affected_instruments or []
        num_affected = len(instruments)
        has_direct = any(inst.relationship == "direct" for inst in instruments)

        # Step 3: Compute individual dimensions (0-100)
        dimensions = self.scoring.compute_dimensions(
            text=full_text,
            publisher=publisher,
            category=category,
            num_affected_instruments=num_affected,
            has_direct_instrument=has_direct,
            is_live=is_live,
        )

        # Step 4: Calculate weighted composite score
        score = self.scoring.calculate_score(dimensions)
        level: ImpactLevel = self.scoring.determine_level(score)
        volatility: VolatilityAssessment = self.scoring.determine_volatility_assessment(score)

        # Step 5: Map affected instruments with directional bias
        direction: PotentialDirection = "uncertain"
        if decider_sentiment:
            sent_lower = decider_sentiment.lower()
            if "bullish" in sent_lower:
                direction = "bullish"
            elif "bearish" in sent_lower:
                direction = "bearish"
            elif "neutral" in sent_lower:
                direction = "mixed"

        impact_instruments: List[AffectedImpactInstrument] = []
        for inst in instruments:
            impact_instruments.append(
                AffectedImpactInstrument(
                    symbol=inst.symbol,
                    relationship=inst.relationship,
                    potential_direction=direction,
                    reason=inst.reason,
                )
            )

        # Step 6: Generate transparent narrative explanation
        category_readable = category.replace("_", " ").title()
        explanation = (
            f"This {category_readable} event registers a {level} impact score of {score}/100. "
            f"Key driving factors include an economic importance rating of {dimensions.economic_importance}/100 "
            f"and a surprise deviation of {dimensions.surprise_magnitude}/100. "
            f"Anticipated market volatility is {volatility}."
        )
        if dimensions.surprise_magnitude >= 80 or "emergency" in full_text.lower():
            explanation += " The event is characterized by significant surprise or emergency deviation from market consensus."

        # Step 7: Historical Context
        primary_symbol = instruments[0].symbol if instruments else None
        historical_ctx = self.historical_analyzer.get_context_for_event(
            event_category=category,
            symbol=primary_symbol,
        )

        # Step 8: Standard engineering limitations
        limitations = [
            "Actual market reaction depends on pre-event consensus positioning and subsequent official press conferences.",
            "Impact score estimates potential market significance, not guaranteed directional price trajectory.",
            "Broader market liquidity and overlapping economic calendar releases can amplify or dampen localized instrument volatility.",
        ]

        return MarketImpactResult(
            article_id=article_id,
            impact_score=score,
            impact_level=level,
            impact_dimensions=dimensions,
            event_category=category,
            affected_instruments=impact_instruments,
            volatility_assessment=volatility,
            methodology="rule_based",
            explanation=explanation,
            limitations=limitations,
            historical_context=historical_ctx,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        )
