"""
AI Summarizer Interface.

Defines the contract for AI backends to summarize aggregated metrics.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class AISummarizer(ABC):
    """
    Abstract base class for AI summarization backends.
    All AI implementations must conform to this interface.
    """
    
    @abstractmethod
    def summarize(self, metrics: Dict[str, Any]) -> str:
        """
        Generate a human-readable operational summary from aggregated metrics.
        
        Args:
            metrics: A dictionary containing aggregated analytics data.
                     MUST NOT contain patient-level personal data.
                     
        Returns:
            A concise, formatted summary string.
            
        Raises:
            ValueError: If the metrics payload violates privacy constraints.
            RuntimeError: If the backend is unavailable or fails.
        """
        pass
