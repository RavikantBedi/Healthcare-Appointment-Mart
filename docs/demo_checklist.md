# Demo Checklist

- [x] Docker running
- [x] PostgreSQL healthy
- [x] `.env` configured (from `.env.example`)
- [x] `AI_BACKEND` confirmed (mock or ollama)
- [x] Qwen model (`qwen3:1.7b`) installed if using Ollama
- [x] Raw data generated (`data/raw/` CSVs present)
- [x] Pipeline executed successfully (`python -m src.etl.pipeline`)
- [x] Metrics payload generated (`data/processed/metrics_payload.json`)
- [x] Privacy check shown (no PII in payload)
- [x] AI summary shown (terminal output)
- [x] `pytest -v` passes (26/26 tests)
- [x] Failure fixture ready (`tests/fixtures/invalid_appointments.csv`)
- [x] Git repository clean
- [x] No secrets visible in code or `.env` tracking
