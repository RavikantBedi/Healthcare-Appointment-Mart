#!/bin/bash
# ==================================================
# Database Initialization Script
# Runs automatically on first PostgreSQL container start
# via docker-entrypoint-initdb.d
# ==================================================

set -e

echo "=== Initializing Healthcare Appointment Mart Database ==="

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

    -- Create schemas
    CREATE SCHEMA IF NOT EXISTS staging;
    CREATE SCHEMA IF NOT EXISTS core;
    CREATE SCHEMA IF NOT EXISTS mart;
    CREATE SCHEMA IF NOT EXISTS analytics;

    -- Confirm
    SELECT schema_name FROM information_schema.schemata
    WHERE schema_name IN ('staging', 'core', 'mart', 'analytics')
    ORDER BY schema_name;

EOSQL

echo "=== Schemas created successfully ==="
