"""
ETL Extraction Module.

Reads synthetic raw CSV files into Pandas DataFrames.
Performs basic file existence and column schema checks.
Raises exceptions if the expected schema is violated.
"""

import os
import pandas as pd
from typing import Dict

from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# Expected schemas for raw CSV files
EXPECTED_SCHEMAS = {
    "patients.csv": [
        "patient_id", "first_name", "last_name", "gender", 
        "date_of_birth", "phone", "email", "address", 
        "zip_code", "created_at"
    ],
    "clinics.csv": [
        "clinic_id", "clinic_name", "clinic_type", 
        "city", "state", "zip_code", "created_at"
    ],
    "appointment_types.csv": [
        "appointment_type_id", "type_name", "description"
    ],
    "appointments.csv": [
        "appointment_id", "patient_id", "clinic_id", "appointment_type_id", 
        "appointment_date", "appointment_time", "status", "created_at"
    ]
}


def extract_data() -> Dict[str, pd.DataFrame]:
    """
    Extract raw CSV files into a dictionary of DataFrames.
    
    Returns:
        Dict mapping file base name (e.g., 'patients') to its DataFrame.
        
    Raises:
        FileNotFoundError: If a required CSV is missing.
        ValueError: If a CSV is missing required columns.
    """
    logger.info("Starting data extraction from raw files.")
    raw_dir = settings.paths.raw_dir
    dataframes = {}

    for filename, expected_columns in EXPECTED_SCHEMAS.items():
        filepath = raw_dir / filename
        
        if not filepath.exists():
            error_msg = f"Required file missing: {filepath}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        logger.info(f"Extracting {filename}...")
        
        # Read all columns as string/object initially to prevent pandas from 
        # dropping invalid types (we want to catch them in validation).
        df = pd.read_csv(filepath, dtype=str)
        
        # Check for missing columns
        missing_columns = set(expected_columns) - set(df.columns)
        if missing_columns:
            error_msg = f"{filename} is missing expected columns: {missing_columns}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        dataframes[filename.replace('.csv', '')] = df
        logger.info(f"Extracted {len(df)} records from {filename}.")
        
    return dataframes
