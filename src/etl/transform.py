"""
ETL Transform Module.

Transforms validated pandas DataFrames to match the core relational schemas.
Critically enforces the privacy boundary by explicitly dropping personal fields.
"""

import pandas as pd
import numpy as np

from src.config.logging_config import get_logger

logger = get_logger(__name__)

def _calculate_age_group(dob: pd.Series, reference_year: int = 2024) -> pd.Series:
    """Calculate age bucket from date of birth."""
    # Convert to datetime and get year
    dt = pd.to_datetime(dob, format='%Y-%m-%d', errors='coerce')
    age = reference_year - dt.dt.year
    
    # Bucket ages according to the CHECK constraint
    # ('0-17', '18-30', '31-45', '46-60', '61+')
    conditions = [
        (age <= 17),
        (age >= 18) & (age <= 30),
        (age >= 31) & (age <= 45),
        (age >= 46) & (age <= 60),
        (age >= 61)
    ]
    choices = ['0-17', '18-30', '31-45', '46-60', '61+']
    
    # If age is somehow missing or negative, default to a safe value or NaN.
    return pd.Series(np.select(conditions, choices, default='Unknown'), index=dob.index)


def transform_patients(df: pd.DataFrame) -> pd.DataFrame:
    """Transform patients: enforce privacy boundary, derive age group."""
    logger.info("Transforming patients...")
    df_transformed = df.copy()
    
    # 1. Enforce Privacy Boundary
    personal_fields = ['first_name', 'last_name', 'phone', 'email', 'address']
    df_transformed = df_transformed.drop(columns=personal_fields, errors='ignore')
    
    # Check that privacy boundary worked
    for field in personal_fields:
        assert field not in df_transformed.columns, f"Privacy violation: {field} leaked!"
        
    # 2. Convert Data Types & Derive Fields
    df_transformed['date_of_birth'] = pd.to_datetime(df_transformed['date_of_birth']).dt.date
    df_transformed['created_at'] = pd.to_datetime(df_transformed['created_at'])
    df_transformed['age_group'] = _calculate_age_group(df_transformed['date_of_birth'])
    
    return df_transformed


def transform_clinics(df: pd.DataFrame) -> pd.DataFrame:
    """Transform clinics: match core schema data types."""
    logger.info("Transforming clinics...")
    df_transformed = df.copy()
    df_transformed['created_at'] = pd.to_datetime(df_transformed['created_at'])
    return df_transformed


def transform_appointment_types(df: pd.DataFrame) -> pd.DataFrame:
    """Transform appointment types: convert ID to integer."""
    logger.info("Transforming appointment types...")
    df_transformed = df.copy()
    df_transformed['appointment_type_id'] = df_transformed['appointment_type_id'].astype(int)
    return df_transformed


def _derive_time_slot(time_series: pd.Series) -> pd.Series:
    """Derive time_slot based on appointment hour."""
    hours = pd.to_datetime(time_series, format='%H:%M:%S').dt.hour
    
    conditions = [
        (hours < 10),
        (hours >= 10) & (hours < 12),
        (hours >= 12) & (hours < 15),
        (hours >= 15) & (hours < 17),
        (hours >= 17)
    ]
    choices = [
        'Early Morning',
        'Late Morning',
        'Afternoon',
        'Mid Afternoon',
        'Evening'
    ]
    return pd.Series(np.select(conditions, choices, default='Unknown'), index=time_series.index)


def transform_appointments(df: pd.DataFrame) -> pd.DataFrame:
    """Transform appointments: derive no_show_flag, normalize dates."""
    logger.info("Transforming appointments...")
    df_transformed = df.copy()
    
    df_transformed['appointment_date'] = pd.to_datetime(df_transformed['appointment_date']).dt.date
    # Note: appointment_time is already a string 'HH:MM:SS', SQLAlchemy handles it well as string or time object.
    df_transformed['created_at'] = pd.to_datetime(df_transformed['created_at'])
    
    # Add updated_at
    df_transformed['updated_at'] = pd.Timestamp.now()
    
    # Derive no_show_flag
    df_transformed['no_show_flag'] = df_transformed['status'] == 'No-Show'
    
    return df_transformed

