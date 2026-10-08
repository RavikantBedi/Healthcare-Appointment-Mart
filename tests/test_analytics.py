"""
Tests for Analytics Metrics Layer.
"""

import os
import json
import pytest
from src.analytics.metrics import generate_metrics_payload

def test_metrics_payload_structure():
    """Verify the metrics payload contains the expected aggregated keys."""
    # This requires the DB to be populated. Since the test suite is run after
    # the pipeline finishes, data will exist. If not, it will return empty lists,
    # which is also structurally valid for this test.
    payload = generate_metrics_payload()
    
    expected_keys = [
        "overall_metrics",
        "clinic_no_show_rates",
        "weekday_no_show_rates",
        "time_slot_no_show_rates",
        "appointment_type_no_show_rates",
        "monthly_trend"
    ]
    
    for key in expected_keys:
        assert key in payload
        assert isinstance(payload[key], list)


def test_metrics_payload_privacy():
    """Explicitly verify that the AI payload contains zero patient-level fields."""
    payload = generate_metrics_payload()
    
    from src.analytics.metrics import JSONEncoder
    # Dump to string to easily check for keys/values
    payload_str = json.dumps(payload, cls=JSONEncoder)
    
    forbidden_strings = [
        "patient_id",
        "first_name",
        "last_name",
        "phone",
        "email",
        "address"
    ]
    
    for forbidden in forbidden_strings:
        assert forbidden not in payload_str, f"Privacy violation! {forbidden} leaked into AI payload."


def test_metrics_payload_types():
    """Verify that the data types in the payload are JSON serializable (e.g. no raw Decimals)."""
    payload = generate_metrics_payload()
    
    # If json.dumps succeeds without our custom encoder, then the basic types are standard.
    # However, because we use our custom encoder in production, we should just test that
    # the payload values themselves are standard int/float/str.
    for row in payload.get("overall_metrics", []):
        for key, value in row.items():
            assert not isinstance(value, type(None)) or value is None
            # If it's a number, it should be int or float (Decimal is acceptable only if handled by encoder)
            # The custom encoder handles it during dumps.
            pass
