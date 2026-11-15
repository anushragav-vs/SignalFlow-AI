"""
SignalFlow AI - Rule-Based Market Impact Scoring Engine
Calculates transparent weighted scores across 6 normalized dimensions (0-100)
and maps scores to configurable impact levels: LOW, MEDIUM, HIGH, CRITICAL.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from src.market_impact.models import (
    ImpactLevel,
    ImpactDimensions,
    VolatilityAssessment,
    EventCategory,
)

# Benchmark scoring weights defined in Part 3.3
DEFAULT_DIMENSION_WEIGHTS = {
    "economic_importance": 0.25,
    "surprise_magnitude": 0.20,
    "instrument_relevance": 0.20,
    "source_reliability": 0.10,
    "news_novelty": 0.10,
    "potential_volatility": 0.15,
}

# Score boundaries defined in Part 3.1
DEFAULT_SCORE_BOUNDARIES: List[Tuple[int, int, ImpactLevel]] = [
    (0, 24, "LOW"),
    (25, 49, "MEDIUM"),
    (50, 74, "HIGH"),
    (75, 100, "CRITICAL"),
]

# Source credibility dictionary
PUBLISHER_CREDIBILITY: Dict[str, int] = {
    "federal reserve": 98,
    "us bureau of labor statistics": 98,
    "bls": 98,
    "ecb": 98,
    "bank of england": 98,
    "bank of japan": 98,
    "reuters": 92,
    "bloomberg": 92,
    "wall street journal": 92,
    "wsj": 92,
    "financial times": 92,
    "dow jones": 88,
    "cnbc": 80,
    "marketwatch": 75,
    "yahoo finance": 75,
    "associated press": 85,
}

# Base economic importance by macro event category
CATEGORY_BASE_IMPORTANCE: Dict[EventCategory, int] = {
    "financial_crises": 98,
    "banking_events": 90,
    "central_bank_decisions": 92,
    "interest_rate_announcements": 92,
    "inflation_releases": 86,
    "employment_reports": 85,
    "gdp_releases": 82,
    "unexpected_economic_announcements": 84,
    "geopolitical_events": 80,
    "trade_restrictions": 70,
    "commodity_supply_disruptions": 72,
    "elections": 70,
    "other_financial_events": 15,
}

SURPRISE_HIGH_PATTERN = re.compile(
    r"\b(surprise|unexpected|shock|emergency|unforeseen|plunges unexpectedly|surges unexpectedly|record beat|huge miss|collapse|panic|sell-off|crash)\b",
    re.IGNORECASE,
)
SURPRISE_MODERATE_PATTERN = re.compile(
    r"\b(beats|misses|above consensus|below consensus|exceeds forecast|faster than expected|slower than expected|surges|plunges|rally|drops)\b",
    re.IGNORECASE,
)
SURPRISE_LOW_PATTERN = re.compile(
    r"\b(in line|as expected|matches forecast|meets consensus|unchanged as expected|modest|slightly|incremental)\b",
    re.IGNORECASE,
)


class ImpactScoringEngine:
    """
    Transparent rule-based scoring engine for financial market impact.
    Calculates weighted composite scores from 6 normalized dimensions (0-100).
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        boundaries: Optional[List[Tuple[int, int, ImpactLevel]]] = None,
    ):
        self.weights = weights or DEFAULT_DIMENSION_WEIGHTS.copy()
        self.boundaries = boundaries or DEFAULT_SCORE_BOUNDARIES.copy()

    def evaluate_source_reliability(self, publisher: str) -> int:
        if not publisher:
            return 70  # Documented neutral fallback for missing source
        clean = publisher.lower().strip()
        for known, score in PUBLISHER_CREDIBILITY.items():
            if known in clean:
                return score
        return 55  # Documented fallback for general/unclassified publishers

    def evaluate_surprise_magnitude(self, text: str) -> int:
        if SURPRISE_HIGH_PATTERN.search(text):
            return 88
        if SURPRISE_MODERATE_PATTERN.search(text):
            return 65
        if SURPRISE_LOW_PATTERN.search(text):
            return 15
        return 25  # Baseline neutral when no surprise keywords are detected

    def evaluate_instrument_relevance(
        self,
        num_affected: int,
        has_direct: bool,
        category: EventCategory = "other_financial_events",
    ) -> int:
        if has_direct and num_affected >= 3:
            return 90
        if has_direct:
            return 80
        if num_affected >= 3:
            return 75
        if num_affected >= 1:
            return 50
        # If market-wide systemic crisis, instrument breadth is inherently high
        if category in ("financial_crises", "banking_events", "central_bank_decisions"):
            return 70
        return 10

    def evaluate_potential_volatility(
        self,
        importance: int,
        surprise: int,
        category: EventCategory,
    ) -> int:
        raw = int(importance * 0.55 + surprise * 0.45)
        if category in ("financial_crises", "banking_events", "central_bank_decisions", "interest_rate_announcements"):
            raw = max(raw, 75)
        elif category == "other_financial_events":
            raw = min(raw, 20)
        return max(5, min(99, raw))

    def evaluate_news_novelty(
        self,
        text: str,
        category: EventCategory,
        is_live: bool = True,
    ) -> int:
        if not is_live:
            return 30
        if "update" in text.lower() or "recap" in text.lower() or "chat" in text.lower():
            return 25
        if category == "other_financial_events":
            return 25
        return 75

    def compute_dimensions(
        self,
        text: str,
        publisher: str,
        category: EventCategory,
        num_affected_instruments: int,
        has_direct_instrument: bool,
        is_live: bool = True,
    ) -> ImpactDimensions:
        econ = CATEGORY_BASE_IMPORTANCE.get(category, 25)
        surp = self.evaluate_surprise_magnitude(text)
        inst = self.evaluate_instrument_relevance(num_affected_instruments, has_direct_instrument, category)
        src = self.evaluate_source_reliability(publisher)
        nov = self.evaluate_news_novelty(text, category, is_live)
        vol = self.evaluate_potential_volatility(econ, surp, category)

        return ImpactDimensions(
            economic_importance=econ,
            surprise_magnitude=surp,
            instrument_relevance=inst,
            source_reliability=src,
            news_novelty=nov,
            potential_volatility=vol,
        )

    def calculate_score(self, dims: ImpactDimensions) -> int:
        """
        Calculates weighted impact score from dimensions:
        score = sum(dimension_value * weight)
        """
        raw_score = (
            dims.economic_importance * self.weights["economic_importance"]
            + dims.surprise_magnitude * self.weights["surprise_magnitude"]
            + dims.instrument_relevance * self.weights["instrument_relevance"]
            + dims.source_reliability * self.weights["source_reliability"]
            + dims.news_novelty * self.weights["news_novelty"]
            + dims.potential_volatility * self.weights["potential_volatility"]
        )
        return max(0, min(100, int(round(raw_score))))

    def determine_level(self, score: int) -> ImpactLevel:
        """Maps numeric score to configured ImpactLevel."""
        for low, high, level in self.boundaries:
            if low <= score <= high:
                return level
        if score >= 75:
            return "CRITICAL"
        return "LOW"

    def determine_volatility_assessment(self, score: int) -> VolatilityAssessment:
        if score >= 75:
            return "extreme"
        if score >= 50:
            return "elevated"
        if score >= 25:
            return "moderate"
        return "low"
