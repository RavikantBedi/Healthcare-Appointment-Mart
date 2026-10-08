"""
xAI Grok AI Summarizer.

Uses the official xai-sdk to summarize the privacy-safe metrics payload.
"""

import json
from typing import Dict, Any

from src.config.settings import settings
from src.config.logging_config import get_logger
from src.ai.interface import AISummarizer
from src.ai.privacy import validate_privacy
from src.ai.prompts import SYSTEM_PROMPT

logger = get_logger(__name__)


class GrokAISummarizer(AISummarizer):
    def summarize(self, metrics: Dict[str, Any]) -> str:
        # 1. Enforce privacy boundary
        validate_privacy(metrics)

        api_key = settings.ai.xai_api_key
        model = settings.ai.grok_model

        if not api_key:
            raise RuntimeError(
                "AI backend configuration error: XAI_API_KEY is not set."
            )

        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError(
                "AI backend unavailable: openai package is not installed. "
                "Run: pip install openai"
            )

        from src.analytics.metrics import JSONEncoder

        user_prompt = (
            f"Here is the aggregated JSON data:\n"
            f"{json.dumps(metrics, cls=JSONEncoder, indent=2)}\n\n"
            f"Please provide the summary now."
        )

        try:
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1",
            )

            logger.info(f"Sending metrics payload to Grok (Model: {model})...")

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
            )

            content = response.choices[0].message.content
            if content:
                return content
            else:
                raise RuntimeError(
                    "AI backend error: Grok returned an empty response."
                )

        except RuntimeError:
            raise
        except Exception as e:
            error_msg = str(e)
            # Never expose the API key in logs
            if api_key and api_key in error_msg:
                error_msg = error_msg.replace(api_key, "***")
            raise RuntimeError(f"AI backend unavailable (Grok): {error_msg}")
