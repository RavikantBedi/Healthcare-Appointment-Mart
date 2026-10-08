"""
Manual integration test for the Grok AI provider.

Usage:
    set XAI_API_KEY=your_key
    set AI_BACKEND=grok
    python -m scripts.test_grok
"""

import sys
import os
from src.ai.grok_model import GrokAISummarizer
from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)

def main():
    if not settings.ai.xai_api_key:
        logger.error("XAI_API_KEY environment variable is missing.")
        sys.exit(1)

    payload = {
        "overall_metrics": [{"total_appointments": 100, "no_show_rate_pct": 20.0}],
        "clinic_no_show_rates": [{"clinic_name": "Test Clinic", "no_show_rate_pct": 25.0}]
    }

    logger.info("Initializing Grok backend...")
    summarizer = GrokAISummarizer()
    
    logger.info("Sending payload to Grok...")
    try:
        summary = summarizer.summarize(payload)
        print("\n=== Grok Summary ===")
        print(summary)
        print("======================\n")
        logger.info("Test successful.")
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    main()
