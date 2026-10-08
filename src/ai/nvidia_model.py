"""
NVIDIA AI Summarizer.

Uses the OpenAI-compatible NVIDIA API to summarize the privacy-safe metrics payload.
"""

import json
from typing import Dict, Any

from src.config.settings import settings
from src.config.logging_config import get_logger
from src.ai.interface import AISummarizer
from src.ai.privacy import validate_privacy
from src.ai.prompts import SYSTEM_PROMPT

logger = get_logger(__name__)


class NvidiaAISummarizer(AISummarizer):
    def summarize(self, metrics: Dict[str, Any]) -> str:
        # 1. Enforce privacy boundary
        validate_privacy(metrics)

        api_key = settings.ai.nvidia_api_key
        model = settings.ai.nvidia_model

        if not api_key:
            raise RuntimeError(
                "AI backend configuration error: NVIDIA_API_KEY is not set."
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
                base_url="https://integrate.api.nvidia.com/v1",
            )

            logger.info(f"Sending metrics payload to NVIDIA API (Model: {model})...")

            # The user provided a streaming example, but the AISummarizer contract
            # expects a single returned string. We will consume the stream and concatenate.
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                top_p=1,
                max_tokens=1024,
                stream=True
            )

            summary_chunks = []
            for chunk in completion:
                if not getattr(chunk, "choices", None):
                    continue
                if chunk.choices[0].delta.content is not None:
                    summary_chunks.append(chunk.choices[0].delta.content)
            
            content = "".join(summary_chunks)

            if content:
                return content
            else:
                raise RuntimeError(
                    "AI backend error: NVIDIA API returned an empty response."
                )

        except RuntimeError:
            raise
        except Exception as e:
            error_msg = str(e)
            # Never expose the API key in logs
            if api_key and api_key in error_msg:
                error_msg = error_msg.replace(api_key, "***")
            raise RuntimeError(f"AI backend unavailable (NVIDIA): {error_msg}")
