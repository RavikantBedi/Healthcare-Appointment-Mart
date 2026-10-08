-- ==================================================
-- Mart Dimension Tables (Star Schema)
-- ==================================================
-- Surrogate keys (SERIAL) decouple the mart from
-- source system IDs. Natural keys are preserved for
-- traceability.
-- ==================================================

-- -------------------------------------------------
-- dim_patient
-- -------------------------------------------------
-- No personal fields — only analytical groupings.
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS mart.dim_patient (
    patient_key         SERIAL          NOT NULL,
    patient_id          UUID            NOT NULL,
    gender              VARCHAR(20)     NOT NULL,
    age_group           VARCHAR(10)     NOT NULL,
    zip_code            VARCHAR(20),

    CONSTRAINT pk_dim_patient
        PRIMARY KEY (patient_key),

    CONSTRAINT uq_dim_patient_id
        UNIQUE (patient_id)
);

-- -------------------------------------------------
-- dim_clinic
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS mart.dim_clinic (
    clinic_key          SERIAL          NOT NULL,
    clinic_id           UUID            NOT NULL,
    clinic_name         VARCHAR(150)    NOT NULL,
    clinic_type         VARCHAR(50)     NOT NULL,
    city                VARCHAR(100)    NOT NULL,
    state               VARCHAR(50)     NOT NULL,

    CONSTRAINT pk_dim_clinic
        PRIMARY KEY (clinic_key),

    CONSTRAINT uq_dim_clinic_id
        UNIQUE (clinic_id)
);

-- -------------------------------------------------
-- dim_appointment_type
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS mart.dim_appointment_type (
    appointment_type_key SERIAL         NOT NULL,
    appointment_type_id  INTEGER        NOT NULL,
    type_name            VARCHAR(100)   NOT NULL,
    description          VARCHAR(255),

    CONSTRAINT pk_dim_appointment_type
        PRIMARY KEY (appointment_type_key),

    CONSTRAINT uq_dim_appointment_type_id
        UNIQUE (appointment_type_id)
);

-- -------------------------------------------------
-- dim_date
-- -------------------------------------------------
-- Pre-populated calendar dimension.
-- date_key uses YYYYMMDD integer format for fast
-- partitioning and human-readable joins.
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS mart.dim_date (
    date_key            INTEGER         NOT NULL,
    full_date           DATE            NOT NULL,
    year                INTEGER         NOT NULL,
    month               INTEGER         NOT NULL,
    day                 INTEGER         NOT NULL,
    month_name          VARCHAR(15)     NOT NULL,
    day_of_week         VARCHAR(15)     NOT NULL,
    day_of_week_num     INTEGER         NOT NULL,
    quarter             INTEGER         NOT NULL,
    is_weekend          BOOLEAN         NOT NULL,

    CONSTRAINT pk_dim_date
        PRIMARY KEY (date_key),

    CONSTRAINT uq_dim_date_full_date
        UNIQUE (full_date),

    CONSTRAINT chk_dim_date_month
        CHECK (month BETWEEN 1 AND 12),

    CONSTRAINT chk_dim_date_day
        CHECK (day BETWEEN 1 AND 31),

    CONSTRAINT chk_dim_date_quarter
        CHECK (quarter BETWEEN 1 AND 4),

    CONSTRAINT chk_dim_date_dow
        CHECK (day_of_week_num BETWEEN 1 AND 7)
);
