-- ==================================================
-- Populate dim_date (2023-01-01 through 2026-12-31)
-- ==================================================
-- Uses generate_series to create a calendar dimension.
-- Idempotent: skips rows that already exist via
-- ON CONFLICT DO NOTHING.
-- ==================================================

INSERT INTO mart.dim_date (
    date_key,
    full_date,
    year,
    month,
    day,
    month_name,
    day_of_week,
    day_of_week_num,
    quarter,
    is_weekend
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER         AS date_key,
    d                                        AS full_date,
    EXTRACT(YEAR FROM d)::INTEGER            AS year,
    EXTRACT(MONTH FROM d)::INTEGER           AS month,
    EXTRACT(DAY FROM d)::INTEGER             AS day,
    TO_CHAR(d, 'FMMonth')                    AS month_name,
    TO_CHAR(d, 'FMDay')                      AS day_of_week,
    EXTRACT(ISODOW FROM d)::INTEGER          AS day_of_week_num,
    EXTRACT(QUARTER FROM d)::INTEGER         AS quarter,
    EXTRACT(ISODOW FROM d)::INTEGER IN (6,7) AS is_weekend
FROM generate_series(
    '2023-01-01'::DATE,
    '2026-12-31'::DATE,
    '1 day'::INTERVAL
) AS d
ON CONFLICT (date_key) DO NOTHING;
