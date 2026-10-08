-- ==================================================
-- Core Relational Tables (3NF)
-- ==================================================
-- Properly typed columns with full constraints.
-- NO personal fields (name, phone, email, address).
-- Privacy by design: those fields never leave staging.
-- ==================================================

-- -------------------------------------------------
-- core.patients
-- -------------------------------------------------
-- Note: first_name, last_name, phone, email, address
-- are intentionally ABSENT. Only demographic grouping
-- fields needed for analytics are retained.
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS core.patients (
    patient_id          UUID            NOT NULL,
    gender              VARCHAR(20)     NOT NULL,
    date_of_birth       DATE            NOT NULL,
    age_group           VARCHAR(10)     NOT NULL,
    zip_code            VARCHAR(20),
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_core_patients
        PRIMARY KEY (patient_id),

    CONSTRAINT chk_patients_gender
        CHECK (gender IN ('Male', 'Female', 'Other', 'Unknown')),

    CONSTRAINT chk_patients_age_group
        CHECK (age_group IN ('0-17', '18-30', '31-45', '46-60', '61+'))
);

-- -------------------------------------------------
-- core.clinics
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS core.clinics (
    clinic_id           UUID            NOT NULL,
    clinic_name         VARCHAR(150)    NOT NULL,
    clinic_type         VARCHAR(50)     NOT NULL,
    city                VARCHAR(100)    NOT NULL,
    state               VARCHAR(50)     NOT NULL,
    zip_code            VARCHAR(20),
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_core_clinics
        PRIMARY KEY (clinic_id),

    CONSTRAINT uq_core_clinics_name
        UNIQUE (clinic_name)
);

-- -------------------------------------------------
-- core.appointment_types
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS core.appointment_types (
    appointment_type_id INTEGER         NOT NULL,
    type_name           VARCHAR(100)    NOT NULL,
    description         VARCHAR(255),

    CONSTRAINT pk_core_appointment_types
        PRIMARY KEY (appointment_type_id),

    CONSTRAINT uq_core_appointment_types_name
        UNIQUE (type_name)
);

-- -------------------------------------------------
-- core.appointments
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS core.appointments (
    appointment_id      UUID            NOT NULL,
    patient_id          UUID            NOT NULL,
    clinic_id           UUID            NOT NULL,
    appointment_type_id INTEGER         NOT NULL,
    appointment_date    DATE            NOT NULL,
    appointment_time    TIME            NOT NULL,
    status              VARCHAR(20)     NOT NULL,
    no_show_flag        BOOLEAN         NOT NULL,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_core_appointments
        PRIMARY KEY (appointment_id),

    CONSTRAINT fk_appointments_patient
        FOREIGN KEY (patient_id)
        REFERENCES core.patients (patient_id),

    CONSTRAINT fk_appointments_clinic
        FOREIGN KEY (clinic_id)
        REFERENCES core.clinics (clinic_id),

    CONSTRAINT fk_appointments_type
        FOREIGN KEY (appointment_type_id)
        REFERENCES core.appointment_types (appointment_type_id),

    CONSTRAINT chk_appointments_status
        CHECK (status IN ('Scheduled', 'Completed', 'Cancelled', 'No-Show')),

    CONSTRAINT chk_appointments_date_range
        CHECK (appointment_date >= '2023-01-01' AND appointment_date <= '2026-12-31')
);

-- -------------------------------------------------
-- Indexes for query performance
-- -------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_appointments_patient_id
    ON core.appointments (patient_id);

CREATE INDEX IF NOT EXISTS idx_appointments_clinic_id
    ON core.appointments (clinic_id);

CREATE INDEX IF NOT EXISTS idx_appointments_date
    ON core.appointments (appointment_date);

CREATE INDEX IF NOT EXISTS idx_appointments_status
    ON core.appointments (status);

CREATE INDEX IF NOT EXISTS idx_appointments_type_id
    ON core.appointments (appointment_type_id);
