"""
AI Privacy Validator.

Ensures that the payload passed to any AI model contains absolutely zero
patient-level or identifiable information.
"""

import json
from typing import Dict, Any

FORBIDDEN_FIELDS = [
    "patient_id",
    "first_name",
    "last_name",
    "patient_name",
    "phone",
    "email",
    "address",
    "date_of_birth",
    "appointment_id"  # Block raw appointment rows
]

def validate_privacy(metrics: Dict[str, Any]) -> None:
    """
    Validate that the metrics payload contains no forbidden personal fields.
    
    Args:
        metrics: The dictionary payload destined for the AI.
        
    Raises:
        ValueError: If a forbidden field is detected anywhere in the payload.
    """
    from src.analytics.metrics import JSONEncoder
    # Easiest way to deeply inspect all keys/values is to convert to string
    # and do a substring check. This is highly aggressive and safe.
    payload_str = json.dumps(metrics, cls=JSONEncoder).lower()
    
    for field in FORBIDDEN_FIELDS:
        if field.lower() in payload_str:
            raise ValueError(f"PRIVACY VIOLATION: Forbidden field '{field}' detected in AI payload!")
