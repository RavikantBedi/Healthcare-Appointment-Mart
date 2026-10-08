# Healthcare Appointment Mart - Demo Checklist

Use this exact sequence for the 5-8 minute demonstration.

## 1. Project Architecture (1 min)
- **Show Code Structure**: Highlight the strict separation between `src/etl`, `src/analytics`, and `src/ai`.
- **Explain the Layers**: 
  1. Staging (contains synthetic PII for debugging)
  2. Core (3NF Relational Data - completely anonymized)
  3. Mart (Star Schema - optimized for querying)
  4. Analytics Views (SQL aggregates)
  5. AI Boundary (JSON payload)

## 2. Clean Setup / Reproducibility (1 min)
- Run the full setup command live:
  ```bash
  docker compose down -v  # Ensure clean slate
  docker compose up --build
  ```
- **Result**: Show the terminal scrolling through Extract -> Validate -> Load -> Summary automatically.

## 3. Data Model & SQL Correctness (1 min)
- Access the database:
  ```bash
  docker compose exec db psql -U healthcare -d healthcare_mart
  ```
- Show the separation between Core and Mart:
  ```sql
  \d core.patients
  \d mart.fact_appointment
  ```
- Show the analytics views working:
  ```sql
  SELECT * FROM analytics.vw_clinic_no_show_rate;
  ```

## 4. Privacy Check (1 min)
- Show that Core/Mart tables have no personal fields:
  ```sql
  SELECT * FROM core.patients LIMIT 5;
  ```
- Show the strict Privacy Validator logic in `src/ai/privacy.py` `FORBIDDEN_FIELDS`.
- Emphasize that the system rejects the entire AI run if a forbidden word is detected.

## 5. Failure / Edge Case Demonstration (1 min)
- Demonstrate the validator rejecting bad data.
- Run the explicit test fixture demonstration:
  ```bash
  pytest tests/test_phase8_audit.py::test_failure_demonstration_with_fixture -v
  ```
- Mention that this proves bad records (like bad FKs or duplicates) are safely quarantined and logged, without crashing the whole pipeline.

## 6. AI Summary Output Safety (1 min)
- Show the final console output produced during the `docker compose up` run.
- Point out the specific phrasing:
  - *"Observed associations do not establish causation"*
  - *"Based on synthetic data"*
- Explain that the AI layer is stateless and completely isolated from the database.

## 7. Pytest Results (1 min)
- Run the full test suite live:
  ```bash
  pytest -v
  ```
- Point out specific tests:
  - `test_patient_privacy_stripping`
  - `test_zero_denominator_mock_ai`
  - `test_clinic_min_sample_filtering`
