"""
Tests for AI Summarization Interface.
"""

import pytest
from src.ai.privacy import validate_privacy
from src.ai.mock_model import MockAISummarizer
from src.ai.ollama_model import OllamaAISummarizer
from src.ai.interface import AISummarizer

def test_privacy_validator_rejects_forbidden():
    """Verify that the privacy validator raises an error on PII."""
    bad_payload = {
        "metrics": [{"total": 100}],
        "some_metadata": {"patient_id": "123-abc"}
    }
    with pytest.raises(ValueError, match="PRIVACY VIOLATION"):
        validate_privacy(bad_payload)
        
    bad_payload_2 = {"first_name": "John"}
    with pytest.raises(ValueError, match="PRIVACY VIOLATION"):
        validate_privacy(bad_payload_2)

def test_privacy_validator_accepts_valid():
    """Verify that safe aggregated data passes validation."""
    good_payload = {
        "overall_metrics": [{"total_appointments": 20000, "no_show_rate_pct": 14.5}]
    }
    # Should not raise
    validate_privacy(good_payload)

def test_interface_contract():
    """Verify the summarizers implement the AISummarizer abstract interface."""
    mock = MockAISummarizer()
    assert isinstance(mock, AISummarizer)
    
    ollama = OllamaAISummarizer()
    assert isinstance(ollama, AISummarizer)

def test_mock_summarizer_deterministic():
    """Verify MockAISummarizer generates a deterministic summary without network."""
    payload = {
        "overall_metrics": [{"total_appointments": 20000, "no_show_rate_pct": 14.5}],
        "clinic_no_show_rates": [{"clinic_name": "Clinic A", "no_show_rate_pct": 20.0}],
        "weekday_no_show_rates": [{"day_of_week": "Monday", "no_show_rate_pct": 18.0}],
        "time_slot_no_show_rates": [{"time_slot": "Evening", "no_show_rate_pct": 19.0}]
    }
    
    summarizer = MockAISummarizer()
    result1 = summarizer.summarize(payload)
    result2 = summarizer.summarize(payload)
    
    assert result1 == result2
    assert "14.5%" in result1
    assert "Clinic A" in result1
    assert "Monday" in result1
    assert "Evening" in result1
    # Check for hallucination control phrasing
    assert "synthetic data" in result1.lower()
    assert "do not establish causation" in result1.lower()

def test_ollama_fallback_unavailable(monkeypatch):
    """Verify Ollama throws RuntimeError when network is down instead of generic exception."""
    # We can test this by forcing the host to an invalid endpoint
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:9999") # Assuming 9999 is dead
    
    summarizer = OllamaAISummarizer()
    payload = {"overall_metrics": [{"total_appointments": 100}]}
    
    # It should raise RuntimeError, not crash with raw requests.ConnectionError
    with pytest.raises(RuntimeError, match="AI backend unavailable"):
        summarizer.summarize(payload)

def test_gemini_interface_contract():
    from src.ai.gemini_model import GeminiAISummarizer
    assert isinstance(GeminiAISummarizer(), AISummarizer)

def test_grok_interface_contract():
    from src.ai.grok_model import GrokAISummarizer
    assert isinstance(GrokAISummarizer(), AISummarizer)

def test_factory_selects_gemini(monkeypatch):
    from src.ai.factory import get_summarizer
    from src.ai.gemini_model import GeminiAISummarizer
    from src.config.settings import Settings, AISettings
    
    # Create a new settings object with the desired backend
    mock_settings = Settings(ai=AISettings(backend="gemini"))
    monkeypatch.setattr("src.ai.factory.settings", mock_settings)
    
    summarizer = get_summarizer()
    assert isinstance(summarizer, GeminiAISummarizer)

def test_factory_selects_grok(monkeypatch):
    from src.ai.factory import get_summarizer
    from src.ai.grok_model import GrokAISummarizer
    from src.config.settings import Settings, AISettings
    
    mock_settings = Settings(ai=AISettings(backend="grok"))
    monkeypatch.setattr("src.ai.factory.settings", mock_settings)
    
    summarizer = get_summarizer()
    assert isinstance(summarizer, GrokAISummarizer)

def test_gemini_missing_key(monkeypatch):
    from src.ai.gemini_model import GeminiAISummarizer
    from src.config.settings import Settings, AISettings
    
    mock_settings = Settings(ai=AISettings(gemini_api_key=""))
    monkeypatch.setattr("src.ai.gemini_model.settings", mock_settings)
    
    summarizer = GeminiAISummarizer()
    payload = {"overall_metrics": [{"total_appointments": 100}]}
    
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not set"):
        summarizer.summarize(payload)

def test_grok_missing_key(monkeypatch):
    from src.ai.grok_model import GrokAISummarizer
    from src.config.settings import Settings, AISettings
    
    mock_settings = Settings(ai=AISettings(xai_api_key=""))
    monkeypatch.setattr("src.ai.grok_model.settings", mock_settings)
    
    summarizer = GrokAISummarizer()
    payload = {"overall_metrics": [{"total_appointments": 100}]}
    
    with pytest.raises(RuntimeError, match="XAI_API_KEY is not set"):
        summarizer.summarize(payload)

def test_factory_unknown_backend(monkeypatch):
    from src.ai.factory import get_summarizer
    from src.config.settings import Settings, AISettings
    
    mock_settings = Settings(ai=AISettings(backend="unknown"))
    monkeypatch.setattr("src.ai.factory.settings", mock_settings)
    
    with pytest.raises(ValueError, match="Unknown AI_BACKEND='unknown'"):
        get_summarizer()

