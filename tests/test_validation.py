"""
Tests for Data Extraction and Validation Rules.
"""

import os
import pytest
import pandas as pd
from uuid import uuid4

from src.etl.extract import extract_data
from src.validation.validators import (
    validate_patients,
    validate_clinics,
    validate_appointment_types,
    validate_appointments
)


def test_clean_dataset_passes_validation():
    """Test that the deterministic clean dataset from Phase 3 passes validation perfectly."""
    dfs = extract_data()
    
    # 1. Patients
    valid_patients, rejected_patients = validate_patients(dfs['patients'])
    assert len(rejected_patients) == 0
    assert len(valid_patients) > 0
    valid_patient_ids = set(valid_patients['patient_id'])

    # 2. Clinics
    valid_clinics, rejected_clinics = validate_clinics(dfs['clinics'])
    assert len(rejected_clinics) == 0
    assert len(valid_clinics) > 0
    valid_clinic_ids = set(valid_clinics['clinic_id'])

    # 3. Appointment Types
    valid_types, rejected_types = validate_appointment_types(dfs['appointment_types'])
    assert len(rejected_types) == 0
    assert len(valid_types) > 0
    valid_type_ids = set(valid_types['appointment_type_id'])

    # 4. Appointments
    valid_appts, rejected_appts = validate_appointments(
        dfs['appointments'],
        valid_patient_ids,
        valid_clinic_ids,
        valid_type_ids
    )
    assert len(rejected_appts) == 0
    assert len(valid_appts) > 0


def test_appointment_validation_rules():
    """Test explicit validation rules using a crafted DataFrame."""
    # Create valid base IDs
    valid_patient = str(uuid4())
    valid_clinic = str(uuid4())
    valid_type = "1"
    
    valid_ids = {
        'patients': {valid_patient},
        'clinics': {valid_clinic},
        'types': {valid_type}
    }

    # Create crafted bad data
    data = [
        {
            # 0: Valid
            "appointment_id": str(uuid4()),
            "patient_id": valid_patient,
            "clinic_id": valid_clinic,
            "appointment_type_id": valid_type,
            "appointment_date": "2024-05-15",
            "appointment_time": "10:30:00",
            "status": "Scheduled"
        },
        {
            # 1: Missing patient_id
            "appointment_id": str(uuid4()),
            "patient_id": "",
            "clinic_id": valid_clinic,
            "appointment_type_id": valid_type,
            "appointment_date": "2024-05-15",
            "appointment_time": "10:30:00",
            "status": "Scheduled"
        },
        {
            # 2: Invalid FK (Clinic)
            "appointment_id": str(uuid4()),
            "patient_id": valid_patient,
            "clinic_id": "bad-clinic-id",
            "appointment_type_id": valid_type,
            "appointment_date": "2024-05-15",
            "appointment_time": "10:30:00",
            "status": "Scheduled"
        },
        {
            # 3: Invalid Status
            "appointment_id": str(uuid4()),
            "patient_id": valid_patient,
            "clinic_id": valid_clinic,
            "appointment_type_id": valid_type,
            "appointment_date": "2024-05-15",
            "appointment_time": "10:30:00",
            "status": "Delayed"
        },
        {
            # 4: Out of bounds date
            "appointment_id": str(uuid4()),
            "patient_id": valid_patient,
            "clinic_id": valid_clinic,
            "appointment_type_id": valid_type,
            "appointment_date": "2019-01-01",
            "appointment_time": "10:30:00",
            "status": "Scheduled"
        }
    ]
    
    # Add a duplicate pair separately from index 0
    dup_row = data[0].copy()
    dup_row["appointment_id"] = str(uuid4()) # A new ID that will be duplicated
    data.append(dup_row)
    data.append(dup_row.copy())
    
    df = pd.DataFrame(data)
    
    valid_df, rejected_df = validate_appointments(
        df,
        valid_ids['patients'],
        valid_ids['clinics'],
        valid_ids['types']
    )
    
    # 1 valid (the original 0), 6 rejected (missing patient, bad clinic, bad status, bad date, 2x duplicate)
    assert len(valid_df) == 1
    assert len(rejected_df) == 6
    
    errors = " ".join(rejected_df['validation_errors'].tolist())
    
    assert "Missing required field: patient_id" in errors
    assert "Invalid foreign key: clinic_id does not exist" in errors
    assert "Invalid status" in errors
    assert "out of bounds" in errors
    assert "Duplicate appointment_id" in errors
