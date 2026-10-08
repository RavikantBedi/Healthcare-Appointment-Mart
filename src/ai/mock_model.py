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
        overall = metrics.get("overall", {})
        total = overall.get("total_appointments", 0)
        no_show_rate = overall.get("no_show_rate_pct", 0.0)
        
        # Get key findings
        findings = metrics.get("key_findings", {})
        
        worst_clinic = findings.get("highest_no_show_clinic", {}) or {}
        worst_clinic_name = worst_clinic.get("clinic_name", "Unknown")
        worst_clinic_rate = worst_clinic.get("no_show_rate_pct", 0.0)
        
        worst_day_obj = findings.get("highest_no_show_weekday", {}) or {}
        worst_day = worst_day_obj.get("day_of_week", "Unknown")
        
        worst_slot_obj = findings.get("highest_no_show_time_slot", {}) or {}
        worst_slot = worst_slot_obj.get("time_slot", "Unknown")
        
        worst_month_obj = findings.get("highest_no_show_month", {}) or {}
        worst_month_name = worst_month_obj.get("month_name", "Unknown")
        worst_month_rate = worst_month_obj.get("no_show_rate_pct", 0.0)
        if "year" in worst_month_obj and "month" in worst_month_obj:
            worst_month_label = f"{worst_month_obj['year']}-{str(worst_month_obj['month']).zfill(2)} ({worst_month_name})"
        elif "year" in worst_month_obj:
            worst_month_label = f"{worst_month_obj['year']} {worst_month_name}"
        else:
            worst_month_label = worst_month_name
        
        # 3. Construct formatted deterministic summary
        summary = (
            "========================================\n"
            "AI NO-SHOW SUMMARY (MOCK BACKEND)\n"
            "========================================\n\n"
            f"Overall no-show rate: {float(no_show_rate):.2f}%\n"
            f"Total appointments analyzed: {total}\n\n"
            "Key observed patterns:\n"
            f"- {worst_clinic_name} has the highest observed rate at {float(worst_clinic_rate):.2f}%.\n"
            f"- {worst_day} has the highest observed weekday rate.\n"
            f"- {worst_slot} slots show a higher observed rate compared to others.\n"
            f"- {worst_month_label} had the highest monthly rate at {float(worst_month_rate):.2f}%.\n\n"
            "Operational observation:\n"
            "The data indicates concentrated no-show patterns in specific clinics and time slots. "
            "These observations may warrant targeted scheduling adjustments.\n\n"
            "Limitations:\n"
            "This summary is based on synthetic data. Observed associations do not establish causation.\n"
            "========================================"
        )
        
        return summary
