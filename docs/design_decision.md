# Design & Decision Note

### Decision 1: PostgreSQL
**Why:**
- Strong relational integrity
- Powerful SQL analytics capabilities
- Support for complex constraints

### Decision 2: Layered architecture
**Why:**
- Strict separation of concerns (Raw vs. Normalized vs. Analytical)
- Clear traceability of data transformation
- Easier debugging and incremental logic building

### Decision 3: Core 3NF
**Why:**
- Provides a normalized operational model reflecting true entity relationships
- Reduces data duplication and update anomalies
- Enforces strict referential integrity (e.g., patient must exist before appointment)

### Decision 4: Star schema
**Why:**
- Analytical simplicity and intuitive querying
- Accelerated business metrics aggregations
- Highly suitable for dimensional querying and filtering by clinic, date, or type

### Decision 5: Python ETL
**Why:**
- The assessment dataset is small enough to fit in memory
- Enhances clarity and readability of the code
- Allows for easy and robust unit testing
- Avoids unnecessary orchestration complexity (e.g., Airflow, Spark) for a baseline platform

### Decision 6: Privacy-safe AI
**Why:**
- Healthcare is a highly regulated domain (HIPAA, GDPR)
- Must aggressively minimize data exposure to third-party or local LLMs
- AI models only need aggregated numbers, not patient histories

### Decision 7: Precomputed key_findings
**Why:**
- Deterministic calculations guarantee 100% mathematical accuracy
- Vastly reduces LLM hallucination (LLMs are poor at numerical sorting/ranking on large arrays)
- The LLM is restricted to its strength: language generation based on concrete, provided facts

### Decision 8: Mock + Ollama
**Why:**
- Reproducible tests that don't rely on flaky external networks
- Offline execution capability
- Local AI demonstration without exposing data or requiring paid API keys

### Decision 9: Truncate-and-reload
**Why:**
- Provides a perfectly deterministic assessment pipeline
- Simple reproducibility for reviewers
- Avoids the overhead of managing complex CDC (Change Data Capture) or upsert logic for a static synthetic dataset

### Trade-offs
This project is an assessment-scoped data platform. For simplicity, it does not include incremental loading, distributed processing (Spark), messaging queues (Kafka), or full pipeline orchestration (Airflow). The truncate-and-reload strategy is ideal for demonstrating the schema and analytics but would require modification for continuous, high-volume production data.
