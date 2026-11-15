"""
SignalFlow AI - Gemini-Assisted Structured Entity & Context Extractor
Uses Google AI Studio Gemini API for complex, multi-lingual, or ambiguous market context.
Strictly validates all returned ticker symbols against the supported instrument registry
to guarantee hallucinated or unsupported instruments are never accepted.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from google.genai import types

from src.gemini_service import GeminiService
from src.ticker_detection.registry import instrument_registry, InstrumentRegistry
from src.ticker_detection.models import DetectedEntity, AffectedInstrument, TickerDetectionResult

logger = logging.getLogger(__name__)


class GeminiEntityExtractor:
    """
    Cloud-assisted entity extractor using Google Gemini for ambiguous macro context.
    Enforces rigid schema validation and supported instrument whitelisting.
    """

    def __init__(
        self,
        gemini_service: Optional[GeminiService] = None,
        registry: Optional[InstrumentRegistry] = None,
    ):
        self.gemini = gemini_service or GeminiService()
        self.registry = registry or instrument_registry

    def extract_with_gemini(
        self,
        headline: str,
        body: str = "",
        article_id: str = "",
    ) -> Optional[TickerDetectionResult]:
        """
        Executes structured entity extraction with Google Gemini and strictly filters
        against supported instruments.
        """
        status = self.gemini.check_credentials_status()
        if not status.get("configured", False):
            logger.info("Gemini credentials not configured; skipping Gemini-assisted extraction.")
            return None

        client = None
        try:
            client = self.gemini._get_client()
        except Exception as e:
            logger.warning(f"Failed to acquire Gemini client: {e}")
            return None

        supported_symbols = self.registry.get_all_supported_symbols()
        supported_list_str = ", ".join(supported_symbols)

        system_instruction = (
            "You are SignalFlow AI's financial NLP entity extraction specialist. "
            "Analyze the news headline and body to identify financial entities and affected forex instruments. "
            f"You may ONLY select instruments from this supported list: [{supported_list_str}]. "
            "Never invent or output ticker symbols not in this list. "
            "Classify relationships into:\n"
            "- 'direct': Explicitly named in the article\n"
            "- 'indirect': Defensible macroeconomic transmission channel (e.g. rate changes, central bank policy)\n"
            "- 'potential': Uncertain or secondary correlation\n\n"
            "Return valid JSON matching this schema:\n"
            "{\n"
            "  \"detected_entities\": [{\"name\": \"string\", \"entity_type\": \"forex_pair|currency|central_bank|economic_indicator|commodity\", \"mention_type\": \"explicit|implicit|contextual\"}],\n"
            "  \"affected_instruments\": [{\"symbol\": \"string\", \"relationship\": \"direct|indirect|potential\", \"confidence\": 0.0-1.0, \"reason\": \"string\", \"mentioned_explicitly\": true|false}],\n"
            "  \"currencies\": [\"USD\", \"EUR\"],\n"
            "  \"economic_events\": [\"interest_rate_decision\", \"cpi_release\"]\n"
            "}"
        )

        content_str = f"Headline: {headline}\nBody: {body}" if body else f"Headline: {headline}"

        config_params = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            max_output_tokens=700,
            response_mime_type="application/json",
        )

        try:
            response = client.models.generate_content(
                model=self.gemini.model_id,
                contents=content_str,
                config=config_params,
            )

            raw_text = response.text or "{}"
            data = json.loads(raw_text)

            # Validate and filter entities
            valid_entities: List[DetectedEntity] = []
            for item in data.get("detected_entities", []):
                try:
                    valid_entities.append(
                        DetectedEntity(
                            name=str(item.get("name", "")),
                            entity_type=item.get("entity_type", "currency"),
                            mention_type=item.get("mention_type", "implicit"),
                            confidence=float(item.get("confidence", 0.9)),
                        )
                    )
                except Exception:
                    continue

            # Strictly validate affected instruments against registry
            valid_instruments: List[AffectedInstrument] = []
            for inst in data.get("affected_instruments", []):
                sym = inst.get("symbol", "")
                norm_sym = self.registry.normalize_symbol(sym)
                if not norm_sym or not self.registry.is_supported(norm_sym):
                    logger.debug(f"Rejecting unsupported symbol from Gemini output: {sym}")
                    continue  # Strict rejection of unsupported symbols

                try:
                    valid_instruments.append(
                        AffectedInstrument(
                            symbol=norm_sym,
                            relationship=inst.get("relationship", "indirect"),
                            confidence=max(0.0, min(1.0, float(inst.get("confidence", 0.8)))),
                            reason=str(inst.get("reason", "Macroeconomic transmission channel.")),
                            mentioned_explicitly=bool(inst.get("mentioned_explicitly", False)),
                        )
                    )
                except Exception:
                    continue

            return TickerDetectionResult(
                article_id=article_id,
                detected_entities=valid_entities,
                affected_instruments=valid_instruments,
                currencies=list(set(data.get("currencies", []))),
                economic_events=list(set(data.get("economic_events", []))),
            )

        except Exception as e:
            logger.warning(f"Gemini entity extraction failed: {e}")
            return None

