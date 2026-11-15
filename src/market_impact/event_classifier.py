"""
SignalFlow AI - Event Categorization Engine
Categorizes financial news into the 13 standard macroeconomic categories defined in Part 3.4.
"""

import re
from typing import Dict, List, Tuple
from src.market_impact.models import EventCategory

# Compiled keyword and regex patterns for macroeconomic event classification
EVENT_PATTERNS: List[Tuple[EventCategory, re.Pattern]] = [
    (
        "financial_crises",
        re.compile(r"\b(financial crisis|systemic crisis|debt default|sovereign default|liquidity contagion|bailout package|emergency rescue|market crash|black swan|panic sell-off|global sell-off)\b", re.IGNORECASE),
    ),
    (
        "interest_rate_announcements",
        re.compile(r"\b(interest rates?|rate hikes?|rate cuts?|rate increases?|rate reductions?|basis points|hike rates?|cut rates?|rates? unchanged|terminal rate|benchmark rate|economic stimulus|monetary easing)\b", re.IGNORECASE),
    ),
    (
        "central_bank_decisions",
        re.compile(r"\b(federal reserve|fomc|ecb|european central bank|bank of england|boe|bank of japan|boj|rba|reserve bank|snb|central bank|monetary policy meeting|quantitative tightening|quantitative easing|balance sheet reduction)\b", re.IGNORECASE),
    ),
    (
        "inflation_releases",
        re.compile(r"\b(cpi|ppi|consumer price index|producer price index|inflation|pce price index|core pce|cost of living|price pressures)\b", re.IGNORECASE),
    ),
    (
        "employment_reports",
        re.compile(r"\b(nonfarm payrolls|non-farm payrolls|nfp|unemployment rate|jobless claims|initial claims|jobs report|labor market|wage growth|hiring pace)\b", re.IGNORECASE),
    ),
    (
        "gdp_releases",
        re.compile(r"\b(gdp|gross domestic product|economic growth|quarterly growth|economic contraction|recession|annualized growth)\b", re.IGNORECASE),
    ),
    (
        "banking_events",
        re.compile(r"\b(bank failure|bank collapse|banking collapse|banking crisis|deposit flight|credit default|credit suisse|silicon valley bank|bank run|bank liquidity|capital adequacy)\b", re.IGNORECASE),
    ),
    (
        "trade_restrictions",
        re.compile(r"\b(tariffs|trade restriction|import tariff|customs duty|export ban|trade dispute|trade sanctions|trade embargo|wto dispute)\b", re.IGNORECASE),
    ),
    (
        "commodity_supply_disruptions",
        re.compile(r"\b(opec|oil embargo|crude oil cut|refinery outage|pipeline shutdown|supply disruption|gas export halt|strait of hormuz|energy crisis)\b", re.IGNORECASE),
    ),
    (
        "geopolitical_events",
        re.compile(r"\b(war|military strike|sanctions|geopolitical conflict|missile attack|peace treaty|ceasefire|invasion|tensions escalate)\b", re.IGNORECASE),
    ),
    (
        "elections",
        re.compile(r"\b(presidential election|general election|prime minister election|parliamentary vote|snap election|election results|ballot|referendum)\b", re.IGNORECASE),
    ),
    (
        "unexpected_economic_announcements",
        re.compile(r"\b(surprise announcement|unexpected surge|unexpected drop|emergency statement|unforeseen|shock print|abrupt change)\b", re.IGNORECASE),
    ),
]


class EventClassifier:
    """
    Classifies news headline and body text into one of 13 macroeconomic event categories.
    """

    @staticmethod
    def classify_event(text: str) -> EventCategory:
        """
        Evaluates regex rules against the text and returns the best matching EventCategory.
        Falls back to 'other_financial_events' if no specific category applies.
        """
        if not text:
            return "other_financial_events"

        # Check in priority order
        for category, pattern in EVENT_PATTERNS:
            if pattern.search(text):
                return category

        return "other_financial_events"
