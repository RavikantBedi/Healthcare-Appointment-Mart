"""
Centralized application settings.

Reads configuration from environment variables (loaded from .env file).
No secrets are hardcoded — all sensitive values come from the environment.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv


# Project root is two levels up from this file: src/config/settings.py → project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class DatabaseSettings:
    """PostgreSQL connection settings."""
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "healthcare"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "healthcare_pass"))
    host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    database: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "healthcare_mart"))

    @property
    def connection_url(self) -> str:
        """SQLAlchemy-compatible connection URL."""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def psycopg2_params(self) -> dict:
        """Connection parameters for psycopg2.connect()."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
            "password": self.password,
        }


@dataclass(frozen=True)
class AISettings:
    """AI summarizer settings."""
    backend: str = field(default_factory=lambda: os.getenv("AI_BACKEND", "mock"))
    # Ollama
    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2:1b"))
    # Gemini
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    # Grok
    xai_api_key: str = field(default_factory=lambda: os.getenv("XAI_API_KEY", ""))
    grok_model: str = field(default_factory=lambda: os.getenv("GROK_MODEL", "grok-3-mini"))


@dataclass(frozen=True)
class AnalyticsSettings:
    """Analytics layer configuration."""
    clinic_min_sample: int = field(default_factory=lambda: int(os.getenv("CLINIC_MIN_SAMPLE", "50")))


@dataclass(frozen=True)
class DataGenerationSettings:
    """Synthetic data generation parameters."""
    seed: int = field(default_factory=lambda: int(os.getenv("DATA_SEED", "42")))
    num_patients: int = field(default_factory=lambda: int(os.getenv("NUM_PATIENTS", "5000")))
    num_clinics: int = field(default_factory=lambda: int(os.getenv("NUM_CLINICS", "15")))
    num_appointments: int = field(default_factory=lambda: int(os.getenv("NUM_APPOINTMENTS", "20000")))


@dataclass(frozen=True)
class PathSettings:
    """File system paths."""
    project_root: Path = PROJECT_ROOT
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    raw_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "raw")
    processed_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "processed")
    rejected_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "rejected")
    sql_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "sql")
    test_fixtures_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "tests" / "fixtures")


@dataclass(frozen=True)
class Settings:
    """Top-level application settings container."""
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    ai: AISettings = field(default_factory=AISettings)
    analytics: AnalyticsSettings = field(default_factory=AnalyticsSettings)
    data_gen: DataGenerationSettings = field(default_factory=DataGenerationSettings)
    paths: PathSettings = field(default_factory=PathSettings)


# Singleton instance used throughout the application
settings = Settings()
