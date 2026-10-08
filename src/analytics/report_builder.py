"""
Report Builder Module.

Generates a deterministic, structured markdown report from the precomputed
analytics payload. No LLM is used — all values are inserted directly from
the Python/SQL computation layer.
"""

from typing import Dict, Any


def build_structured_report(payload: Dict[str, Any]) -> str:
    """Build the complete structured deterministic markdown report."""

    overall = payload.get("overall", {})
    kf = payload.get("key_findings", {})

    total = overall.get("total_appointments", 0)
    completed = overall.get("completed", 0)
    cancelled = overall.get("cancelled", 0)
    no_shows = overall.get("no_shows", 0)
    scheduled = overall.get("still_scheduled", 0)

    completed_pct = overall.get("completed_pct", 0)
    cancelled_pct = overall.get("cancelled_pct", 0)
    no_show_pct = overall.get("no_show_pct", 0)
    scheduled_pct = overall.get("still_scheduled_pct", 0)

    highest_clinic = kf.get("highest_no_show_clinic", {})
    highest_weekday = kf.get("highest_no_show_weekday", {})
    highest_ts = kf.get("highest_no_show_time_slot", {})
    highest_type = kf.get("highest_no_show_appointment_type", {})
    highest_month = kf.get("highest_no_show_month", {})
    lowest_month = kf.get("lowest_no_show_month", {})
    month_diff = kf.get("highest_lowest_month_difference_pp", 0)

    report = [
        "# 1. EXECUTIVE SUMMARY\n",
        f"- Total appointments: {total:,}",
        f"- Completed appointments: {completed:,}",
        f"- Cancelled appointments: {cancelled:,}",
        f"- No-show appointments: {no_shows:,}",
        f"- Scheduled appointments: {scheduled:,}",
        f"- Overall no-show rate: {no_show_pct}%\n",
        "- Key Findings:",
        f"  - Highest clinic no-show rate: {highest_clinic.get('clinic_name', 'N/A')} at {highest_clinic.get('no_show_rate_pct', 0)}%",
        f"  - Highest weekday no-show rate: {highest_weekday.get('day_of_week', 'N/A')} at {highest_weekday.get('no_show_rate_pct', 0)}%",
        f"  - Highest time slot no-show rate: {highest_ts.get('time_slot', 'N/A')} at {highest_ts.get('no_show_rate_pct', 0)}%\n",

        "# 2. APPOINTMENT STATUS OVERVIEW\n",
        f"- Completed: {completed:,} ({completed_pct}%) - Successfully attended.",
        f"- No-show: {no_shows:,} ({no_show_pct}%) - Patient did not arrive.",
        f"- Cancelled: {cancelled:,} ({cancelled_pct}%) - Cancelled before appointment.",
        f"- Scheduled: {scheduled:,} ({scheduled_pct}%) - Upcoming.\n",

        "# 3. NO-SHOW ANALYSIS\n",
        "## 3.1 Overall No-Show Rate",
        f"- Overall no-show rate: {no_show_pct}%",
        f"- Number of no-shows: {no_shows:,}",
        f"- Total appointments: {total:,}\n",

        "## 3.2 By Clinic",
        f"- Highest no-show clinic: {highest_clinic.get('clinic_name', 'N/A')}",
        f"  - No-show rate: {highest_clinic.get('no_show_rate_pct', 0)}%",
        f"  - Difference from overall rate: +{highest_clinic.get('difference_from_overall_pp', 0)} pp\n",

        "## 3.3 By Weekday",
        f"- Highest no-show weekday: {highest_weekday.get('day_of_week', 'N/A')}",
        f"  - No-show rate: {highest_weekday.get('no_show_rate_pct', 0)}%",
        f"  - Difference from overall rate: +{highest_weekday.get('difference_from_overall_pp', 0)} pp\n",

        "## 3.4 By Time Slot",
        f"- Highest no-show time slot: {highest_ts.get('time_slot', 'N/A')}",
        f"  - No-show rate: {highest_ts.get('no_show_rate_pct', 0)}%",
        f"  - Difference from overall rate: +{highest_ts.get('difference_from_overall_pp', 0)} pp\n",

        "## 3.5 By Appointment Type",
        f"- Highest no-show appointment type: {highest_type.get('type_name', 'N/A')}",
        f"  - No-show rate: {highest_type.get('no_show_rate_pct', 0)}%",
        f"  - Difference from overall rate: +{highest_type.get('difference_from_overall_pp', 0)} pp\n",

        "## 3.6 By Month",
        f"- Highest no-show month: {highest_month.get('month_name', 'N/A')} {highest_month.get('year', '')}",
        f"- Lowest no-show month: {lowest_month.get('month_name', 'N/A')} {lowest_month.get('year', '')}",
        f"- Difference between highest and lowest: {month_diff} pp\n",

        "# 4. KEY FINDINGS\n",
        f"- The clinic '{highest_clinic.get('clinic_name', 'N/A')}' observed a {highest_clinic.get('no_show_rate_pct', 0)}% no-show rate, which is +{highest_clinic.get('difference_from_overall_pp', 0)} pp compared to overall.",
        f"- The weekday '{highest_weekday.get('day_of_week', 'N/A')}' observed a {highest_weekday.get('no_show_rate_pct', 0)}% no-show rate, which is +{highest_weekday.get('difference_from_overall_pp', 0)} pp compared to overall.",
        f"- The time slot '{highest_ts.get('time_slot', 'N/A')}' observed a {highest_ts.get('no_show_rate_pct', 0)}% no-show rate, which is +{highest_ts.get('difference_from_overall_pp', 0)} pp compared to overall.",
        f"- The appointment type '{highest_type.get('type_name', 'N/A')}' observed a {highest_type.get('no_show_rate_pct', 0)}% no-show rate, which is +{highest_type.get('difference_from_overall_pp', 0)} pp compared to overall.\n",

        "# 5. OPERATIONAL AREAS FOR INVESTIGATION\n",
        f"- The observed higher rate at '{highest_clinic.get('clinic_name', 'N/A')}' may warrant investigation.",
        f"- The observed higher rate on {highest_weekday.get('day_of_week', 'N/A')} is a potential area for review.",
        f"- The observed higher rate during {highest_ts.get('time_slot', 'N/A')} slots may warrant investigation.\n",

        "# 6. RECOMMENDED NEXT ANALYSIS\n",
        "- Clinic × Appointment Type",
        "- Clinic × Time Slot",
        "- Weekday × Time Slot",
        "- Month × Appointment Type",
        "- Appointment lead time\n",

        "# 7. DATA LIMITATIONS\n",
        "The dataset is synthetic, and observed associations do not establish causation.",
    ]

    return "\n".join(report)
