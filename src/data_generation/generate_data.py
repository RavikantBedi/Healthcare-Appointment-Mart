"""
Synthetic Data Generation Module.

Generates realistic but completely synthetic healthcare data.
Outputs clean CSV files into the `data/raw/` directory.
Uses a deterministic seed to ensure reproducibility.

Produces 4 files:
- patients.csv (Contains personal fields to demonstrate privacy stripping later)
- clinics.csv
- appointment_types.csv
- appointments.csv
"""

import csv
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# Initialize Faker and seed it for reproducibility
fake = Faker()
Faker.seed(settings.data_gen.seed)
random.seed(settings.data_gen.seed)


def generate_patients(num: int) -> list[dict]:
    """Generate synthetic patient records."""
    patients = []
    genders = ['Male', 'Female', 'Other', 'Unknown']
    for _ in range(num):
        patients.append({
            'patient_id': str(uuid.UUID(int=random.getrandbits(128), version=4)),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'gender': random.choices(genders, weights=[48, 48, 2, 2])[0],
            'date_of_birth': fake.date_of_birth(minimum_age=0, maximum_age=90).isoformat(),
            'phone': fake.phone_number(),
            'email': fake.email(),
            'address': fake.street_address().replace('\n', ' '),
            'zip_code': fake.zipcode(),
            'created_at': fake.date_time_between(start_date="-5y", end_date="-1y").isoformat()
        })
    return patients


def generate_clinics(num: int) -> list[dict]:
    """Generate synthetic clinic records with base no-show weights."""
    clinics = []
    types = ['Primary Care', 'Specialty', 'Urgent Care', 'Pediatrics']
    for i in range(num):
        clinics.append({
            'clinic_id': str(uuid.UUID(int=random.getrandbits(128), version=4)),
            'clinic_name': f"{fake.city()} {random.choice(types)} Center",
            'clinic_type': random.choice(types),
            'city': fake.city(),
            'state': fake.state_abbr(),
            'zip_code': fake.zipcode(),
            'created_at': fake.date_time_between(start_date="-10y", end_date="-5y").isoformat(),
            # Hidden property for generating realistic data: base no-show probability modifier
            '_no_show_base': random.uniform(0.05, 0.25)
        })
    return clinics


def generate_appointment_types() -> list[dict]:
    """Generate fixed appointment types with no-show weights."""
    return [
        {'appointment_type_id': 1, 'type_name': 'General Checkup', 'description': 'Annual routine checkup', '_no_show_mod': 0.0},
        {'appointment_type_id': 2, 'type_name': 'Follow-up', 'description': 'Follow-up on previous visit', '_no_show_mod': -0.05},
        {'appointment_type_id': 3, 'type_name': 'Vaccination', 'description': 'Immunization or flu shot', '_no_show_mod': 0.02},
        {'appointment_type_id': 4, 'type_name': 'Specialist Consult', 'description': 'Consultation with specialist', '_no_show_mod': -0.08},
        {'appointment_type_id': 5, 'type_name': 'Lab Test', 'description': 'Blood work or other lab tests', '_no_show_mod': 0.05},
        {'appointment_type_id': 6, 'type_name': 'Physical Therapy', 'description': 'Rehabilitation session', '_no_show_mod': 0.10},
    ]


def _get_time_modifier(appt_time: datetime) -> float:
    """Return a probability modifier based on time of day (e.g., early morning = higher no-show)."""
    hour = appt_time.hour
    if hour < 10:  # Early morning
        return 0.05
    elif hour >= 16:  # Late afternoon/evening
        return 0.03
    return 0.0  # Mid-day


def _get_weekday_modifier(appt_date: datetime) -> float:
    """Return a probability modifier based on weekday (e.g., Mondays and Fridays higher)."""
    weekday = appt_date.weekday()
    if weekday == 0:  # Monday
        return 0.04
    elif weekday == 4:  # Friday
        return 0.03
    elif weekday >= 5:  # Weekend
        return 0.06
    return -0.02  # Mid-week


def generate_appointments(num: int, patients: list, clinics: list, appt_types: list) -> list[dict]:
    """Generate synthetic appointments with realistic status patterns."""
    appointments = []
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2026, 12, 31)
    date_range_days = (end_date - start_date).days

    for _ in range(num):
        patient = random.choice(patients)
        clinic = random.choice(clinics)
        appt_type = random.choice(appt_types)
        
        # Random date and time between 8 AM and 6 PM
        days_offset = random.randint(0, date_range_days)
        appt_date = start_date + timedelta(days=days_offset)
        
        hour = random.randint(8, 17)
        minute = random.choice([0, 15, 30, 45])
        appt_time = appt_date.replace(hour=hour, minute=minute)

        # Calculate final no-show probability based on features
        prob = clinic['_no_show_base'] + appt_type['_no_show_mod'] + _get_weekday_modifier(appt_date) + _get_time_modifier(appt_time)
        prob = max(0.01, min(0.99, prob)) # clamp
        
        # Determine status
        rand_val = random.random()
        if rand_val < prob:
            status = 'No-Show'
        elif rand_val < prob + 0.10: # 10% chance of cancellation
            status = 'Cancelled'
        else:
            status = 'Completed'

        # Ensure future appointments (relative to an arbitrary current date like late 2026) are 'Scheduled'
        # For simplicity in the dataset, we'll make a small % explicitly 'Scheduled' regardless of the past
        if random.random() < 0.05:
            status = 'Scheduled'

        # Created at is sometime before the appointment
        created_at = appt_date - timedelta(days=random.randint(1, 60))
        
        appointments.append({
            'appointment_id': str(uuid.UUID(int=random.getrandbits(128), version=4)),
            'patient_id': patient['patient_id'],
            'clinic_id': clinic['clinic_id'],
            'appointment_type_id': appt_type['appointment_type_id'],
            'appointment_date': appt_date.strftime('%Y-%m-%d'),
            'appointment_time': appt_time.strftime('%H:%M:%S'),
            'status': status,
            'created_at': created_at.isoformat()
        })
        
    return appointments


def save_to_csv(data: list[dict], filename: str, hidden_keys: set = None) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        return
        
    filepath = settings.paths.raw_dir / filename
    
    # Filter out hidden keys (used for logic but shouldn't be in CSV)
    hidden_keys = hidden_keys or set()
    fieldnames = [k for k in data[0].keys() if k not in hidden_keys]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            filtered_row = {k: v for k, v in row.items() if k not in hidden_keys}
            writer.writerow(filtered_row)
            
    logger.info(f"Saved {len(data)} records to {filepath}")


def main() -> None:
    """Main entry point for data generation."""
    logger.info(f"Starting data generation with seed={settings.data_gen.seed}")
    
    # Generate Entities
    patients = generate_patients(settings.data_gen.num_patients)
    clinics = generate_clinics(settings.data_gen.num_clinics)
    appt_types = generate_appointment_types()
    
    # Generate Fact Data
    appointments = generate_appointments(
        settings.data_gen.num_appointments, 
        patients, 
        clinics, 
        appt_types
    )
    
    # Save to CSV
    save_to_csv(patients, 'patients.csv')
    save_to_csv(clinics, 'clinics.csv', hidden_keys={'_no_show_base'})
    save_to_csv(appt_types, 'appointment_types.csv', hidden_keys={'_no_show_mod'})
    save_to_csv(appointments, 'appointments.csv')
    
    logger.info("Data generation completed successfully.")


if __name__ == "__main__":
    main()
