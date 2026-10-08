FROM python:3.11-slim

WORKDIR /app

# Install PostgreSQL client for psql access
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command: run the full pipeline
CMD ["python", "-m", "scripts.run_pipeline"]
