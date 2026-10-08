"""
Tests for ETL Transformation rules.
"""

import pandas as pd
from src.etl.transform import (
    transform_patients,
    transform_appointments
)

def test_patient_privacy_stripping():
    """Verify that personal fields are strictly removed during transformation."""
    raw_data = {
        'patient_id': ['123'],
        'first_name': ['John'],
        'last_name': ['Doe'],
        'phone': ['555-1234'],
        'email': ['john@example.com'],
        'address': ['123 Main St'],
        'zip_code': ['12345'],
        'gender': ['Male'],
        'date_of_birth': ['1990-01-01'],
        'created_at': ['2024-01-01T00:00:00']
    }
    df = pd.DataFrame(raw_data)
    
    transformed = transform_patients(df)
    
    # Must be missing
    assert 'first_name' not in transformed.columns
    assert 'last_name' not in transformed.columns
    assert 'phone' not in transformed.columns
    assert 'email' not in transformed.columns
    assert 'address' not in transformed.columns
    
    # Must be present
    assert 'patient_id' in transformed.columns
    assert 'age_group' in transformed.columns
    assert transformed['age_group'].iloc[0] == '31-45'  # 2024 - 1990 = 34

def test_appointment_derivations():
    """Verify derivations like no_show_flag."""
    raw_data = {
        'appointment_id': ['1', '2'],
        'patient_id': ['p1', 'p2'],
        'clinic_id': ['c1', 'c2'],
        'appointment_type_id': [1, 2],
        'appointment_date': ['2024-01-01', '2024-01-02'],
        'appointment_time': ['09:00:00', '14:00:00'],
        'status': ['No-Show', 'Completed'],
        'created_at': ['2024-01-01T00:00:00', '2024-01-01T00:00:00']
    }
    df = pd.DataFrame(raw_data)
    
    transformed = transform_appointments(df)
    
    assert 'no_show_flag' in transformed.columns
    assert transformed['no_show_flag'].iloc[0] == True
    assert transformed['no_show_flag'].iloc[1] == False
    assert 'updated_at' in transformed.columns
