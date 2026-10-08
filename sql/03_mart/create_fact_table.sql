-- ==================================================
-- Mart Fact Table (Star Schema)
-- ==================================================
-- Grain: ONE ROW PER APPOINTMENT
-- Every scheduled appointment is a fact row regardless
-- of its final status (Completed, Cancelled, No-Show).
--
-- Additive measures (is_no_show, is_completed,
-- is_cancelled) are INT 0/1 so analytics can use
-- SUM() directly without CASE expressions.
-- ==================================================

CREATE TABLE IF NOT EXISTS mart.fact_appointment (
    fact_id                 BIGSERIAL       NOT NULL,
    appointment_id          UUID            NOT NULL,
    patient_key             INTEGER         NOT NULL,
    clinic_key              INTEGER         NOT NULL,
    date_key                INTEGER         NOT NULL,
    appointment_type_key    INTEGER         NOT NULL,
    appointment_time        TIME            NOT NULL,
    time_slot               VARCHAR(20)     NOT NULL,
    status                  VARCHAR(20)     NOT NULL,
    no_show_flag            BOOLEAN         NOT NULL,

    -- Additive measures for easy aggregation
    is_no_show              INTEGER         NOT NULL DEFAULT 0,
    is_completed            INTEGER         NOT NULL DEFAULT 0,
    is_cancelled            INTEGER         NOT NULL DEFAULT 0,

    CONSTRAINT pk_fact_appointment
        PRIMARY KEY (fact_id),

    CONSTRAINT uq_fact_appointment_id
        UNIQUE (appointment_id),

    CONSTRAINT fk_fact_patient
        FOREIGN KEY (patient_key)
        REFERENCES mart.dim_patient (patient_key),

    CONSTRAINT fk_fact_clinic
        FOREIGN KEY (clinic_key)
        REFERENCES mart.dim_clinic (clinic_key),

    CONSTRAINT fk_fact_date
        FOREIGN KEY (date_key)
        REFERENCES mart.dim_date (date_key),

    CONSTRAINT fk_fact_appointment_type
        FOREIGN KEY (appointment_type_key)
        REFERENCES mart.dim_appointment_type (appointment_type_key),

    CONSTRAINT chk_fact_status
        CHECK (status IN ('Scheduled', 'Completed', 'Cancelled', 'No-Show')),

    CONSTRAINT chk_fact_time_slot
        CHECK (time_slot IN (
            'Early Morning', 'Late Morning', 'Afternoon',
            'Mid Afternoon', 'Evening'
        )),

    CONSTRAINT chk_fact_is_no_show
        CHECK (is_no_show IN (0, 1)),

    CONSTRAINT chk_fact_is_completed
        CHECK (is_completed IN (0, 1)),

    CONSTRAINT chk_fact_is_cancelled
        CHECK (is_cancelled IN (0, 1))
);

-- -------------------------------------------------
-- Indexes for analytics query performance
-- -------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fact_patient_key
    ON mart.fact_appointment (patient_key);

CREATE INDEX IF NOT EXISTS idx_fact_clinic_key
    ON mart.fact_appointment (clinic_key);

CREATE INDEX IF NOT EXISTS idx_fact_date_key
    ON mart.fact_appointment (date_key);

CREATE INDEX IF NOT EXISTS idx_fact_type_key
    ON mart.fact_appointment (appointment_type_key);

CREATE INDEX IF NOT EXISTS idx_fact_status
    ON mart.fact_appointment (status);
