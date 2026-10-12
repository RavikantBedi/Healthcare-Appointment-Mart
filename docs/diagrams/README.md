# Database Diagrams

ER and flow diagrams for the four database layers. Each diagram exists in two forms:

| Diagram | Mermaid source | Rendered PNG |
| :--- | :--- | :--- |
| Staging schema (`staging.stg_*`) | [`staging-schema.mmd`](staging-schema.mmd) | `staging-schema.png` |
| Core schema (`core.*`, 3NF) | [`core-schema.mmd`](core-schema.mmd) | `core-schema.png` |
| Analytics star schema (`mart.*`) | [`analytics-star-schema.mmd`](analytics-star-schema.mmd) | `analytics-star-schema.png` |
| Analytical views (`analytics.vw_*`) | [`analytics-views.mmd`](analytics-views.mmd) | `analytics-views.png` |
| End-to-end data flow | [`data-flow-architecture.mmd`](data-flow-architecture.mmd) | `data-flow-architecture.png` |

## Accuracy notes

- All table names, column names, and data types are transcribed from the DDL in
  `sql/01_staging/`, `sql/02_core/`, `sql/03_mart/`, and `sql/04_analytics/`, and
  were re-verified against the live PostgreSQL database.
- **Solid relationships in the Core and Mart diagrams are physical foreign-key
  constraints** (verified via `pg_constraint`): 3 in `core`, 4 in `mart`.
- **Relationships in the Staging diagram are logical only** — staging tables carry
  no foreign keys by design (raw landing layer, all VARCHAR).
- **The Views diagram shows output columns only** — views have no foreign keys;
  their joins back to the mart star schema are logical (documented in the main
  README, section "Analytical Views").
- The DBeaver screenshots supplied with the documentation task were used as
  reference material; these Mermaid diagrams are redrawn equivalents, not copies
  of those screenshots.

## Re-rendering the PNGs

The `.png` files are generated from the `.mmd` sources with any Mermaid renderer.
Two easy options:

**Option 1 — Mermaid CLI (local, no network):**

```bash
npx -y @mermaid-js/mermaid-cli -i staging-schema.mmd -o staging-schema.png -b white
```

**Option 2 — a local Kroki container (gateway + mermaid microservice):**

```bash
docker network create kroki-net
docker run -d --name kroki-mermaid --network kroki-net yuzutech/kroki-mermaid
docker run -d --name kroki-render --network kroki-net -p 127.0.0.1:8000:8000 \
  -e KROKI_MERMAID_HOST=kroki-mermaid yuzutech/kroki

# POST the RAW diagram text (not base64) with Content-Type: text/plain
curl -sS -H "Content-Type: text/plain" --data-binary @staging-schema.mmd \
  http://127.0.0.1:8000/mermaid/png -o staging-schema.png

docker rm -f kroki-render kroki-mermaid && docker network rm kroki-net
```

> Note: only **GET** requests to Kroki require the base64(zlib) URL encoding.
> **POST** bodies must be the raw diagram source.
