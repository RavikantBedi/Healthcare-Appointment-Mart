"""
AI Summarizer Factory.

Instantiates the correct AI backend based on environment configuration.
"""

from src.config.settings import settings
from src.ai.interface import AISummarizer
from src.ai.mock_model import MockAISummarizer
from src.ai.ollama_model import OllamaAISummarizer
from src.config.logging_config import get_logger

logger = get_logger(__name__)

def get_summarizer() -> AISummarizer:
    """Return the configured AI summarizer backend."""
    backend = settings.ai.backend.lower()
    
    if backend == "ollama":
        logger.info("Initializing Ollama AI backend.")
        return OllamaAISummarizer()
    else:
        logger.info("Initializing Mock AI backend.")
        return MockAISummarizer()
