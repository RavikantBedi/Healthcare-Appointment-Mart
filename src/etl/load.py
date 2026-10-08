"""
ETL Load Module.

Handles bulk loading DataFrames into PostgreSQL.
Orchestrates dependency-aware loading and idempotency via Truncate-and-Reload.
"""

from typing import Dict
import pandas as pd
from sqlalchemy import create_engine, text

from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# SQLAlchemy Engine Singleton
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.db.connection_url)
    return _engine


def clear_database():
    """
    Idempotency Strategy: Truncate-and-Reload.
    Because this is a synthetic snapshot dataset, the simplest and most robust
    method to avoid duplicates across all layers is to clear the tables before loading.
    We truncate in reverse dependency order (or use CASCADE).
    """
    logger.info("Clearing database tables for idempotent reload...")
    engine = get_engine()
    
    # We don't truncate dim_date because it was statically populated in Phase 2
    truncate_commands = [
        "TRUNCATE TABLE mart.fact_appointment CASCADE;",
        "TRUNCATE TABLE mart.dim_patient CASCADE;",
        "TRUNCATE TABLE mart.dim_clinic CASCADE;",
        "TRUNCATE TABLE mart.dim_appointment_type CASCADE;",
        "TRUNCATE TABLE core.appointments CASCADE;",
        "TRUNCATE TABLE core.patients CASCADE;",
        "TRUNCATE TABLE core.clinics CASCADE;",
        "TRUNCATE TABLE core.appointment_types CASCADE;",
        "TRUNCATE TABLE staging.stg_appointments CASCADE;",
        "TRUNCATE TABLE staging.stg_patients CASCADE;",
        "TRUNCATE TABLE staging.stg_clinics CASCADE;",
        "TRUNCATE TABLE staging.stg_appointment_types CASCADE;"
    ]
    
    with engine.begin() as conn:
        for cmd in truncate_commands:
            conn.execute(text(cmd))
            
    logger.info("Database successfully cleared.")


def load_staging(dfs: Dict[str, pd.DataFrame]):
    """Load raw DataFrames into the staging schema."""
    logger.info("Loading Staging layer...")
    engine = get_engine()
    
    with engine.begin() as conn:
        dfs['patients'].to_sql('stg_patients', con=conn, schema='staging', if_exists='append', index=False)
        dfs['clinics'].to_sql('stg_clinics', con=conn, schema='staging', if_exists='append', index=False)
        dfs['appointment_types'].to_sql('stg_appointment_types', con=conn, schema='staging', if_exists='append', index=False)
        dfs['appointments'].to_sql('stg_appointments', con=conn, schema='staging', if_exists='append', index=False)
        
    logger.info("Staging load complete.")


def load_core(dfs: Dict[str, pd.DataFrame]):
    """Load transformed DataFrames into the core schema."""
    logger.info("Loading Core layer...")
    engine = get_engine()
    
    with engine.begin() as conn:
        dfs['patients'].to_sql('patients', con=conn, schema='core', if_exists='append', index=False)
        dfs['clinics'].to_sql('clinics', con=conn, schema='core', if_exists='append', index=False)
        dfs['appointment_types'].to_sql('appointment_types', con=conn, schema='core', if_exists='append', index=False)
        dfs['appointments'].to_sql('appointments', con=conn, schema='core', if_exists='append', index=False)
        
    logger.info("Core load complete.")


def load_mart(df_appointments: pd.DataFrame):
    """
    Build the Analytical Mart from the Core tables.
    Instead of passing dataframes from Python, it is vastly more efficient to 
    execute an INSERT...SELECT statement that transfers data directly within Postgres.
    """
    logger.info("Loading Mart layer (Star Schema)...")
    engine = get_engine()
    
    populate_dim_patient = """
        INSERT INTO mart.dim_patient (patient_id, gender, age_group)
        SELECT patient_id, gender, age_group
        FROM core.patients;
    """
    
    populate_dim_clinic = """
        INSERT INTO mart.dim_clinic (clinic_id, clinic_name, clinic_type, city, state)
        SELECT clinic_id, clinic_name, clinic_type, city, state
        FROM core.clinics;
    """
    
    populate_dim_appointment_type = """
        INSERT INTO mart.dim_appointment_type (appointment_type_id, type_name)
        SELECT appointment_type_id, type_name
        FROM core.appointment_types;
    """
    
    # We need to map time_slot in Python and then upload, OR we can derive it in SQL.
    # The requirements asked to derive it in transformation. Let's do a fast upload
    # of the fact table after joining the surrogate keys.
    
    # The fact table needs surrogate keys. The standard ELT pattern is to build the fact
    # table purely in SQL by joining the core data with the dimension tables.
    
    populate_fact = """
        INSERT INTO mart.fact_appointment (
            appointment_id, patient_key, clinic_key, date_key, appointment_type_key,
            appointment_time, time_slot, status, no_show_flag,
            is_no_show, is_completed, is_cancelled
        )
        SELECT 
            c.appointment_id,
            dp.patient_key,
            dc.clinic_key,
            dd.date_key,
            dt.appointment_type_key,
            c.appointment_time,
            CASE 
                WHEN EXTRACT(HOUR FROM c.appointment_time) < 10 THEN 'Early Morning'
                WHEN EXTRACT(HOUR FROM c.appointment_time) < 12 THEN 'Late Morning'
                WHEN EXTRACT(HOUR FROM c.appointment_time) < 15 THEN 'Afternoon'
                WHEN EXTRACT(HOUR FROM c.appointment_time) < 17 THEN 'Mid Afternoon'
                ELSE 'Evening'
            END as time_slot,
            c.status,
            c.no_show_flag,
            CASE WHEN c.status = 'No-Show' THEN 1 ELSE 0 END as is_no_show,
            CASE WHEN c.status = 'Completed' THEN 1 ELSE 0 END as is_completed,
            CASE WHEN c.status = 'Cancelled' THEN 1 ELSE 0 END as is_cancelled
        FROM core.appointments c
        JOIN mart.dim_patient dp ON c.patient_id = dp.patient_id
        JOIN mart.dim_clinic dc ON c.clinic_id = dc.clinic_id
        JOIN mart.dim_date dd ON c.appointment_date = dd.full_date
        JOIN mart.dim_appointment_type dt ON c.appointment_type_id = dt.appointment_type_id;
    """
    
    with engine.begin() as conn:
        conn.execute(text(populate_dim_patient))
        conn.execute(text(populate_dim_clinic))
        conn.execute(text(populate_dim_appointment_type))
        conn.execute(text(populate_fact))
        
    logger.info("Mart load complete.")


def get_table_counts() -> Dict[str, int]:
    """Retrieve row counts for reconciliation."""
    engine = get_engine()
    counts = {}
    queries = {
        'staging.stg_appointments': "SELECT COUNT(*) FROM staging.stg_appointments",
        'core.appointments': "SELECT COUNT(*) FROM core.appointments",
        'mart.fact_appointment': "SELECT COUNT(*) FROM mart.fact_appointment",
        'core.patients': "SELECT COUNT(*) FROM core.patients",
        'core.clinics': "SELECT COUNT(*) FROM core.clinics",
        'core.appointment_types': "SELECT COUNT(*) FROM core.appointment_types",
    }
    
    with engine.connect() as conn:
        for name, query in queries.items():
            result = conn.execute(text(query)).scalar()
            counts[name] = result
            
    return counts
