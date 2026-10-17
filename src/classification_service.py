"""
SignalFlow AI - Classification Service
Orchestrates headline classification through Strands Decider 2B and evaluates policy routing.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from src.decider_client import DeciderClient, DeciderResult
from config import config


class PolicyAction(str, Enum):
    APPROVE = "APPROVE"
    BLOCK_NOISE = "BLOCK_NOISE"
    BLOCK_NEUTRAL = "BLOCK_NEUTRAL"
    REVIEW_QUEUE = "REVIEW_QUEUE"
    ERROR_RETRY = "ERROR_RETRY"


@dataclass
class ClassificationOutput:
    headline: str
    decision: str
    confidence: float
    probabilities: Dict[str, float]
    policy_action: PolicyAction
    policy_reason: str
    decider_latency_ms: float
    model_id: str
    requires_review: bool
    status: str = "success"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["policy_action"] = self.policy_action.value
        return d


class ClassificationService:
    """
    Applies System One Strands Decider classification and enforces policy routing.
    """

    def __init__(
        self,
        decider_client: Optional[DeciderClient] = None,
        min_confidence: Optional[float] = None,
    ):
        self.client = decider_client or DeciderClient()
        self.min_confidence = min_confidence or config.min_confidence_threshold

    def classify_headline(self, headline: str) -> ClassificationOutput:
        """
        Classifies headline and determines policy routing action based on calibrated confidence.
        """
        decider_res = self.client.ask(headline)

        if decider_res.status != "success":
            return ClassificationOutput(
                headline=headline,
                decision="Error",
                confidence=0.0,
                probabilities={},
                policy_action=PolicyAction.REVIEW_QUEUE,
                policy_reason=f"Decider service failure: {decider_res.error_message}. Routed to review queue.",
                decider_latency_ms=decider_res.latency_ms,
                model_id=decider_res.model_id,
                requires_review=True,
                status=decider_res.status,
                error_message=decider_res.error_message,
            )

        decision = decider_res.selected_option.strip().capitalize()
        conf = decider_res.confidence

        # Case 1: Noise (Drop and record, 0 ms cloud latency)
        if decision == "Noise":
            return ClassificationOutput(
                headline=headline,
                decision=decision,
                confidence=conf,
                probabilities=decider_res.probabilities,
                policy_action=PolicyAction.BLOCK_NOISE,
                policy_reason="Policy: Dropped locally as non-market noise (0 ms cloud latency, $0.00 cost).",
                decider_latency_ms=decider_res.latency_ms,
                model_id=decider_res.model_id,
                requires_review=False,
            )

        # Case 2: Neutral (Consensus/in-line, store & skip deep analysis)
        if decision == "Neutral":
            return ClassificationOutput(
                headline=headline,
                decision=decision,
                confidence=conf,
                probabilities=decider_res.probabilities,
                policy_action=PolicyAction.BLOCK_NEUTRAL,
                policy_reason="Policy: Stored locally as consensus neutral news (cloud analysis skipped).",
                decider_latency_ms=decider_res.latency_ms,
                model_id=decider_res.model_id,
                requires_review=False,
            )

        # Case 3: Invalid or negative confidence -> Fail safely to review queue
        if conf is None or conf <= 0.0 or conf > 1.0:
            return ClassificationOutput(
                headline=headline,
                decision=decision,
                confidence=0.0,
                probabilities=decider_res.probabilities,
                policy_action=PolicyAction.REVIEW_QUEUE,
                policy_reason="Policy: Invalid or unavailable confidence score. Routed to review queue for verification.",
                decider_latency_ms=decider_res.latency_ms,
                model_id=decider_res.model_id,
                requires_review=True,
            )

        # Case 4: Low-confidence Bullish/Bearish below threshold -> Review Queue
        if conf < self.min_confidence:
            return ClassificationOutput(
                headline=headline,
                decision=decision,
                confidence=conf,
                probabilities=decider_res.probabilities,
                policy_action=PolicyAction.REVIEW_QUEUE,
                policy_reason=f"Policy: Low-confidence signal ({conf:.3f} < threshold {self.min_confidence:.2f}). Held in review queue.",
                decider_latency_ms=decider_res.latency_ms,
                model_id=decider_res.model_id,
                requires_review=True,
            )

        # Case 5: High-conviction Bullish or Bearish -> Approved for Gemini
        if decision in ("Bullish", "Bearish"):
            return ClassificationOutput(
                headline=headline,
                decision=decision,
                confidence=conf,
                probabilities=decider_res.probabilities,
                policy_action=PolicyAction.APPROVE,
                policy_reason=f"Policy: High-conviction {decision} signal ({conf:.3f} >= {self.min_confidence:.2f}). Approved for cloud research.",
                decider_latency_ms=decider_res.latency_ms,
                model_id=decider_res.model_id,
                requires_review=False,
            )

        # Unknown decision fallback
        return ClassificationOutput(
            headline=headline,
            decision=decision,
            confidence=conf,
            probabilities=decider_res.probabilities,
            policy_action=PolicyAction.REVIEW_QUEUE,
            policy_reason=f"Policy: Unknown classification '{decision}'. Held in review queue.",
            decider_latency_ms=decider_res.latency_ms,
            model_id=decider_res.model_id,
            requires_review=True,
        )
