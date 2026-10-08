"""
Analytics Metrics Module.

Bridges the gap between the PostgreSQL Analytics views and the upcoming AI layer.
Queries the aggregated SQL views and returns a structured, JSON-serializable dictionary.
Strictly ensures that NO patient-level rows are returned.
"""

from typing import Any, Dict, List
import json
import decimal
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.config.logging_config import get_logger
from src.config.settings import settings
from src.etl.load import get_engine

logger = get_logger(__name__)

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types returned by psycopg2."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


def _query_to_dict_list(engine: Engine, query: str) -> List[Dict[str, Any]]:
    """Execute a query and convert the result set to a list of dictionaries."""
    with engine.connect() as conn:
        result = conn.execute(text(query))
        # Convert rows to dicts
        return [dict(row._mapping) for row in result]


def generate_metrics_payload() -> Dict[str, Any]:
    """
    Generate a complete, structured, JSON-serializable dictionary
    containing only aggregated metrics from the analytics schema views.
    
    Returns:
        Dict containing lists of aggregated data.
    """
    logger.info("Generating Analytics Metrics payload...")
    engine = get_engine()
    min_sample = settings.analytics.clinic_min_sample
    
    overall_data = _query_to_dict_list(engine, "SELECT * FROM analytics.vw_overall_metrics")
    clinics_data = _query_to_dict_list(engine, f"SELECT * FROM analytics.vw_clinic_no_show_rate WHERE total_appointments >= {min_sample} LIMIT 5")
    weekdays_data = _query_to_dict_list(engine, "SELECT * FROM analytics.vw_weekday_no_show_rate")
    time_slots_data = _query_to_dict_list(engine, "SELECT * FROM analytics.vw_time_slot_no_show_rate")
    appt_types_data = _query_to_dict_list(engine, "SELECT * FROM analytics.vw_appointment_type_no_show_rate")
    monthly_data = _query_to_dict_list(engine, "SELECT * FROM analytics.vw_monthly_no_show_trend")

    overall = dict(overall_data[0]) if overall_data else {}
    
    # Calculate deterministic percentages for overall
    total_appts = int(overall.get('total_appointments', 0))
    def safe_pct(num, den):
        return round((float(num) / float(den)) * 100, 2) if den > 0 else 0.0
        
    overall['completed_pct'] = safe_pct(overall.get('completed', 0), total_appts)
    overall['cancelled_pct'] = safe_pct(overall.get('cancelled', 0), total_appts)
    overall['no_show_pct'] = safe_pct(overall.get('no_shows', 0), total_appts)
    overall['still_scheduled_pct'] = safe_pct(overall.get('still_scheduled', 0), total_appts)
    # Ensure no_show_rate_pct is consistently named
    overall_no_show_rate = float(overall.get('no_show_rate_pct', overall['no_show_pct']))
    overall['no_show_rate_pct'] = overall_no_show_rate

    def get_max(items: List[Dict], key: str) -> Dict:
        if not items: return {}
        item = dict(max(items, key=lambda x: float(x[key])))
        item['difference_from_overall_pp'] = round(float(item[key]) - overall_no_show_rate, 2)
        return item

    def get_min(items: List[Dict], key: str) -> Dict:
        if not items: return {}
        item = dict(min(items, key=lambda x: float(x[key])))
        item['difference_from_overall_pp'] = round(float(item[key]) - overall_no_show_rate, 2)
        return item
        
    highest_month = get_max(monthly_data, "no_show_rate_pct")
    lowest_month = get_min(monthly_data, "no_show_rate_pct")
    month_diff = round(float(highest_month['no_show_rate_pct']) - float(lowest_month['no_show_rate_pct']), 2) if highest_month and lowest_month else 0.0

    payload = {
        "overall": overall,
        "key_findings": {
            "highest_no_show_clinic": get_max(clinics_data, "no_show_rate_pct"),
            "highest_no_show_weekday": get_max(weekdays_data, "no_show_rate_pct"),
            "highest_no_show_time_slot": get_max(time_slots_data, "no_show_rate_pct"),
            "highest_no_show_appointment_type": get_max(appt_types_data, "no_show_rate_pct"),
            "highest_no_show_month": highest_month,
            "lowest_no_show_month": lowest_month,
            "highest_lowest_month_difference_pp": month_diff
        },
        "monthly_trend": monthly_data,
        "detailed_data": {
            "clinics": clinics_data,
            "weekdays": weekdays_data,
            "time_slots": time_slots_data,
            "appointment_types": appt_types_data
        }
    }
    
    # We aggressively assert that there is no patient_id or personal data anywhere in the payload
    payload_str = json.dumps(payload, cls=JSONEncoder)
    assert "patient_id" not in payload_str, "Privacy violation: patient_id found in metrics payload!"
    assert "first_name" not in payload_str, "Privacy violation: first_name found in metrics payload!"
    
    logger.info("Metrics payload generated successfully. Privacy boundary verified.")
    return payload


def save_metrics_payload(payload: Dict[str, Any], filepath: str = "data/processed/metrics_payload.json") -> None:
    """Save the metrics payload to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, cls=JSONEncoder, indent=4)
        
    logger.info(f"Saved metrics payload to {filepath}")
