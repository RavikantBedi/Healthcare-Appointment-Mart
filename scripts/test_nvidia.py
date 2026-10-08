"""
Manual integration test for the NVIDIA AI provider.

Usage:
    set NVIDIA_API_KEY=your_key
    set AI_BACKEND=nvidia
    python -m scripts.test_nvidia
"""

import sys
import os
from src.ai.nvidia_model import NvidiaAISummarizer
from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)

def main():
    if not settings.ai.nvidia_api_key:
        logger.error("NVIDIA_API_KEY environment variable is missing.")
        sys.exit(1)

    payload = {
        "overall_metrics": [{"total_appointments": 100, "no_show_rate_pct": 20.0}],
        "clinic_no_show_rates": [{"clinic_name": "Test Clinic", "no_show_rate_pct": 25.0}]
    }

    logger.info("Initializing NVIDIA backend...")
    summarizer = NvidiaAISummarizer()
    
    logger.info("Sending payload to NVIDIA API...")
    try:
        summary = summarizer.summarize(payload)
        print("\n=== NVIDIA Summary ===")
        print(summary)
        print("======================\n")
        logger.info("Test successful.")
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    main()
