-- ==================================================
-- Staging Tables
-- ==================================================
-- All columns are VARCHAR to accept raw data as-is.
-- No foreign keys or CHECK constraints at this layer.
-- Validation happens in Python before promotion to core.
-- Personal fields (first_name, last_name, phone, email,
-- address) exist HERE ONLY — they are stripped before
-- loading into core/mart (privacy by design).
-- ==================================================

-- -------------------------------------------------
-- stg_patients
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_patients (
    patient_id          VARCHAR(50)     NOT NULL,
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    gender              VARCHAR(20),
    date_of_birth       VARCHAR(20),
    phone               VARCHAR(30),
    email               VARCHAR(100),
    address             VARCHAR(255),
    zip_code            VARCHAR(20),
    created_at          VARCHAR(50),

    CONSTRAINT pk_stg_patients PRIMARY KEY (patient_id)
);

-- -------------------------------------------------
-- stg_clinics
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_clinics (
    clinic_id           VARCHAR(50)     NOT NULL,
    clinic_name         VARCHAR(150),
    clinic_type         VARCHAR(50),
    city                VARCHAR(100),
    state               VARCHAR(50),
    zip_code            VARCHAR(20),
    created_at          VARCHAR(50),

    CONSTRAINT pk_stg_clinics PRIMARY KEY (clinic_id)
);

-- -------------------------------------------------
-- stg_appointment_types
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_appointment_types (
    appointment_type_id VARCHAR(10)     NOT NULL,
    type_name           VARCHAR(100),
    description         VARCHAR(255),

    CONSTRAINT pk_stg_appointment_types PRIMARY KEY (appointment_type_id)
);

-- -------------------------------------------------
-- stg_appointments
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_appointments (
    appointment_id      VARCHAR(50)     NOT NULL,
    patient_id          VARCHAR(50),
    clinic_id           VARCHAR(50),
    appointment_type_id VARCHAR(10),
    appointment_date    VARCHAR(20),
    appointment_time    VARCHAR(20),
    status              VARCHAR(30),
    created_at          VARCHAR(50),

    CONSTRAINT pk_stg_appointments PRIMARY KEY (appointment_id)
);
