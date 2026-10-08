# Project Context: Healthcare Appointment Mart (DAI-019)

**Candidate:** Ravikant Bedi  
**Assignment ID:** DAI-019
**Track:** Data Modeling  
**Date Started:** 2026-10-08  

This file is maintained to ensure context is never lost across sessions or when switching AI models. **Any model reading this file should read it entirely before proceeding with the next development phase.**

---

## 1. Detailed Project Overview

**The Problem Statement:**
Healthcare clinics experience significant operational and financial losses due to patient "no-shows" (missed appointments). Identifying the patterns behind these no-shows is critical for operational teams to intervene, overbook intelligently, or send targeted reminders. However, healthcare data contains highly sensitive Protected Health Information (PHI/PII), meaning any analytics or AI integration must be strictly isolated from raw patient data.

**The Solution:**
The "Healthcare Appointment Mart" is a production-quality data engineering and analytics pipeline designed to securely ingest, model, and analyze no-show behavior without ever exposing personal fields. 

**Core Business Objectives:**
The system is built to definitively answer operational questions such as:
- What is the overall no-show rate?
- Which specific clinics experience the highest no-show rates?
- Which days of the week or specific time slots (e.g., 'Early Morning' vs. 'Afternoon') have higher no-show rates?
- How do no-shows trend month-over-month?
- Do specific appointment types (e.g., 'Follow-up' vs. 'New Patient') suffer from higher attrition?

**The Flow (End-to-End):**
1. **Data Generation:** We simulate raw operational data using Python (`Faker`), creating thousands of realistic but synthetic appointments, patients, and clinics. 
2. **Extraction & Validation:** The pipeline ingests this raw CSV data, explicitly validating foreign keys, data types, and logical constraints. Invalid records are explicitly quarantined into a `rejected/` directory.
3. **Privacy & Transformation (ETL):** This is the crucial privacy boundary. Personal fields (names, phone numbers, emails, addresses) are stripped out. The data is normalized and business logic (like deriving a `no_show_flag` and `time_slot`) is applied.
4. **Data Modeling:** Clean data is loaded into PostgreSQL. It is first stored in a strict **Core Relational Model (3NF)**, and then modeled into an **Analytical Star Schema (Data Mart)** designed for high-performance querying.
5. **Business Metrics Layer:** SQL views sit on top of the Star Schema to calculate the core operational questions defined above.
6. **AI Summarization:** A Python interface queries the SQL views to generate an aggregated, privacy-safe JSON payload. This payload (containing zero personal data) is sent to an AI summarizer (either a Local LLM via Ollama or a Mock service). The AI reads the metrics and outputs a human-readable summary of the **observed patterns** to help operations teams make decisions. The AI is strictly prompted to avoid making unprovable causal claims (e.g., it can say "Mondays have higher no-shows", but it cannot say "Mondays have higher no-shows because patients are tired").

---

## 2. Final Design Decisions (Locked)

1. **Dataset Size:** ~20,000 appointments, ~5,000 patients, ~15 clinics, 6 appointment types. Generated deterministically (`seed=42`).
2. **Bad Data Strategy:** The main generated dataset is 100% clean. Intentional bad records (for failure demos) will be created as a separate fixture file (`tests/fixtures/invalid_appointments.csv`).
3. **PostgreSQL:** Port `5432` (configurable via `.env`). Uses schemas: `staging`, `core`, `mart`, `analytics`.
4. **Date Dimension:** `dim_date` covers 2023-01-01 to 2026-12-31.
5. **Dashboard:** Skip Metabase entirely until core requirements are complete. Output metrics to console instead.

---

## 3. Architecture Details

**Schemas and Tables:**
- **staging:** `stg_patients`, `stg_clinics`, `stg_appointment_types`, `stg_appointments`. (All columns VARCHAR, personal fields present).
- **core:** `patients` (no personal fields), `clinics`, `appointment_types`, `appointments`. (Strict types, constraints, FKs, CHECK constraints).
- **mart (Star Schema):** `dim_patient`, `dim_clinic`, `dim_appointment_type`, `dim_date`, `fact_appointment`. (Surrogate SERIAL keys, additive INT measures like `is_no_show` in fact table).
- **analytics:** Views over the mart (`vw_overall_metrics`, `vw_clinic_no_show_rate`, `vw_weekday_no_show_rate`, `vw_time_slot_no_show_rate`, `vw_appointment_type_no_show_rate`, `vw_monthly_no_show_trend`).

---

## 4. Phase Tracking

