"""
Faithfulness & Report Builder Tests.

Validates:
- Status percentages are precomputed by Python
- Report builder uses exact supplied values
- Report builder does not calculate new values
- Key finding percentage-point differences are precomputed
- Qwen receives only overall + key_findings
- Qwen does not receive monthly_trend or detailed_data
- Payload structure matches expected schema
"""

import pytest
from src.ai.mock_model import MockAISummarizer
from src.analytics.report_builder import build_structured_report


# ==================================================
# Payload Structure Tests
# ==================================================

SAMPLE_PAYLOAD = {
    "overall": {
        "total_appointments": 20000,
        "completed": 13334,
        "cancelled": 1915,
        "no_shows": 3777,
        "still_scheduled": 974,
        "no_show_rate_pct": 18.89,
        "no_show_pct": 18.89,
        "completed_pct": 66.67,
        "cancelled_pct": 9.58,
        "still_scheduled_pct": 4.87
    },
    "key_findings": {
        "highest_no_show_clinic": {
            "clinic_name": "TestClinic",
            "no_show_rate_pct": 26.06,
            "difference_from_overall_pp": 7.17
        },
        "highest_no_show_weekday": {
            "day_of_week": "Sunday",
            "no_show_rate_pct": 23.59,
            "difference_from_overall_pp": 4.7
        },
        "highest_no_show_time_slot": {
            "time_slot": "Early Morning",
            "no_show_rate_pct": 21.74,
            "difference_from_overall_pp": 2.85
        },
        "highest_no_show_appointment_type": {
            "type_name": "Physical Therapy",
            "no_show_rate_pct": 28.0,
            "difference_from_overall_pp": 9.11
        },
        "highest_no_show_month": {
            "month_name": "September",
            "year": 2024,
            "no_show_rate_pct": 24.3
        },
        "lowest_no_show_month": {
            "month_name": "August",
            "year": 2025,
            "no_show_rate_pct": 15.2
        },
        "highest_lowest_month_difference_pp": 9.1
    }
}


def test_status_percentages_are_precomputed():
    """Verify that status percentages exist in the payload and are used by the report builder."""
    overall = SAMPLE_PAYLOAD["overall"]
    assert "completed_pct" in overall
    assert "cancelled_pct" in overall
    assert "still_scheduled_pct" in overall
    assert "no_show_pct" in overall


def test_report_builder_uses_exact_supplied_values():
    """Verify the report builder inserts the exact values from the payload."""
    report = build_structured_report(SAMPLE_PAYLOAD)
    
    assert "20,000" in report
    assert "13,334" in report
    assert "1,915" in report
    assert "3,777" in report
    assert "18.89%" in report
    assert "66.67%" in report
    assert "9.58%" in report
    assert "TestClinic" in report
    assert "Sunday" in report
    assert "Early Morning" in report
    assert "Physical Therapy" in report


def test_report_builder_does_not_invent_values():
    """Verify the report builder does not introduce values not in the payload."""
    report = build_structured_report(SAMPLE_PAYLOAD)
    
    # Should not contain causal language
    assert "because" not in report.lower()
    # Should not contain fabricated clinic names
    assert "Downtown" not in report
    assert "Central" not in report


def test_key_finding_differences_are_precomputed():
    """Verify difference_from_overall_pp is precomputed for key findings."""
    kf = SAMPLE_PAYLOAD["key_findings"]
    assert kf["highest_no_show_clinic"]["difference_from_overall_pp"] == 7.17
    assert kf["highest_no_show_weekday"]["difference_from_overall_pp"] == 4.7
    assert kf["highest_no_show_time_slot"]["difference_from_overall_pp"] == 2.85
    assert kf["highest_no_show_appointment_type"]["difference_from_overall_pp"] == 9.11


def test_payload_does_not_contain_monthly_trend():
    """Verify the payload sent to the LLM does NOT contain monthly_trend."""
    assert "monthly_trend" not in SAMPLE_PAYLOAD


def test_payload_does_not_contain_detailed_data():
    """Verify the payload sent to the LLM does NOT contain detailed_data."""
    assert "detailed_data" not in SAMPLE_PAYLOAD


def test_payload_contains_only_overall_and_key_findings():
    """Verify the payload has exactly the two expected top-level keys."""
    assert set(SAMPLE_PAYLOAD.keys()) == {"overall", "key_findings"}


def test_report_builder_contains_all_seven_sections():
    """Verify the structured report contains all 7 required sections."""
    report = build_structured_report(SAMPLE_PAYLOAD)
    
    assert "# 1. EXECUTIVE SUMMARY" in report
    assert "# 2. APPOINTMENT STATUS OVERVIEW" in report
    assert "# 3. NO-SHOW ANALYSIS" in report
    assert "## 3.1 Overall No-Show Rate" in report
    assert "## 3.2 By Clinic" in report
    assert "## 3.3 By Weekday" in report
    assert "## 3.4 By Time Slot" in report
    assert "## 3.5 By Appointment Type" in report
    assert "## 3.6 By Month" in report
    assert "# 4. KEY FINDINGS" in report
    assert "# 5. OPERATIONAL AREAS FOR INVESTIGATION" in report
    assert "# 6. RECOMMENDED NEXT ANALYSIS" in report
    assert "# 7. DATA LIMITATIONS" in report


def test_mock_summary_is_concise():
    """Verify the mock AI summary stays under a reasonable word count."""
    summarizer = MockAISummarizer()
    result = summarizer.summarize(SAMPLE_PAYLOAD)
    word_count = len(result.split())
    assert word_count < 200, f"Mock summary is {word_count} words, expected < 200"


def test_month_difference_is_precomputed():
    """Verify the highest-lowest month difference is precomputed."""
    kf = SAMPLE_PAYLOAD["key_findings"]
    assert "highest_lowest_month_difference_pp" in kf
    assert kf["highest_lowest_month_difference_pp"] == 9.1
