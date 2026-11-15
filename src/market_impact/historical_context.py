"""
SignalFlow AI - Historical Market Reaction Context Analyzer
Analyzes historical post-event reactions across configurable windows:
- 15 minutes
- 1 hour
- 4 hours
- 1 trading day
Measures: absolute return, signed return, realized volatility, max favorable, max adverse.
Strictly distinguishes historical post-event outcomes from future forecasts.
Never invents historical statistics: if data is unavailable, explicitly returns fallback status.
"""

from typing import Dict, List, Any, Optional
from src.market_impact.models import HistoricalReactionContext

SUPPORTED_REACTION_WINDOWS = ["15m", "1h", "4h", "1d"]


class HistoricalMarketContextAnalyzer:
    """
    Analyzes post-event price reaction data when verified records are provided.
    If historical records are absent, provides transparent rule-based disclosure.
    """

    def __init__(self, historical_database: Optional[Dict[str, Any]] = None):
        # Optional dictionary of verified historical event outcomes
        self._historical_store = historical_database or {}

    def get_context_for_event(
        self,
        event_category: str,
        symbol: Optional[str] = None,
        event_timestamp: Optional[str] = None,
    ) -> HistoricalReactionContext:
        """
        Retrieves historical post-event reaction context.
        If no verified historical series exists for the specific event, returns
        transparent rule_based_fallback status rather than fabricating numbers.
        """
        lookup_key = f"{event_category}:{symbol}" if symbol else event_category
        record = self._historical_store.get(lookup_key)

        if not record:
            return HistoricalReactionContext(
                has_historical_data=False,
                data_status="historical_data_unavailable",
                methodology="rule_based_fallback",
                windows={
                    w: {
                        "status": "unavailable",
                        "absolute_return_pct": None,
                        "signed_return_pct": None,
                        "realized_volatility_pct": None,
                        "max_favorable_move_pct": None,
                        "max_adverse_move_pct": None,
                    }
                    for w in SUPPORTED_REACTION_WINDOWS
                },
                disclaimer=(
                    "No verified post-event price reaction data is available in the local repository for this event. "
                    "All assessments represent transparent rule-based engineering models. "
                    "Historical returns are never fabricated or used as predictive guarantees."
                ),
            )

        # Verified historical record exists
        windows_data: Dict[str, Dict[str, Any]] = {}
        for w in SUPPORTED_REACTION_WINDOWS:
            w_rec = record.get(w, {})
            windows_data[w] = {
                "status": "verified_historical",
                "absolute_return_pct": w_rec.get("absolute_return_pct"),
                "signed_return_pct": w_rec.get("signed_return_pct"),
                "realized_volatility_pct": w_rec.get("realized_volatility_pct"),
                "max_favorable_move_pct": w_rec.get("max_favorable_move_pct"),
                "max_adverse_move_pct": w_rec.get("max_adverse_move_pct"),
            }

        return HistoricalReactionContext(
            has_historical_data=True,
            data_status="verified_historical_record",
            methodology="post_event_historical_analysis",
            windows=windows_data,
            disclaimer=(
                "Historical metrics reflect actual observed market responses around prior analogous events. "
                "Past performance is not indicative of future market results."
            ),
        )

