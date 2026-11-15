"""
SignalFlow AI - Alert Engine Models & Schemas
Defines configurable alert rules and deduplicated alert records.
"""

from typing import Optional, Literal, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

AlertConditionType = Literal[
    "critical_impact",
    "high_impact",
    "currency_mention",
    "watchlist_pair",
    "central_bank_event",
]

AlertSeverity = Literal["info", "warning", "critical"]


class AlertRule(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=2, description="Display name of alert rule")
    condition_type: AlertConditionType
    target_value: Optional[str] = Field(default=None, description="e.g. 'USD', 'EUR/USD', 'Federal Reserve'")
    min_confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    enabled: bool = Field(default=True)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class MarketAlert(BaseModel):
    id: Optional[int] = None
    signal_id: int
    rule_id: Optional[int] = None
    alert_type: str
    title: str
    message: str
    severity: AlertSeverity = "warning"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_read: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

