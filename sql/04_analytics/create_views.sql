-- ==================================================
-- Analytics Views
-- ==================================================
-- Reusable SQL views over the mart star schema.
-- These power the business metrics and the privacy-
-- safe aggregation layer that feeds the AI.
--
-- All views return AGGREGATED data only.
-- No patient-level personal fields are exposed.
-- ==================================================

-- -------------------------------------------------
-- 1. Overall appointment metrics
-- -------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_overall_metrics AS
SELECT
    COUNT(*)                                        AS total_appointments,
    SUM(is_completed)                               AS completed,
    SUM(is_cancelled)                               AS cancelled,
    SUM(is_no_show)                                 AS no_shows,
    COUNT(*) - SUM(is_completed)
              - SUM(is_cancelled)
              - SUM(is_no_show)                     AS still_scheduled,
    ROUND(
        100.0 * SUM(is_no_show) / NULLIF(COUNT(*), 0), 2
    )                                               AS no_show_rate_pct
FROM mart.fact_appointment;

-- -------------------------------------------------
-- 2. No-show rate by clinic
-- -------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_clinic_no_show_rate AS
SELECT
    dc.clinic_name,
    dc.clinic_type,
    dc.city,
    COUNT(*)                                        AS total_appointments,
    SUM(fa.is_no_show)                              AS no_shows,
    ROUND(
        100.0 * SUM(fa.is_no_show) / NULLIF(COUNT(*), 0), 2
    )                                               AS no_show_rate_pct
FROM mart.fact_appointment fa
JOIN mart.dim_clinic dc ON dc.clinic_key = fa.clinic_key
GROUP BY dc.clinic_name, dc.clinic_type, dc.city
ORDER BY no_show_rate_pct DESC;

-- -------------------------------------------------
-- 3. No-show rate by day of week
-- -------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_weekday_no_show_rate AS
SELECT
    dd.day_of_week,
    dd.day_of_week_num,
    COUNT(*)                                        AS total_appointments,
    SUM(fa.is_no_show)                              AS no_shows,
    ROUND(
        100.0 * SUM(fa.is_no_show) / NULLIF(COUNT(*), 0), 2
    )                                               AS no_show_rate_pct
FROM mart.fact_appointment fa
JOIN mart.dim_date dd ON dd.date_key = fa.date_key
GROUP BY dd.day_of_week, dd.day_of_week_num
ORDER BY dd.day_of_week_num;

-- -------------------------------------------------
-- 4. No-show rate by time slot
-- -------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_time_slot_no_show_rate AS
SELECT
    fa.time_slot,
    COUNT(*)                                        AS total_appointments,
    SUM(fa.is_no_show)                              AS no_shows,
    ROUND(
        100.0 * SUM(fa.is_no_show) / NULLIF(COUNT(*), 0), 2
    )                                               AS no_show_rate_pct
FROM mart.fact_appointment fa
GROUP BY fa.time_slot
ORDER BY no_show_rate_pct DESC;

-- -------------------------------------------------
-- 5. No-show rate by appointment type
-- -------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_appointment_type_no_show_rate AS
SELECT
    dat.type_name,
    COUNT(*)                                        AS total_appointments,
    SUM(fa.is_no_show)                              AS no_shows,
    ROUND(
        100.0 * SUM(fa.is_no_show) / NULLIF(COUNT(*), 0), 2
    )                                               AS no_show_rate_pct
FROM mart.fact_appointment fa
JOIN mart.dim_appointment_type dat ON dat.appointment_type_key = fa.appointment_type_key
GROUP BY dat.type_name
ORDER BY no_show_rate_pct DESC;

-- -------------------------------------------------
-- 6. Monthly no-show trend
-- -------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_monthly_no_show_trend AS
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    COUNT(*)                                        AS total_appointments,
    SUM(fa.is_no_show)                              AS no_shows,
    ROUND(
        100.0 * SUM(fa.is_no_show) / NULLIF(COUNT(*), 0), 2
    )                                               AS no_show_rate_pct
FROM mart.fact_appointment fa
JOIN mart.dim_date dd ON dd.date_key = fa.date_key
GROUP BY dd.year, dd.month, dd.month_name
ORDER BY dd.year, dd.month;