**Phase 1: Project Scaffolding & Git Init**
- **Status:** ✅ **DONE** (Commit `d3ed08b`)
- **Details:** Created the directory structure, `.gitignore`, `.env.example`, `requirements.txt`, `pytest.ini`, `docker-compose.yml`, and `Dockerfile`. Setup Python centralized settings (`settings.py`) and structured logging. Initialized git and made the first commit.

**Phase 2: Database Schema Creation**
- **Status:** ✅ **DONE** (Commit `1125f9c`)
- **Details:** Wrote and executed idempotent SQL scripts. Created `staging` (all-VARCHAR tables), `core` (3NF relational model with constraints), and `mart` (Star Schema with surrogate keys). Created `analytics` views over the mart. Populated the `dim_date` calendar for 2023-2026.

**Phase 3: Synthetic Data Generation**
- **Status:** ✅ **DONE** (Commit `f019f70`)
- **Details:** Write `src/data_generation/generate_data.py` using the `Faker` library. Must deterministically (using `seed=42`) generate ~20K appointments, 5K patients, and 15 clinics. Will include personal fields (name, phone, email) in `patients.csv` so the ETL pipeline can demonstrate privacy stripping. Main dataset must be clean (no intentional errors here). Outputs to `data/raw/`.

**Phase 4: ETL Extract + Data Validation Rules**
- **Status:** ✅ **DONE** (Commit `4563d13`)
- **Details:** Write `src/etl/extract.py` (pandas CSV reading) and `src/validation/validators.py`. Implement hard rules: check for invalid foreign keys, invalid statuses, invalid date ranges, and duplicates. Valid records continue; invalid records are explicitly saved to `data/rejected/`.

**Phase 5: ETL Transform & Load**
- **Status:** ✅ **DONE** (Commit `1d4476d`)
- **Details:** Write `src/etl/transform.py` and `src/etl/load.py`. Crucial privacy step: strip all personal fields from patient data. Normalize statuses, derive `no_show_flag` and `time_slot`, bucket `age_group`. Use SQLAlchemy/psycopg2 to load the transformed data into the PostgreSQL `staging`, then push to `core`, then build the `mart`. Create `src/etl/pipeline.py` to orchestrate E-T-L.

**Phase 6: Analytics Metrics Layer**
- **Status:** ✅ **DONE** (Commit `9b5db53`)
- **Details:** Write `src/analytics/metrics.py`. This Python module will query the SQL views created in Phase 2 (`vw_overall_metrics`, `vw_clinic_no_show_rate`, etc.) and bundle the results into a single, structured, privacy-safe JSON payload/dictionary. This output must contain absolutely no patient-level rows.

**Phase 7: AI Summarizer Interface**
- **Status:** ✅ **DONE** (Commit `b614930`)
- **Details:** Write `src/ai/interface.py` (abstract class), `mock_model.py` (deterministic fallback), and `ollama_model.py` (local LLM via HTTP). The system must pass the JSON payload from Phase 6 to the AI. The AI prompt must restrict the model to observing patterns without inventing causal claims.

**Phase 8: Testing**
- **Status:** ✅ **DONE** (Commit `401e54c`)
- **Details:** Write ≥5 tests in `tests/` using `pytest`. Must test: Metric correctness (no-show rate math), data validation (rejecting duplicates/bad FKs), privacy (proving the AI payload contains no personal fields), zero-denominator edge cases, and the Mock AI interface. Includes generating `tests/fixtures/invalid_appointments.csv` for the failure demo.

**Phase 9: Pipeline Entrypoint & Docker Polish**
- **Status:** 🟡 **PENDING**
- **Details:** Write `scripts/run_pipeline.py` as the main orchestrator (Data Gen -> ETL -> Analytics -> AI). Update `Dockerfile` and `docker-compose.yml` so that a clean `docker compose up --build` runs the entire project seamlessly from end to end.

**Phase 10: Documentation**
- **Status:** ❌ TODO
- **Details:** Write a comprehensive `README.md` containing setup instructions, architecture explanation, data model, testing, and demo steps. Write a 1-page `docs/design_decision.md` covering architecture trade-offs. Export the architecture diagram.

---

## 5. Current State & Next Steps

**Current Situation:**
- Phase 8 complete: The full comprehensive audit is finished.
- 18 tests are passing, proving validation, privacy, transformations, AI boundary limits, and zero-denominator safety.
- The pipeline is fully idempotent.
- The clean setup via `docker compose up --build` works flawlessly.
- A `CLINIC_MIN_SAMPLE` threshold was added to prevent misleading rankings from small-sample clinics.

**Immediate Next Step (Phase 9/10):**
Generate `README.md`, finalize documentation, and prepare for handover.

*(Models reading this: Acknowledge you have read the context and proceed directly with executing Phase 3).*
