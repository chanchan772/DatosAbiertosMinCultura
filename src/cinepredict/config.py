"""Configuración central del proyecto: rutas y ajustes cargados desde el entorno.

Las rutas se derivan de la raíz del repositorio, de modo que el código funciona
igual en local, en Docker o en CI sin rutas absolutas codificadas.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del repo: este archivo vive en src/cinepredict/config.py -> subir 3 niveles
ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"
REFERENCE_DIR = DATA_DIR / "reference"

MODELS_DIR = ROOT_DIR / "models"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"


class Settings(BaseSettings):
    """Ajustes leídos de variables de entorno / archivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Socrata (datos.gov.co)
    socrata_domain: str = "www.datos.gov.co"
    socrata_app_token: str | None = None
    sirec_dataset_id: str | None = None
    dane_poblacion_dataset_id: str | None = None

    # API de Claude
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-4-8"

    # MLflow
    mlflow_tracking_uri: str = "./mlruns"

    # Modelado
    forecast_horizon_year: int = 2027
    covid_break_start: str = "2020-03"  # inicio de la intervención COVID
    covid_break_end: str = "2021-12"


settings = Settings()


def ensure_dirs() -> None:
    """Crea las carpetas de datos/artefactos si no existen."""
    for directory in (
        RAW_DIR,
        INTERIM_DIR,
        PROCESSED_DIR,
        EXTERNAL_DIR,
        REFERENCE_DIR,
        MODELS_DIR,
        FIGURES_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
