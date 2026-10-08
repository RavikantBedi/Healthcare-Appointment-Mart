"""
Google Gemini AI Summarizer.

Uses the official google-genai SDK to summarize the privacy-safe metrics payload.
"""

import json
from typing import Dict, Any

from src.config.settings import settings
from src.config.logging_config import get_logger
from src.ai.interface import AISummarizer
from src.ai.privacy import validate_privacy
from src.ai.prompts import SYSTEM_PROMPT

logger = get_logger(__name__)


class GeminiAISummarizer(AISummarizer):
    def summarize(self, metrics: Dict[str, Any]) -> str:
        # 1. Enforce privacy boundary
        validate_privacy(metrics)

        api_key = settings.ai.gemini_api_key
        model = settings.ai.gemini_model

        if not api_key:
            raise RuntimeError(
                "AI backend configuration error: GEMINI_API_KEY is not set."
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise RuntimeError(
                "AI backend unavailable: google-genai package is not installed. "
                "Run: pip install google-genai"
            )

        from src.analytics.metrics import JSONEncoder

        user_prompt = (
            f"Here is the aggregated JSON data:\n"
            f"{json.dumps(metrics, cls=JSONEncoder, indent=2)}\n\n"
            f"Please provide the summary now."
        )

        try:
            client = genai.Client(api_key=api_key)

            logger.info(f"Sending metrics payload to Gemini (Model: {model})...")

            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.3,
                    max_output_tokens=1024,
                ),
            )

            if response.text:
                return response.text
            else:
                raise RuntimeError(
                    "AI backend error: Gemini returned an empty response."
                )

        except RuntimeError:
            raise
        except Exception as e:
            error_msg = str(e)
            # Never expose the API key in logs
            if api_key and api_key in error_msg:
                error_msg = error_msg.replace(api_key, "***")
            raise RuntimeError(f"AI backend unavailable (Gemini): {error_msg}")
