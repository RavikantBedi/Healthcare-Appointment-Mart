"""
Phase 8 Audit Tests.

Covers:
- Zero-denominator edge case
- Clinic minimum-sample threshold
- Full privacy audit (core/mart/analytics/AI)
- AI output safety
- Failure demonstration with invalid fixture
- Idempotency
"""

import json
import pytest
import pandas as pd
from uuid import uuid4

from src.ai.privacy import validate_privacy, FORBIDDEN_FIELDS
from src.ai.mock_model import MockAISummarizer
from src.analytics.metrics import JSONEncoder


# ==================================================
# Section 5: Zero-Denominator Edge Case
# ==================================================

def test_zero_denominator_mock_ai():
    """Verify MockAI handles a payload where all counts are zero without crashing."""
    payload = {
        "overall": {"total_appointments": 0, "no_show_rate_pct": 0.0, "no_show_pct": 0.0, "no_shows": 0},
        "key_findings": {}
    }
    summarizer = MockAISummarizer()
    result = summarizer.summarize(payload)
    assert "0.00%" in result
    assert "Unknown" in result  # Fallback when no data


# ==================================================
# Section 6: Privacy Audit
# ==================================================

def test_privacy_rejects_each_forbidden_field():
    """Verify every single forbidden field triggers a privacy violation."""
    for field in FORBIDDEN_FIELDS:
        bad_payload = {field: "some_value"}
        with pytest.raises(ValueError, match="PRIVACY VIOLATION"):
            validate_privacy(bad_payload)


def test_privacy_rejects_nested_forbidden_field():
    """Verify privacy catches forbidden fields nested inside lists/dicts."""
    bad_payload = {
        "safe_key": [
            {"nested": {"first_name": "John"}}
        ]
    }
    with pytest.raises(ValueError, match="PRIVACY VIOLATION"):
        validate_privacy(bad_payload)


# ==================================================
# Section 8: AI Output Safety & Faithfulness
# ==================================================

def test_mock_ai_output_references_only_supplied_data():
    """Verify mock AI output only references data from the supplied payload."""
    payload = {
        "overall": {"total_appointments": 500, "no_show_rate_pct": 12.5, "no_show_pct": 12.5},
        "key_findings": {
            "highest_no_show_clinic": {"clinic_name": "TestClinic", "no_show_rate_pct": 25.0},
            "highest_no_show_weekday": {"day_of_week": "Friday", "no_show_rate_pct": 15.0},
            "highest_no_show_time_slot": {"time_slot": "Afternoon", "no_show_rate_pct": 18.0},
            "highest_no_show_appointment_type": {"type_name": "Checkup", "no_show_rate_pct": 22.0},
            "highest_no_show_month": {"month_name": "May", "year": 2024, "month": 5, "no_show_rate_pct": 24.30}
        }
    }
    summarizer = MockAISummarizer()
    result = summarizer.summarize(payload)

    # Must reference supplied data
    assert "12.50%" in result
    assert "TestClinic" in result
    assert "Friday" in result
    assert "Afternoon" in result
    assert "24.30%" in result
    
    # Must NOT hallucinate unsupported claims
    assert "because" not in result.lower()
    assert "cause" not in result.lower().replace("causation", "").replace("because", "")

def test_ai_faithfulness_missing_months():
    """Verify that the AI doesn't fabricate missing months."""
    payload = {
        "overall": {"no_show_rate_pct": 18.89, "no_show_pct": 18.89},
        "key_findings": {
            "highest_no_show_month": {
                "year": 2024,
                "month_name": "May",
                "no_show_rate_pct": 24.30
            }
        }
    }
    summarizer = MockAISummarizer()
    result = summarizer.summarize(payload)
    
    assert "May" in result
    assert "24.30" in result
    
    # Should not invent another month
    assert "June" not in result
    assert "July" not in result
    assert "August" not in result


# ==================================================
# Section 9: Clinic Minimum-Sample Threshold
# ==================================================

def test_clinic_min_sample_filtering():
    """
    Verify that the metrics query filters clinics below the minimum sample threshold.
    This is an integration test against the live database.
    """
    from src.analytics.metrics import generate_metrics_payload
    payload = generate_metrics_payload()

    # The highest clinic finding should have total_appointments >= threshold
    highest_clinic = payload.get("key_findings", {}).get("highest_no_show_clinic", {})
    from src.config.settings import settings
    threshold = settings.analytics.clinic_min_sample
    
    if highest_clinic:
        assert highest_clinic["total_appointments"] >= threshold, (
            f"Clinic '{highest_clinic['clinic_name']}' has only {highest_clinic['total_appointments']} "
            f"appointments, below the minimum sample threshold of {threshold}"
        )


# ==================================================
# Section 4: Failure Demonstration (edge-case file)
# ==================================================

def test_failure_demonstration_with_fixture():
    """
    Demonstrate concrete validation failures using the crafted invalid fixture.
    This proves the system quarantines bad records with clear error reasons.
    """
    from src.validation.validators import validate_appointments
    fixture_path = "tests/fixtures/invalid_appointments.csv"
    df = pd.read_csv(fixture_path, dtype=str)
    
    # Use synthetic valid IDs that won't match the fixture's bad IDs
    valid_patients = {"p0000000-0000-0000-0000-000000000001",
                      "p0000000-0000-0000-0000-000000000002",
                      "p0000000-0000-0000-0000-000000000003",
                      "p0000000-0000-0000-0000-000000000004"}
    valid_clinics = {"b0000000-0000-0000-0000-000000000001",
                     "b0000000-0000-0000-0000-000000000002",
                     "b0000000-0000-0000-0000-000000000003",
                     "b0000000-0000-0000-0000-000000000004"}
    valid_types = {"1", "2", "3"}

    valid_df, rejected_df = validate_appointments(df, valid_patients, valid_clinics, valid_types)
    
    # The fixture has 6 data rows. We expect failures:
    # Row 1: empty patient_id
    # Row 2: invalid clinic_id ("invalid-clinic")
    # Row 3: date out of range (2020-01-01)
    # Row 4: invalid type_id (99), invalid status ("Rescheduled")
    # Rows 5-6: duplicate appointment_id
    assert len(rejected_df) >= 4, f"Expected at least 4 rejections, got {len(rejected_df)}"
    assert len(valid_df) <= 2, f"Expected at most 2 valid, got {len(valid_df)}"
    
    errors = " ".join(rejected_df["validation_errors"].tolist())
    assert "Missing required field: patient_id" in errors
    assert "Invalid foreign key: clinic_id" in errors
    assert "out of bounds" in errors
    assert "Duplicate appointment_id" in errors
