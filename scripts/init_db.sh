#!/bin/bash
# ==================================================
# Database Initialization Script
# Runs automatically on first PostgreSQL container start
# via docker-entrypoint-initdb.d
# ==================================================

set -e

echo "=== Initializing Healthcare Appointment Mart Database ==="

# Execute SQL files in dependency order
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/00_schemas.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/01_staging/create_staging_tables.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/02_core/create_core_tables.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/03_mart/create_dim_tables.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/03_mart/create_fact_table.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/03_mart/populate_dim_date.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/04_analytics/create_views.sql

echo "=== Database Structure created successfully ==="
