"""
SignalFlow AI - Google Gemini Cloud Analysis Service
Powered by the official Google Gen AI Python SDK (google-genai).
Extracts structured financial market intelligence with strict factual boundary enforcement.
"""

import os
import time
import json
import logging
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List

from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError, ServerError

from config import config, FINANCIAL_DISCLAIMER

logger = logging.getLogger(__name__)

GEMINI_PRICING_PER_1M = {
    "gemini-3.5-flash-lite": {"prompt": 0.075, "completion": 0.30},
    "gemini-3.8-flash": {"prompt": 0.15, "completion": 0.60},
    "gemini-2.5-flash": {"prompt": 0.075, "completion": 0.30},
    "gemini-2.5-pro": {"prompt": 1.25, "completion": 5.00},
    "gemini-1.5-flash": {"prompt": 0.075, "completion": 0.30},
    "default": {"prompt": 0.075, "completion": 0.30},
}


@dataclass
class StructuredFinancialAnalysis:
    event_summary: str = ""
    transmission_mechanism: str = ""
    affected_assets: List[str] = field(default_factory=list)
    directional_implications: str = ""
    uncertainties_and_risks: List[str] = field(default_factory=list)
    reported_facts: List[str] = field(default_factory=list)
    analytical_hypotheses: List[str] = field(default_factory=list)
    catalyst_watchpoints: List[str] = field(default_factory=list)
    market_impact_horizon: str = ""
    institutional_risk_level: str = ""
    peer_impact: List[str] = field(default_factory=list)
    raw_summary: str = ""
    disclaimer: str = FINANCIAL_DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GeminiAnalysisResult:
    headline: str
    decision: str
    confidence: float
    model_id: str
    latency_ms: float
    analysis: Optional[StructuredFinancialAnalysis] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost_usd: float = 0.0
    status: str = "success"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.analysis:
            d["analysis"] = self.analysis.to_dict()
        return d


