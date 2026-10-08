"""
Mock AI Summarizer.

Deterministic, zero-dependency mock implementation of the AISummarizer interface.
Extracts insights directly from the metrics dictionary without network calls.
"""

from typing import Dict, Any
from src.ai.interface import AISummarizer
from src.ai.privacy import validate_privacy

class MockAISummarizer(AISummarizer):
    def summarize(self, metrics: Dict[str, Any]) -> str:
        # 1. Enforce privacy boundary
        validate_privacy(metrics)
        
        # 2. Extract key metrics safely
        overall = metrics.get("overall_metrics", [{}])[0]
        total = overall.get("total_appointments", 0)
        no_show_rate = overall.get("no_show_rate_pct", 0.0)
        
        # Get worst clinic
        clinics = metrics.get("clinic_no_show_rates", [])
        worst_clinic = clinics[0] if clinics else {}
        worst_clinic_name = worst_clinic.get("clinic_name", "Unknown")
        worst_clinic_rate = worst_clinic.get("no_show_rate_pct", 0.0)
        
        # Get worst weekday
        weekdays = metrics.get("weekday_no_show_rates", [])
        sorted_weekdays = sorted(weekdays, key=lambda x: x.get("no_show_rate_pct", 0.0), reverse=True)
        worst_day = sorted_weekdays[0].get("day_of_week", "Unknown") if sorted_weekdays else "Unknown"
        
        # Get worst time slot
        time_slots = metrics.get("time_slot_no_show_rates", [])
        sorted_slots = sorted(time_slots, key=lambda x: x.get("no_show_rate_pct", 0.0), reverse=True)
        worst_slot = sorted_slots[0].get("time_slot", "Unknown") if sorted_slots else "Unknown"
        
        # 3. Construct formatted deterministic summary
        summary = (
            "========================================\n"
            "AI NO-SHOW SUMMARY (MOCK BACKEND)\n"
            "========================================\n\n"
            f"Overall no-show rate: {no_show_rate}%\n"
            f"Total appointments analyzed: {total}\n\n"
            "Key observed patterns:\n"
            f"- {worst_clinic_name} has the highest observed rate at {worst_clinic_rate}%.\n"
            f"- {worst_day} has the highest observed weekday rate.\n"
            f"- {worst_slot} slots show a higher observed rate compared to others.\n\n"
            "Operational observation:\n"
            "The data indicates concentrated no-show patterns in specific clinics and time slots. "
            "These observations may warrant targeted scheduling adjustments.\n\n"
            "Limitations:\n"
            "This summary is based on synthetic data. Observed associations do not establish causation.\n"
            "========================================"
        )
        
        return summary
