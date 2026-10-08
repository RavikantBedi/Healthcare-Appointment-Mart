"""
AI Summarizer Factory.

Instantiates the correct AI backend based on environment configuration.

Supported backends:
    mock    → MockAISummarizer    (default, offline, deterministic)
    ollama  → OllamaAISummarizer  (local LLM via HTTP)
    gemini  → GeminiAISummarizer  (Google Gemini API, key required)
    grok    → GrokAISummarizer    (xAI Grok API, key required)
"""

from src.config.settings import settings
from src.ai.interface import AISummarizer
from src.config.logging_config import get_logger

logger = get_logger(__name__)

_VALID_BACKENDS = {"mock", "ollama", "gemini", "grok"}


def get_summarizer() -> AISummarizer:
    """Return the configured AI summarizer backend."""
    backend = settings.ai.backend.lower()

    if backend not in _VALID_BACKENDS:
        raise ValueError(
            f"Unknown AI_BACKEND='{backend}'. "
            f"Valid options: {', '.join(sorted(_VALID_BACKENDS))}"
        )

    if backend == "ollama":
        from src.ai.ollama_model import OllamaAISummarizer
        logger.info("Initializing Ollama AI backend.")
        return OllamaAISummarizer()

    elif backend == "gemini":
        from src.ai.gemini_model import GeminiAISummarizer
        logger.info("Initializing Gemini AI backend.")
        return GeminiAISummarizer()

    elif backend == "grok":
        from src.ai.grok_model import GrokAISummarizer
        logger.info("Initializing Grok AI backend.")
        return GrokAISummarizer()

    else:  # mock (default)
        from src.ai.mock_model import MockAISummarizer
        logger.info("Initializing Mock AI backend.")
        return MockAISummarizer()
