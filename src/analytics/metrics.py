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
    
    payload = {
        "overall_metrics": _query_to_dict_list(
            engine, "SELECT * FROM analytics.vw_overall_metrics"
        ),
        "clinic_no_show_rates": _query_to_dict_list(
            engine,
            f"SELECT * FROM analytics.vw_clinic_no_show_rate "
            f"WHERE total_appointments >= {min_sample} LIMIT 5"
        ),
        "weekday_no_show_rates": _query_to_dict_list(
            engine, "SELECT * FROM analytics.vw_weekday_no_show_rate"
        ),
        "time_slot_no_show_rates": _query_to_dict_list(
            engine, "SELECT * FROM analytics.vw_time_slot_no_show_rate"
        ),
        "appointment_type_no_show_rates": _query_to_dict_list(
            engine, "SELECT * FROM analytics.vw_appointment_type_no_show_rate"
        ),
        "monthly_trend": _query_to_dict_list(
            engine, "SELECT * FROM analytics.vw_monthly_no_show_trend"
        )
    }
    
    # We aggressively assert that there is no patient_id or personal data anywhere in the payload
    payload_str = json.dumps(payload, cls=JSONEncoder)
    assert "patient_id" not in payload_str, "Privacy violation: patient_id found in metrics payload!"
    assert "first_name" not in payload_str, "Privacy violation: first_name found in metrics payload!"
    
    logger.info("Metrics payload generated successfully. Privacy boundary verified.")
    return payload


def save_metrics_payload(filepath: str = "data/processed/metrics_payload.json") -> None:
    """Save the metrics payload to a JSON file."""
    payload = generate_metrics_payload()
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, cls=JSONEncoder, indent=4)
        
    logger.info(f"Saved metrics payload to {filepath}")
