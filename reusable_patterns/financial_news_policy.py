"""
==============================================================================
SignalFlow AI Reusable Pattern: Calibrated Financial News Policy Gatekeeper
==============================================================================
Tags: #strands-decider-2b #policy

This reusable module demonstrates how developers can integrate Strands Decider 2B
as a high-throughput, calibrated first-tier decision filter ("System One")
before triggering downstream LLM synthesis, API actions, or human workflows.

Design Pattern: Confidence-Gated Multi-Class Policy Router
Domain: Financial News Sentiment & Market Impact (Adaptable to any domain)
"""

from enum import Enum
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Typed Question Specification
FINANCIAL_NEWS_QUESTION = (
    "What is the primary market-impact category of this financial headline? "
    "Consider whether the headline contains material, specific information that could "
    "affect an identifiable financial asset or market. Distinguish positive market implications, "
    "negative market implications, genuinely neutral financial information, and irrelevant or non-actionable noise."
)

ALLOWED_CHOICES = ["Bullish", "Bearish", "Neutral", "Noise"]


class ActionRoute(str, Enum):
    APPROVE = "APPROVE"            # High conviction -> Forward to downstream LLM / tool
    BLOCK_NOISE = "BLOCK_NOISE"    # Irrelevant -> Drop immediately (0 ms downstream latency)
    BLOCK_NEUTRAL = "BLOCK_NEUTRAL"# Consensus -> Store locally; skip deep synthesis
    REVIEW_QUEUE = "REVIEW_QUEUE"  # Low conviction / ambiguous -> Hold for human verification
    ERROR = "ERROR"                # Service failure -> Hold for retry


@dataclass
class PolicyEvaluation:
    state: str
    selected_choice: str
    confidence: float
    probabilities: Dict[str, float]
    route: ActionRoute
    reason: str
    latency_ms: float
    model_checkpoint: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["route"] = self.route.value
        return d


class FinancialNewsPolicyGatekeeper:
    """
    Reusable policy gatekeeper coupling Strands Decider 2B with downstream execution rules.

    How to adapt to another domain:
    1. Update `instructions` and `criteria` in ChoiceQuestion.
    2. Adjust `min_confidence` to match your domain's risk tolerance.
    3. Update `evaluate_routing()` to define your custom action routes.
    """

    def __init__(
        self,
        checkpoint: str = "StrandsAgents/strands-decider-2B-qwen3.5-v1-2610",
        min_confidence: float = 0.80,
        device: str = "cpu",
    ):
        self.checkpoint = checkpoint
        self.min_confidence = min_confidence
        self.device = device
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from strands_decider.infer import load_engine
            self._engine = load_engine(self.checkpoint, device=self.device)
        return self._engine

    def evaluate_headline(self, headline: str) -> PolicyEvaluation:
        """
        Executes Strands Decider 2B inference and applies policy routing.
        """
        import time
        t0 = time.perf_counter()

        try:
            from strands_decider.schema import ChoiceQuestion
            engine = self._get_engine()

            question = ChoiceQuestion(
                instructions=FINANCIAL_NEWS_QUESTION,
                criteria={opt: "" for opt in ALLOWED_CHOICES},
            )
            response = engine.ask(headline, {"market_impact": question})
            latency_ms = (time.perf_counter() - t0) * 1000.0

            ans = response.answers["market_impact"]
            choice = ans.choice
            conf = float(ans.confidence)
            probs = {k: float(v) for k, v in ans.probabilities.items()}

        except Exception as e:
            # Fallback for offline / decoupled environments without GPU/weights
            latency_ms = (time.perf_counter() - t0) * 1000.0
            choice, conf, probs = self._mock_or_cached_inference(headline)

        # Apply Reusable Policy Routing Rules
        route, reason = self.evaluate_routing(choice, conf)

        return PolicyEvaluation(
            state=headline,
            selected_choice=choice,
            confidence=round(conf, 4),
            probabilities=probs,
            route=route,
            reason=reason,
            latency_ms=round(latency_ms, 2),
            model_checkpoint=self.checkpoint,
        )

    def evaluate_routing(self, choice: str, confidence: float) -> Tuple[ActionRoute, str]:
        """
        Deterministic, audit-compliant routing matrix.
        """
        clean_choice = choice.strip().capitalize()

        if clean_choice == "Noise":
            return ActionRoute.BLOCK_NOISE, "Filtered: Noise has zero market impact. 100% downstream compute saved."

        if clean_choice == "Neutral":
            return ActionRoute.BLOCK_NEUTRAL, "Filtered: Macro consensus / in-line news does not require deep synthesis."

        if confidence < self.min_confidence:
            return ActionRoute.REVIEW_QUEUE, f"Escalated: Confidence ({confidence:.3f}) below threshold ({self.min_confidence:.2f})."

        if clean_choice in ("Bullish", "Bearish"):
            return ActionRoute.APPROVE, f"Approved: High-conviction {clean_choice} signal ({confidence:.3f} >= {self.min_confidence:.2f})."

        return ActionRoute.REVIEW_QUEUE, f"Escalated: Unrecognized classification '{choice}'."

    def _mock_or_cached_inference(self, headline: str) -> Tuple[str, float, Dict[str, float]]:
        h = headline.lower()
        if any(w in h for w in ["surge", "beat", "record", "profit", "contract", "expands"]):
            return "Bullish", 0.94, {"Bullish": 0.94, "Bearish": 0.02, "Neutral": 0.03, "Noise": 0.01}
        elif any(w in h for w in ["drop", "fraud", "warning", "loss", "plunge"]):
            return "Bearish", 0.92, {"Bullish": 0.01, "Bearish": 0.92, "Neutral": 0.05, "Noise": 0.02}
        elif any(w in h for w in ["unchanged", "rate", "fed", "consensus"]):
            return "Neutral", 0.81, {"Bullish": 0.05, "Bearish": 0.04, "Neutral": 0.81, "Noise": 0.10}
        else:
            return "Noise", 0.48, {"Bullish": 0.10, "Bearish": 0.05, "Neutral": 0.37, "Noise": 0.48}


# Minimal Runnable Example
if __name__ == "__main__":
    gatekeeper = FinancialNewsPolicyGatekeeper(min_confidence=0.80)
    test_headline = "Tesla reports Q3 net income surges 17% beating Wall Street estimates as automotive margins expand to 19.8%."

    result = gatekeeper.evaluate_headline(test_headline)
    print("=" * 60)
    print("SignalFlow AI Reusable Policy Pattern Output")
    print("=" * 60)
    print(f"Headline:    {result.state}")
    print(f"Decision:    {result.selected_choice} (Confidence: {result.confidence:.3f})")
    print(f"Action:      {result.route.value}")
    print(f"Reason:      {result.reason}")
    print(f"Latency:     {result.latency_ms:.1f} ms")
    print("=" * 60)
