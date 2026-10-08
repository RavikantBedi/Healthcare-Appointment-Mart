"""
ETL Pipeline Orchestrator.

Orchestrates the end-to-end data pipeline:
1. Extract (Read CSVs)
2. Validate (Rules & Quarantine)
3. Load Staging (Raw Landing)
4. Transform (Privacy Stripping, Derivations)
5. Load Core (Relational 3NF)
6. Load Mart (Star Schema)
7. Reconcile Counts
"""

import sys

from src.config.logging_config import get_logger, setup_logging
from src.etl.extract import extract_data
from src.validation.validators import (
    validate_patients,
    validate_clinics,
    validate_appointment_types,
    validate_appointments
)
from src.etl.transform import (
    transform_patients,
    transform_clinics,
    transform_appointment_types,
    transform_appointments
)
from src.etl.load import (
    clear_database,
    load_staging,
    load_core,
    load_mart,
    get_table_counts
)

setup_logging()
logger = get_logger(__name__)

def run_pipeline():
    if sys.version_info < (3, 10):
        logger.error("Python 3.10 or higher is required.")
        sys.exit(1)
        
    logger.info("==================================================")
    logger.info("STARTING PIPELINE RUN")
    logger.info("==================================================")
    
    try:
        # 1. Extract
        dfs = extract_data()
        
        # 2. Validate
        vp, _ = validate_patients(dfs['patients'])
        vc, _ = validate_clinics(dfs['clinics'])
        vt, _ = validate_appointment_types(dfs['appointment_types'])
        va, _ = validate_appointments(
            dfs['appointments'],
            set(vp['patient_id']),
            set(vc['clinic_id']),
            set(vt['appointment_type_id'])
        )
        
        validated_dfs = {
            'patients': vp,
            'clinics': vc,
            'appointment_types': vt,
            'appointments': va
        }
        
        # 3. Idempotency Setup
        clear_database()
        
        # 4. Load Staging
        # Staging is our raw landing area. It intentionally includes the synthetic
        # personal fields for traceability before transformation. 
        # IT IS NEVER EXPOSED TO AI OR MART.
        load_staging(validated_dfs)
        
        # 5. Transform (Privacy Boundary is enforced here)
        transformed_dfs = {
            'patients': transform_patients(vp),
            'clinics': transform_clinics(vc),
            'appointment_types': transform_appointment_types(vt),
            'appointments': transform_appointments(va)
        }
        
        # 6. Load Core & Mart
        load_core(transformed_dfs)
        load_mart(transformed_dfs['appointments'])
        
        # 7. Row Count Reconciliation
        counts = get_table_counts()
        
        logger.info("==================================================")
        logger.info("PIPELINE RECONCILIATION SUMMARY")
        logger.info("==================================================")
        logger.info(f"Raw Extracted Appointments: {len(dfs['appointments'])}")
        logger.info(f"Validated Appointments:     {len(va)}")
        logger.info(f"Staging Appointments:       {counts['staging.stg_appointments']}")
        logger.info(f"Core Appointments:          {counts['core.appointments']}")
        logger.info(f"Mart Fact Appointments:     {counts['mart.fact_appointment']}")
        
        if not (len(dfs['appointments']) == len(va) == counts['staging.stg_appointments'] == counts['core.appointments'] == counts['mart.fact_appointment']):
            logger.error("ROW COUNT MISMATCH DETECTED!")
        else:
            logger.info("Row counts reconciled successfully.")
            
        # 8. Generate Analytics Metrics Payload
        from src.analytics.metrics import generate_metrics_payload, save_metrics_payload
        save_metrics_payload()
        
        # 9. AI Summarization
        payload = generate_metrics_payload()
        from src.ai.factory import get_summarizer
        summarizer = get_summarizer()
        
        try:
            summary = summarizer.summarize(payload)
            print("\n" + summary + "\n")
        except RuntimeError as e:
            logger.warning(f"{str(e)}; metrics pipeline completed successfully.")
            print(f"\n[AI SUMMARY SKIPPED]: {str(e)}\n")
            
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
