"""
Tests for Analytics Metrics Layer.
"""

import os
import json
import pytest
from src.analytics.metrics import generate_metrics_payload


def test_metrics_payload_structure():
    """Verify the metrics payload contains the expected aggregated keys."""
    payload = generate_metrics_payload()
    
    # Top-level keys
    assert "overall" in payload
    assert isinstance(payload["overall"], dict)
    
    assert "key_findings" in payload
    assert isinstance(payload["key_findings"], dict)
    
    assert "monthly_trend" in payload
    assert isinstance(payload["monthly_trend"], list)
    
    assert "detailed_data" in payload
    assert isinstance(payload["detailed_data"], dict)
    
    # Key findings sub-keys
    expected_findings = [
        "highest_no_show_clinic",
        "highest_no_show_weekday",
        "highest_no_show_time_slot",
        "highest_no_show_appointment_type",
        "highest_no_show_month",
        "lowest_no_show_month"
    ]
    for key in expected_findings:
        assert key in payload["key_findings"], f"Missing key_finding: {key}"


def test_metrics_payload_privacy():
    """Explicitly verify that the AI payload contains zero patient-level fields."""
    payload = generate_metrics_payload()
    
    from src.analytics.metrics import JSONEncoder
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
    """Verify that the data types in the payload are JSON serializable."""
    payload = generate_metrics_payload()
    
    from src.analytics.metrics import JSONEncoder
    # If json.dumps succeeds without error, all types are handled
    json.dumps(payload, cls=JSONEncoder)


def test_metrics_payload_derived_fields():
    """Verify that the real production payload includes the deterministically derived fields
    required by the report builder."""
    payload = generate_metrics_payload()
    
    overall = payload.get("overall", {})
    assert "completed_pct" in overall
    assert "cancelled_pct" in overall
    assert "no_show_pct" in overall
    assert "still_scheduled_pct" in overall
    
    # Check that key findings have difference_from_overall_pp
    key_findings = payload.get("key_findings", {})
    expected_findings = [
        "highest_no_show_clinic",
        "highest_no_show_weekday",
        "highest_no_show_time_slot",
        "highest_no_show_appointment_type",
        "highest_no_show_month",
        "lowest_no_show_month"
    ]
    for key in expected_findings:
        finding = key_findings.get(key, {})
        if finding:  # Only if there is data
            assert "difference_from_overall_pp" in finding, f"{key} missing difference_from_overall_pp"
            
    # Check monthly specific field
    assert "highest_lowest_month_difference_pp" in key_findings, "Missing highest_lowest_month_difference_pp"