class GeminiService:
    """
    Google AI Studio Gemini API client using official google-genai SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        timeout_sec: Optional[int] = None,
    ):
        self.api_key = api_key if api_key is not None else config.gemini_api_key
        self.model_id = model_id or config.gemini_model_id
        self.timeout_sec = timeout_sec or config.gemini_timeout_sec
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if self._client is not None:
            return self._client

        resolved_key = self.api_key if self.api_key is not None else os.environ.get("GEMINI_API_KEY")
        if not resolved_key or not resolved_key.strip():
            raise ValueError(
                "GEMINI_API_KEY is not configured in the environment. "
                "Please add your Google AI Studio API key to .env."
            )

        timeout_ms = int(self.timeout_sec * 1000) if self.timeout_sec else 30000
        http_opts = types.HttpOptions(timeout=timeout_ms)
        self._client = genai.Client(api_key=resolved_key.strip(), http_options=http_opts)
        return self._client

    def check_credentials_status(self) -> Dict[str, Any]:
        resolved_key = self.api_key if self.api_key is not None else os.environ.get("GEMINI_API_KEY")
        if not resolved_key or not resolved_key.strip():
            return {
                "configured": False,
                "provider": "Google AI Studio",
                "model_id": self.model_id,
                "message": "No GEMINI_API_KEY found in environment or .env file.",
            }
        return {
            "configured": True,
            "provider": "Google AI Studio",
            "model_id": self.model_id,
            "key_length": len(resolved_key.strip()),
            "message": "Google AI Studio GEMINI_API_KEY resolved successfully from environment.",
        }

    def list_accessible_models(self) -> Dict[str, Any]:
        try:
            client = self._get_client()
            pager = client.models.list()
            models_list = []
            for m in pager:
                actions = getattr(m, "supported_actions", None) or []
                if not actions or "generateContent" in actions:
                    name = getattr(m, "name", "").replace("models/", "")
                    display = getattr(m, "display_name", name)
                    models_list.append({"modelId": name, "displayName": display})
            return {"success": True, "total_count": len(models_list), "models": models_list}
        except ValueError as ve:
            return {"success": False, "error_code": "MissingApiKeyError", "message": str(ve)}
        except Exception as e:
            return {"success": False, "error_code": type(e).__name__, "message": str(e)}

    def verify_model_availability(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        target = (model_id or self.model_id).replace("models/", "")
        listing = self.list_accessible_models()
        if not listing["success"]:
            return {
                "available": False,
                "model_id": target,
                "message": f"Cannot verify availability: {listing['message']}",
            }
        avail_ids = [m["modelId"] for m in listing.get("models", [])]
        is_avail = target in avail_ids
        return {
            "available": is_avail,
            "model_id": target,
            "total_accessible_models": len(avail_ids),
            "message": f"Model '{target}' is verified and available." if is_avail else f"Model '{target}' not found in active catalog.",
        }

    def analyze_headline(
        self,
        headline: str,
        decision: str,
        confidence: float,
        model_id: Optional[str] = None,
    ) -> GeminiAnalysisResult:
        """
        Executes real Gemini analysis adhering to conservative generation settings and structured schema.
        """
        try:
            client = self._get_client()
        except ValueError as ve:
            return GeminiAnalysisResult(
                headline=headline,
                decision=decision,
                confidence=confidence,
                model_id=model_id or self.model_id,
                latency_ms=0.0,
                status="error_missing_key",
                error_message=str(ve),
            )

        chosen_model = (model_id or self.model_id).replace("models/", "")

        system_instruction = (
            "You are SignalFlow AI's senior institutional financial intelligence analyst. "
            "Analyze the provided headline and local Strands Decider 2B classification. "
            "You must separate your analysis into strict structured fields separating verified facts from analytical inferences: "
            "1. event_summary: Concise 1-2 sentence institutional summary of the reported event. "
            "2. transmission_mechanism: The financial-market transmission mechanism (how this affects cash flows, valuations, discount rates, supply/demand, or cost of capital). "
            "3. affected_assets: List of specific tickers, asset classes, or commodity/bond instruments directly impacted (e.g. ['NVDA', 'TSM', 'SOXX', 'US10Y', 'CL=F']). "
            "4. directional_implications: Clear assessment of bullish, bearish, mixed, or uncertain price action bias and volatility implications. "
            "5. uncertainties_and_risks: Key missing information, execution risks, or upcoming data points to watch. "
            "6. reported_facts: List 2-3 objective, verified facts explicitly stated in the source. "
            "7. analytical_hypotheses: List 1-2 forward-looking analytical inferences clearly distinguished from facts. "
            "8. catalyst_watchpoints: List 2-3 specific upcoming calendar catalysts, economic data releases, or corporate reports to watch (e.g. ['Next FOMC Rate Decision', 'Q3 Earnings Print', 'U.S. CPI Release']). "
            "9. market_impact_horizon: Estimated impact timeframe: 'Immediate / Intraday (0-24h)', 'Tactical (1-4 weeks)', or 'Strategic / Structural (Multi-Month)'. "
            "10. institutional_risk_level: Risk severity rating: 'Low', 'Moderate', 'High', or 'Systemic'. "
            "11. peer_impact: List 2-4 related industry peers or sector supply-chain tickers sensitive to this event. "
            "Rules: Strictly output valid JSON matching these keys. Never invent prices or give personalized financial advice."
        )

        user_prompt = (
            f"Headline: \"{headline}\"\n"
            f"Strands Decider 2B Classification: {decision} (Calibrated Confidence: {confidence:.3f})\n\n"
            f"Analyze this market event according to the required institutional JSON schema."
        )

        config_params = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
            max_output_tokens=850,
            response_mime_type="application/json",
        )

        start_time = time.perf_counter()

        try:
            response = client.models.generate_content(
                model=chosen_model,
                contents=user_prompt,
                config=config_params,
            )
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            raw_text = response.text or ""
            analysis = self._parse_json_response(raw_text)

            # Extract token metadata
            usage = getattr(response, "usage_metadata", None)
            in_tok = getattr(usage, "prompt_token_count", None) if usage else None
            out_tok = getattr(usage, "candidates_token_count", None) if usage else None
            tot_tok = getattr(usage, "total_token_count", None) if usage else None

            # Calculate accurate cost
            cost = self._calculate_cost(chosen_model, in_tok, out_tok)

            return GeminiAnalysisResult(
                headline=headline,
                decision=decision,
                confidence=confidence,
                model_id=chosen_model,
                latency_ms=round(latency_ms, 2),
                analysis=analysis,
                input_tokens=in_tok,
                output_tokens=out_tok,
                total_tokens=tot_tok,
                estimated_cost_usd=cost,
                status="success",
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            err_type = type(e).__name__
            err_msg = str(e)

            if "Timeout" in err_type or "timed out" in err_msg.lower():
                status = "error_timeout"
                clean_msg = f"Gemini API request timed out after {latency_ms:.1f} ms."
            elif isinstance(e, ClientError):
                status = "error_api_client"
                clean_msg = f"Gemini ClientError [{e.code}]: {err_msg}"
            elif isinstance(e, ServerError):
                status = "error_api_server"
                clean_msg = f"Gemini ServerError [{e.code}]: {err_msg}"
            elif isinstance(e, APIError):
                status = "error_api"
                clean_msg = f"Gemini APIError: {err_msg}"
            else:
                status = "error_unknown"
                clean_msg = f"Unexpected error: {err_type}: {err_msg}"

            return GeminiAnalysisResult(
                headline=headline,
                decision=decision,
                confidence=confidence,
                model_id=chosen_model,
                latency_ms=round(latency_ms, 2),
                status=status,
                error_message=clean_msg,
            )

    def _parse_json_response(self, text: str) -> StructuredFinancialAnalysis:
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            data = json.loads(clean_text)
            event_summary = str(data.get("event_summary", "")).strip()
            transmission = str(data.get("transmission_mechanism", "")).strip()
            assets = self._clean_list(data.get("affected_assets", []))
            implications = str(data.get("directional_implications", "")).strip()
            risks = self._clean_list(data.get("uncertainties_and_risks", []))
            facts = self._clean_list(data.get("reported_facts", []))
            hypotheses = self._clean_list(data.get("analytical_hypotheses", []))
            watchpoints = self._clean_list(data.get("catalyst_watchpoints", []))
            horizon = str(data.get("market_impact_horizon", "")).strip()
            risk_level = str(data.get("institutional_risk_level", "")).strip()
            peers = self._clean_list(data.get("peer_impact", []))

            # Compile synthesis text
            summary_parts = []
            if event_summary:
                summary_parts.append(f"**Event Summary:** {event_summary}")
            if transmission:
                summary_parts.append(f"**Transmission Mechanism:** {transmission}")
            if implications:
                summary_parts.append(f"**Market Implications:** {implications}")
            if assets:
                summary_parts.append(f"**Affected Assets:** {', '.join(assets)}")
            if facts:
                summary_parts.append(f"**Reported Facts:** {'; '.join(facts)}")
            if hypotheses:
                summary_parts.append(f"**Analytical Hypotheses:** {'; '.join(hypotheses)}")
            if watchpoints:
                summary_parts.append(f"**Catalysts to Watch:** {'; '.join(watchpoints)}")
            if horizon:
                summary_parts.append(f"**Impact Horizon:** {horizon}")
            if risk_level:
                summary_parts.append(f"**Risk Level:** {risk_level}")
            if peers:
                summary_parts.append(f"**Peer Sensitivity:** {', '.join(peers)}")
            if risks:
                summary_parts.append(f"**Uncertainties / Risks:** {'; '.join(risks)}")

            raw_summary = "\n\n".join(summary_parts) or clean_text

            return StructuredFinancialAnalysis(
                event_summary=event_summary,
                transmission_mechanism=transmission,
                affected_assets=assets,
                directional_implications=implications,
                uncertainties_and_risks=risks,
                reported_facts=facts,
                analytical_hypotheses=hypotheses,
                catalyst_watchpoints=watchpoints,
                market_impact_horizon=horizon,
                institutional_risk_level=risk_level,
                peer_impact=peers,
                raw_summary=raw_summary,
            )
        except Exception:
            return StructuredFinancialAnalysis(
                event_summary=clean_text[:250],
                raw_summary=clean_text,
            )

    @staticmethod
    def _clean_list(val: Any) -> List[str]:
        if isinstance(val, list):
            return [str(v).strip() for v in val if v]
        if isinstance(val, str) and val.strip():
            return [val.strip()]
        return []

    @staticmethod
    def _calculate_cost(model_id: str, prompt_tokens: Optional[int], completion_tokens: Optional[int]) -> float:
        if not prompt_tokens and not completion_tokens:
            return 0.0
        clean_id = model_id.split("/")[-1].lower()
        pricing = GEMINI_PRICING_PER_1M.get(clean_id, GEMINI_PRICING_PER_1M["default"])
        p_cost = ((prompt_tokens or 0) / 1_000_000.0) * pricing["prompt"]
        c_cost = ((completion_tokens or 0) / 1_000_000.0) * pricing["completion"]
        return round(p_cost + c_cost, 6)
