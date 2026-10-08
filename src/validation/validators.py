"""
Data Validation Module.

Provides reusable validation functions for staging data.
Filters valid records and explicitly quarantines rejected records
with clear error messages.
"""

import os
from typing import Tuple, Set
import pandas as pd
from datetime import datetime

from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)


def save_rejected(df: pd.DataFrame, filename: str) -> None:
    """Save rejected records to the rejected directory."""
    if df.empty:
        return
    out_path = settings.paths.rejected_dir / filename
    df.to_csv(out_path, index=False)
    logger.warning(f"Saved {len(df)} rejected records to {out_path}")


def _add_error(df: pd.DataFrame, mask: pd.Series, error_msg: str) -> None:
    """Helper to append an error message to the validation_errors column."""
    if 'validation_errors' not in df.columns:
        df['validation_errors'] = ''
    
    # Append error message, adding a separator if not empty
    df.loc[mask, 'validation_errors'] = df.loc[mask, 'validation_errors'].apply(
        lambda x: x + f"{error_msg}; " if x else f"{error_msg}; "
    )


def validate_patients(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Validate patients DataFrame."""
    df = df.copy()
    df['validation_errors'] = ''

    # Rule 1: Required fields
    required = ['patient_id', 'gender', 'date_of_birth']
    for col in required:
        mask = df[col].isna() | (df[col] == '')
        _add_error(df, mask, f"Missing required field: {col}")

    # Rule 2: Uniqueness
    mask = df.duplicated(subset=['patient_id'], keep=False)
    _add_error(df, mask, "Duplicate patient_id")

    # Rule 3: Valid gender
    valid_genders = {'Male', 'Female', 'Other', 'Unknown'}
    mask = ~df['gender'].isin(valid_genders) & df['gender'].notna() & (df['gender'] != '')
    _add_error(df, mask, "Invalid gender")

    # Rule 4: Valid date
    try:
        parsed_dates = pd.to_datetime(df['date_of_birth'], format='%Y-%m-%d', errors='coerce')
        mask = parsed_dates.isna() & df['date_of_birth'].notna() & (df['date_of_birth'] != '')
        _add_error(df, mask, "Invalid date_of_birth format (must be YYYY-MM-DD)")
    except Exception:
        _add_error(df, pd.Series([True]*len(df), index=df.index), "Invalid date_of_birth formatting completely failed")

    # Split
    is_invalid = df['validation_errors'] != ''
    rejected_df = df[is_invalid].copy()
    valid_df = df[~is_invalid].drop(columns=['validation_errors']).copy()

    logger.info(f"Patients validation: {len(valid_df)} valid, {len(rejected_df)} rejected.")
    save_rejected(rejected_df, "rejected_patients.csv")
    return valid_df, rejected_df


def validate_clinics(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Validate clinics DataFrame."""
    df = df.copy()
    df['validation_errors'] = ''

    required = ['clinic_id', 'clinic_name', 'clinic_type', 'city', 'state']
    for col in required:
        mask = df[col].isna() | (df[col] == '')
        _add_error(df, mask, f"Missing required field: {col}")

    mask = df.duplicated(subset=['clinic_id'], keep=False)
    _add_error(df, mask, "Duplicate clinic_id")

    is_invalid = df['validation_errors'] != ''
    rejected_df = df[is_invalid].copy()
    valid_df = df[~is_invalid].drop(columns=['validation_errors']).copy()

    logger.info(f"Clinics validation: {len(valid_df)} valid, {len(rejected_df)} rejected.")
    save_rejected(rejected_df, "rejected_clinics.csv")
    return valid_df, rejected_df


def validate_appointment_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Validate appointment types DataFrame."""
    df = df.copy()
    df['validation_errors'] = ''

    required = ['appointment_type_id', 'type_name']
    for col in required:
        mask = df[col].isna() | (df[col] == '')
        _add_error(df, mask, f"Missing required field: {col}")

    mask = df.duplicated(subset=['appointment_type_id'], keep=False)
    _add_error(df, mask, "Duplicate appointment_type_id")

    is_invalid = df['validation_errors'] != ''
    rejected_df = df[is_invalid].copy()
    valid_df = df[~is_invalid].drop(columns=['validation_errors']).copy()

    logger.info(f"Appointment Types validation: {len(valid_df)} valid, {len(rejected_df)} rejected.")
    save_rejected(rejected_df, "rejected_appointment_types.csv")
    return valid_df, rejected_df


def validate_appointments(
    df: pd.DataFrame, 
    valid_patient_ids: set, 
    valid_clinic_ids: set, 
    valid_type_ids: set
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Validate appointments DataFrame with foreign key checks."""
    df = df.copy()
    df['validation_errors'] = ''

    # Rule 1: Required fields
    required = [
        'appointment_id', 'patient_id', 'clinic_id', 'appointment_type_id', 
        'appointment_date', 'appointment_time', 'status'
    ]
    for col in required:
        mask = df[col].isna() | (df[col] == '')
        _add_error(df, mask, f"Missing required field: {col}")

    # Rule 2: Uniqueness
    mask = df.duplicated(subset=['appointment_id'], keep=False)
    _add_error(df, mask, "Duplicate appointment_id")

    # Rule 3: Foreign Keys
    mask = ~df['patient_id'].isin(valid_patient_ids) & df['patient_id'].notna() & (df['patient_id'] != '')
    _add_error(df, mask, "Invalid foreign key: patient_id does not exist")
    
    mask = ~df['clinic_id'].isin(valid_clinic_ids) & df['clinic_id'].notna() & (df['clinic_id'] != '')
    _add_error(df, mask, "Invalid foreign key: clinic_id does not exist")
    
    mask = ~df['appointment_type_id'].isin(valid_type_ids) & df['appointment_type_id'].notna() & (df['appointment_type_id'] != '')
    _add_error(df, mask, "Invalid foreign key: appointment_type_id does not exist")

    # Rule 4: Status values
    valid_statuses = {'Scheduled', 'Completed', 'Cancelled', 'No-Show'}
    mask = ~df['status'].isin(valid_statuses) & df['status'].notna() & (df['status'] != '')
    _add_error(df, mask, f"Invalid status (must be one of {valid_statuses})")

    # Rule 5: Dates and Times
    try:
        parsed_dates = pd.to_datetime(df['appointment_date'], format='%Y-%m-%d', errors='coerce')
        
        # Format check
        format_mask = parsed_dates.isna() & df['appointment_date'].notna() & (df['appointment_date'] != '')
        _add_error(df, format_mask, "Invalid appointment_date format (must be YYYY-MM-DD)")
        
        # Range check
        start_date = pd.Timestamp('2023-01-01')
        end_date = pd.Timestamp('2026-12-31')
        range_mask = (parsed_dates < start_date) | (parsed_dates > end_date)
        # Apply range mask only where date is validly parsed
        valid_date_mask = parsed_dates.notna()
        _add_error(df, range_mask & valid_date_mask, "appointment_date out of bounds (must be 2023-01-01 to 2026-12-31)")
    except Exception:
        _add_error(df, pd.Series([True]*len(df), index=df.index), "Invalid appointment_date processing failed")

    # Time format check (allow HH:MM or HH:MM:SS)
    try:
        parsed_times = pd.to_datetime(df['appointment_time'], format='%H:%M:%S', errors='coerce').fillna(
                       pd.to_datetime(df['appointment_time'], format='%H:%M', errors='coerce'))
        time_mask = parsed_times.isna() & df['appointment_time'].notna() & (df['appointment_time'] != '')
        _add_error(df, time_mask, "Invalid appointment_time format")
    except Exception:
        _add_error(df, pd.Series([True]*len(df), index=df.index), "Invalid appointment_time processing failed")

    # Created at timestamp check (if present)
    if 'created_at' in df.columns:
        try:
            parsed_created = pd.to_datetime(df['created_at'], errors='coerce')
            created_mask = parsed_created.isna() & df['created_at'].notna() & (df['created_at'] != '')
            _add_error(df, created_mask, "Invalid created_at timestamp format")
        except Exception:
            _add_error(df, pd.Series([True]*len(df), index=df.index), "Invalid created_at processing failed")

    # Split
    is_invalid = df['validation_errors'] != ''
    rejected_df = df[is_invalid].copy()
    valid_df = df[~is_invalid].drop(columns=['validation_errors']).copy()

    logger.info(f"Appointments validation: {len(valid_df)} valid, {len(rejected_df)} rejected.")
    save_rejected(rejected_df, "rejected_appointments.csv")
    return valid_df, rejected_df
