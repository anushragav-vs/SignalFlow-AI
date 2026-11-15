"""
SignalFlow AI - Configurable Market Alert Engine
Evaluates signals against active alert rules, applies confidence filtering,
and enforces strict deduplication to prevent duplicate alerts.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone

from src.alerts.models import AlertRule, MarketAlert, AlertConditionType, AlertSeverity
from src.ticker_detection.models import TickerDetectionResult
from src.market_impact.models import MarketImpactResult

logger = logging.getLogger(__name__)

DEFAULT_ALERT_RULES = [
    AlertRule(
        id=1,
        name="Critical Market Impact Event",
        condition_type="critical_impact",
        target_value=None,
        min_confidence=0.80,
        enabled=True,
    ),
    AlertRule(
        id=2,
        name="High Market Impact Event",
        condition_type="high_impact",
        target_value=None,
        min_confidence=0.80,
        enabled=True,
    ),
    AlertRule(
        id=3,
        name="Federal Reserve Announcement",
        condition_type="central_bank_event",
        target_value="Federal Reserve",
        min_confidence=0.75,
        enabled=True,
    ),
    AlertRule(
        id=4,
        name="EUR/USD Watchlist Transmission",
        condition_type="watchlist_pair",
        target_value="EUR/USD",
        min_confidence=0.80,
        enabled=True,
    ),
]


class AlertEngine:
    """
    Evaluates new signals against active alert rules and records deduplicated alerts.
    """

    def __init__(self, db=None, default_rules: Optional[List[AlertRule]] = None):
        self.db = db
        self._in_memory_rules: List[AlertRule] = (
            default_rules.copy() if default_rules else [r.model_copy() for r in DEFAULT_ALERT_RULES]
        )
        self._seen_alert_keys: Set[str] = set()

    def get_active_rules(self) -> List[AlertRule]:
        if self.db and hasattr(self.db, "get_alert_rules"):
            try:
                db_rules = self.db.get_alert_rules()
                if db_rules:
                    return [AlertRule(**r) for r in db_rules if r.get("enabled", 1)]
            except Exception as e:
                logger.debug(f"Failed to fetch rules from DB, using memory fallback: {e}")
        return [r for r in self._in_memory_rules if r.enabled]

    def evaluate_and_record_alerts(
        self,
        signal_id: int,
        headline: str,
        decider_confidence: float,
        ticker_result: TickerDetectionResult,
        impact_result: MarketImpactResult,
    ) -> List[MarketAlert]:
        """
        Evaluates signal against all active rules and inserts deduplicated alerts.
        """
        active_rules = self.get_active_rules()
        generated_alerts: List[MarketAlert] = []

        affected_symbols = {inst.symbol for inst in ticker_result.affected_instruments}
        detected_cbs = {
            e.name for e in ticker_result.detected_entities if e.entity_type == "central_bank"
        }

        for rule in active_rules:
            # Safeguard: Do not trigger alerts from low-confidence signals unless user explicitly lowered threshold
            if decider_confidence < rule.min_confidence:
                continue

            alert_matched = False
            title = ""
            message = ""
            severity: AlertSeverity = "warning"

            if rule.condition_type == "critical_impact" and impact_result.impact_level == "CRITICAL":
                alert_matched = True
                title = f"🚨 Critical Impact Detected ({impact_result.impact_score}/100)"
                message = f"Headline: \"{headline}\" — Anticipated volatility is {impact_result.volatility_assessment}."
                severity = "critical"

            elif rule.condition_type == "high_impact" and impact_result.impact_level in ("HIGH", "CRITICAL"):
                alert_matched = True
                title = f"⚠️ High Impact Event ({impact_result.impact_score}/100)"
                message = f"Headline: \"{headline}\" — {impact_result.explanation}"
                severity = "warning"

            elif rule.condition_type == "watchlist_pair" and rule.target_value:
                target = rule.target_value.upper().strip()
                if target in affected_symbols:
                    alert_matched = True
                    title = f"🎯 Watchlist Instrument Affected: {target}"
                    inst_obj = next((i for i in ticker_result.affected_instruments if i.symbol == target), None)
                    rel = inst_obj.relationship.upper() if inst_obj else "INDIRECT"
                    message = f"{target} has a {rel} transmission relationship to: \"{headline}\"."
                    severity = "warning" if impact_result.impact_score >= 50 else "info"

            elif rule.condition_type == "currency_mention" and rule.target_value:
                target_cur = rule.target_value.upper().strip()
                if target_cur in ticker_result.currencies:
                    alert_matched = True
                    title = f"💱 Currency Monitored: {target_cur}"
                    message = f"{target_cur} actively referenced in: \"{headline}\"."
                    severity = "info"

            elif rule.condition_type == "central_bank_event":
                if rule.target_value:
                    if rule.target_value.lower() in [cb.lower() for cb in detected_cbs]:
                        alert_matched = True
                        title = f"🏛️ Central Bank Alert: {rule.target_value}"
                        message = f"{rule.target_value} action identified in: \"{headline}\"."
                        severity = "critical" if impact_result.impact_score >= 75 else "warning"
                elif detected_cbs:
                    alert_matched = True
                    cb_names = ", ".join(list(detected_cbs)[:2])
                    title = f"🏛️ Central Bank Event: {cb_names}"
                    message = f"Policy action reported: \"{headline}\"."
                    severity = "warning"

            if alert_matched:
                dedup_key = f"{signal_id}:{rule.condition_type}:{rule.target_value or ''}"
                if dedup_key in self._seen_alert_keys:
                    continue  # In-memory deduplication

                # Check SQLite deduplication if DB available
                if self.db and hasattr(self.db, "has_alert_for_signal"):
                    if self.db.has_alert_for_signal(signal_id, rule.condition_type, rule.target_value):
                        continue

                self._seen_alert_keys.add(dedup_key)

                alert = MarketAlert(
                    signal_id=signal_id,
                    rule_id=rule.id,
                    alert_type=rule.condition_type,
                    title=title,
                    message=message,
                    severity=severity,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    is_read=False,
                )

                if self.db and hasattr(self.db, "insert_alert"):
                    try:
                        alert_id = self.db.insert_alert(
                            signal_id=alert.signal_id,
                            rule_id=alert.rule_id,
                            alert_type=alert.alert_type,
                            title=alert.title,
                            message=alert.message,
                            severity=alert.severity,
                        )
                        alert.id = alert_id
                    except Exception as e:
                        logger.warning(f"Failed to persist alert in SQLite: {e}")

                generated_alerts.append(alert)

        return generated_alerts

