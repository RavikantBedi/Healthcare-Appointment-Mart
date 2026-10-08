"""
Tests: AI System Prompt Integration Contract

Verifies that:
1. OllamaAISummarizer uses the centralized SYSTEM_PROMPT from prompts.py.
2. The old 7-section report format is NOT present in the Ollama HTTP request.
3. Ollama receives ONLY 'overall' and 'key_findings' — no raw arrays.
4. 'monthly_trend' is NOT sent to the LLM.
5. 'detailed_data' is NOT sent to the LLM.
6. Privacy validation runs BEFORE the Ollama HTTP request.
7. Mock backend still works correctly.
8. Ollama fallback behavior still works (RuntimeError on connection failure).

All Ollama HTTP calls are mocked — no real Ollama server is required.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from src.ai.prompts import SYSTEM_PROMPT
from src.ai.ollama_model import OllamaAISummarizer
from src.ai.mock_model import MockAISummarizer
from src.ai.privacy import validate_privacy


# ---------------------------------------------------------------------------
# Fixture: a full metrics payload (as generated_metrics_payload() would return)
# ---------------------------------------------------------------------------
@pytest.fixture
def full_payload():
    """Simulates the complete payload from generate_metrics_payload()."""
    return {
        "overall": {
            "total_appointments": 20000,
            "completed": 14500,
            "cancelled": 1720,
            "no_shows": 3780,
            "still_scheduled": 0,
            "no_show_rate_pct": 18.90,
        },
        "key_findings": {
            "highest_no_show_clinic": {
                "clinic_name": "Westside Medical Center",
                "no_show_rate_pct": 26.06,
                "difference_from_overall_pp": 7.17,
            },
            "highest_no_show_weekday": {
                "day_of_week": "Wednesday",
                "no_show_rate_pct": 20.50,
                "difference_from_overall_pp": 1.60,
            },
            "highest_no_show_time_slot": {
                "time_slot": "Early Morning",
                "no_show_rate_pct": 21.30,
                "difference_from_overall_pp": 2.40,
            },
            "highest_no_show_appointment_type": {
                "type_name": "New Patient",
                "no_show_rate_pct": 22.10,
                "difference_from_overall_pp": 3.20,
            },
            "highest_no_show_month": {
                "year": 2024,
                "month": 8,
                "month_name": "August",
                "no_show_rate_pct": 21.80,
            },
            "lowest_no_show_month": {
                "year": 2023,
                "month": 11,
                "month_name": "November",
                "no_show_rate_pct": 15.40,
            },
        },
        # These keys must NOT reach the LLM
        "monthly_trend": [
            {"year": 2023, "month": 1, "no_show_rate_pct": 18.0},
            {"year": 2023, "month": 2, "no_show_rate_pct": 19.5},
        ],
        "detailed_data": {
            "clinics": [{"clinic_name": "Clinic A", "no_show_rate_pct": 20.0}],
            "weekdays": [{"day_of_week": "Monday", "no_show_rate_pct": 19.0}],
            "time_slots": [{"time_slot": "Morning", "no_show_rate_pct": 18.5}],
            "appointment_types": [{"type_name": "Follow-up", "no_show_rate_pct": 17.0}],
        },
    }


# ---------------------------------------------------------------------------
# Helper: capture the HTTP payload sent to Ollama
# ---------------------------------------------------------------------------
def _mock_ollama_call(full_payload):
    """Run OllamaAISummarizer.summarize() with a mocked requests.post.
    Returns (captured_request_payload, summary_text)."""
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["payload"] = json
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "MOCKED SUMMARY"}
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    with patch("src.ai.ollama_model.requests.post", side_effect=fake_post):
        summarizer = OllamaAISummarizer()
        result = summarizer.summarize(full_payload)

    return captured["payload"], result


# ===========================================================================
# TEST 1: OllamaAISummarizer uses the centralized SYSTEM_PROMPT
# ===========================================================================
def test_ollama_uses_centralized_system_prompt(full_payload):
    """The prompt sent to Ollama must contain the centralized SYSTEM_PROMPT verbatim."""
    request_payload, _ = _mock_ollama_call(full_payload)

    sent_prompt = request_payload["prompt"]
    # The centralized SYSTEM_PROMPT must appear in the prompt string
    assert SYSTEM_PROMPT in sent_prompt, (
        "SYSTEM_PROMPT from prompts.py is not present in the Ollama request prompt."
    )


# ===========================================================================
# TEST 2: Old 7-section report format is NOT present
# ===========================================================================
def test_old_7_section_report_not_in_prompt(full_payload):
    """Banned structural sections from the old report format must not appear."""
    request_payload, _ = _mock_ollama_call(full_payload)

    sent_prompt = request_payload["prompt"]

    forbidden_fragments = [
        "APPOINTMENT STATUS OVERVIEW",
        "NO-SHOW ANALYSIS",
        "3.1 Overall No-Show Rate",
        "OPERATIONAL AREAS FOR INVESTIGATION",
        "RECOMMENDED NEXT ANALYSIS",
        "REPORT FORMAT",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in sent_prompt, (
            f"Old 7-section report instruction '{fragment}' must NOT be in the Ollama prompt."
        )


# ===========================================================================
# TEST 3: Ollama receives ONLY 'overall' and 'key_findings'
# ===========================================================================
def test_ollama_receives_only_overall_and_key_findings(full_payload):
    """The condensed payload embedded in the LLM prompt must only have 'overall' and 'key_findings'."""
    request_payload, _ = _mock_ollama_call(full_payload)

    sent_prompt = request_payload["prompt"]

    # Extract the JSON portion from the prompt — it is between 'Here are the precomputed findings:\n' and '\n\nSummarize'
    start_marker = "Here are the precomputed findings:\n"
    end_marker = "\n\nSummarize these findings now."
    start_idx = sent_prompt.index(start_marker) + len(start_marker)
    end_idx = sent_prompt.index(end_marker)
    condensed_json_str = sent_prompt[start_idx:end_idx]

    condensed = json.loads(condensed_json_str)
    assert set(condensed.keys()) == {"overall", "key_findings"}, (
        f"Expected exactly {{'overall', 'key_findings'}} in condensed payload, "
        f"got: {set(condensed.keys())}"
    )


# ===========================================================================
# TEST 4: 'monthly_trend' is NOT sent to Ollama
# ===========================================================================
def test_monthly_trend_not_sent_to_ollama(full_payload):
    """monthly_trend must be stripped from the condensed payload before sending to LLM."""
    request_payload, _ = _mock_ollama_call(full_payload)

    sent_prompt = request_payload["prompt"]

    # Extract condensed JSON
    start_marker = "Here are the precomputed findings:\n"
    end_marker = "\n\nSummarize these findings now."
    start_idx = sent_prompt.index(start_marker) + len(start_marker)
    end_idx = sent_prompt.index(end_marker)
    condensed = json.loads(sent_prompt[start_idx:end_idx])

    assert "monthly_trend" not in condensed, (
        "'monthly_trend' must NOT be included in the condensed payload sent to Ollama."
    )


# ===========================================================================
# TEST 5: 'detailed_data' is NOT sent to Ollama
# ===========================================================================
def test_detailed_data_not_sent_to_ollama(full_payload):
    """detailed_data must be stripped from the condensed payload before sending to LLM."""
    request_payload, _ = _mock_ollama_call(full_payload)

    sent_prompt = request_payload["prompt"]

    start_marker = "Here are the precomputed findings:\n"
    end_marker = "\n\nSummarize these findings now."
    start_idx = sent_prompt.index(start_marker) + len(start_marker)
    end_idx = sent_prompt.index(end_marker)
    condensed = json.loads(sent_prompt[start_idx:end_idx])

    assert "detailed_data" not in condensed, (
        "'detailed_data' must NOT be included in the condensed payload sent to Ollama."
    )


# ===========================================================================
# TEST 6: Privacy validation runs BEFORE the HTTP request
# ===========================================================================
def test_privacy_validation_runs_before_ollama_request():
    """If the payload contains a forbidden PII field, the HTTP request must never be made."""
    pii_payload = {
        "overall": {"total_appointments": 100},
        "key_findings": {},
        "patient_id": "PAT-001",  # Forbidden
    }

    call_made = {"value": False}

    def fake_post(*args, **kwargs):
        call_made["value"] = True
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "should not reach here"}
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    with patch("src.ai.ollama_model.requests.post", side_effect=fake_post):
        summarizer = OllamaAISummarizer()
        with pytest.raises(ValueError, match="PRIVACY VIOLATION"):
            summarizer.summarize(pii_payload)

    assert not call_made["value"], (
        "HTTP request to Ollama must NOT be made when privacy validation fails."
    )


# ===========================================================================
# TEST 7: Mock backend still works correctly
# ===========================================================================
def test_mock_backend_still_works(full_payload):
    """MockAISummarizer must still return a deterministic summary from the same payload shape."""
    mock = MockAISummarizer()
    result = mock.summarize(full_payload)

    assert isinstance(result, str)
    assert len(result) > 0
    # Must reference actual values
    assert "18.9" in result or "18.90" in result  # overall no-show rate
    assert "Westside Medical Center" in result
    assert "synthetic data" in result.lower() or "synthetic" in result.lower()


# ===========================================================================
# TEST 8: Ollama fallback raises RuntimeError (no real server needed)
# ===========================================================================
def test_ollama_fallback_raises_runtime_error(full_payload):
    """When Ollama is unreachable, OllamaAISummarizer must raise RuntimeError."""
    import requests as req

    def fail_post(*args, **kwargs):
        raise req.exceptions.ConnectionError("refused")

    with patch("src.ai.ollama_model.requests.post", side_effect=fail_post):
        summarizer = OllamaAISummarizer()
        with pytest.raises(RuntimeError, match="AI backend unavailable"):
            summarizer.summarize(full_payload)


# ===========================================================================
# TEST 9: SYSTEM_PROMPT does NOT contain old 7-section report instructions
# ===========================================================================
def test_system_prompt_has_no_old_report_format_sections():
    """The centralized SYSTEM_PROMPT must not contain any of the old 7-section headers."""
    forbidden_in_prompt = [
        "APPOINTMENT STATUS OVERVIEW",
        "NO-SHOW ANALYSIS",
        "3.1 Overall No-Show Rate",
        "3.2 By Clinic",
        "3.3 By Weekday",
        "3.4 By Time Slot",
        "3.5 By Appointment Type",
        "3.6 By Month",
        "OPERATIONAL AREAS FOR INVESTIGATION",
        "RECOMMENDED NEXT ANALYSIS",
        "REPORT FORMAT",
    ]
    for section in forbidden_in_prompt:
        assert section not in SYSTEM_PROMPT, (
            f"Old 7-section instruction '{section}' must NOT appear in SYSTEM_PROMPT."
        )


# ===========================================================================
# TEST 10: SYSTEM_PROMPT contains the required 4-section output instructions
# ===========================================================================
def test_system_prompt_contains_required_four_sections():
    """The SYSTEM_PROMPT must instruct the LLM to output exactly the four required sections."""
    required_sections = [
        "EXECUTIVE SUMMARY",
        "KEY OBSERVED PATTERNS",
        "OPERATIONAL OBSERVATION",
        "LIMITATION",
    ]
    for section in required_sections:
        assert section in SYSTEM_PROMPT, (
            f"Required output section '{section}' is missing from SYSTEM_PROMPT."
        )
