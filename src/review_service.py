"""
SignalFlow AI - Human Review Queue Service
Provides audit-compliant human-in-the-loop oversight for low-confidence or disputed signals.
Preserves original Strands Decider model classifications while logging reviewer decisions.
"""

import logging
from typing import List, Dict, Any, Optional

from src.database import SignalFlowDatabase
from src.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class ReviewService:
    """
    Manages review queue retrieval, human actions, and on-demand cloud synthesis.
    """

    def __init__(self, db: Optional[SignalFlowDatabase] = None):
        self.db = db or SignalFlowDatabase()

    def get_pending_items(self) -> List[Dict[str, Any]]:
        return self.db.get_pending_reviews()

    def confirm_item(self, signal_id: int, notes: str = ""):
        """
        Confirms the original model classification without altering it.
        """
        self.db.record_review_action(
            signal_id=signal_id,
            action="CONFIRMED",
            corrected_label=None,
            notes=notes,
        )

    def reclassify_item(self, signal_id: int, new_label: str, notes: str = ""):
        """
        Assigns human-corrected label without overwriting the original decider_sentiment.
        """
        self.db.record_review_action(
            signal_id=signal_id,
            action="RECLASSIFIED",
            corrected_label=new_label,
            notes=notes,
        )

    def dismiss_item(self, signal_id: int, notes: str = ""):
        """
        Dismisses the item as non-actionable or noise.
        """
        self.db.record_review_action(
            signal_id=signal_id,
            action="DISMISSED",
            corrected_label="Noise",
            notes=notes,
        )

    def approve_and_send_to_gemini(
        self,
        signal_id: int,
        gemini_service: Optional[GeminiService] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches a human-approved signal to Gemini and records the structured analysis.
        """
        service = gemini_service or GeminiService()

        # Retrieve the signal
        with self.db._get_connection() as conn:
            row = conn.execute("SELECT * FROM signals WHERE id = ?", (signal_id,)).fetchone()
            if not row:
                raise ValueError(f"Signal ID {signal_id} not found.")
            sig = dict(row)

        effective_sentiment = sig.get("corrected_label") or sig.get("decider_sentiment")

        # Execute Gemini analysis
        res = service.analyze_headline(
            headline=sig["headline"],
            decision=effective_sentiment,
            confidence=sig["decider_confidence"],
        )

        analysis = res.analysis
        facts = analysis.reported_facts if analysis else []
        mechanisms = analysis.transmission_mechanism if analysis else ""
        assets = analysis.affected_assets if analysis else []
        implications = analysis.directional_implications if analysis else ""
        uncertainties = analysis.uncertainties_and_risks if analysis else []
        hypotheses = analysis.analytical_hypotheses if analysis else []

        self.db.update_gemini_analysis(
            signal_id=signal_id,
            gemini_model_id=res.model_id,
            gemini_status=res.status,
            raw_summary=analysis.raw_summary if analysis else "",
            event_summary=analysis.event_summary if analysis else "",
            transmission_mechanism=mechanisms,
            affected_assets=assets,
            directional_implications=implications,
            uncertainties=uncertainties,
            reported_facts=facts,
            analytical_hypotheses=hypotheses,
            cloud_latency_ms=res.latency_ms,
            input_tokens=res.input_tokens,
            output_tokens=res.output_tokens,
            total_tokens=res.total_tokens,
            estimated_cost_usd=res.estimated_cost_usd,
        )

        # Mark review as CONFIRMED / APPROVED
        self.db.record_review_action(
            signal_id=signal_id,
            action="CONFIRMED",
            notes="Manually approved and sent to Google Gemini.",
        )

        return res.to_dict()
