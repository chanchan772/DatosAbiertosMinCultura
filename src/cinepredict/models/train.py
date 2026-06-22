"""Orquestación del entrenamiento de los tres componentes, con trazabilidad MLflow.

Carga la tabla analítica, construye features, entrena A/B/C y registra parámetros
y métricas en MLflow. Los modelos entrenados se guardan en `models/`.
"""

from __future__ import annotations

import mlflow
import pandas as pd
from loguru import logger

from cinepredict.config import MODELS_DIR, PROCESSED_DIR, settings


def _load_analytic() -> pd.DataFrame:
    path = PROCESSED_DIR / "analytic.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Ejecuta primero: cinepredict clean"
        )
    return pd.read_parquet(path)


def run() -> None:
    """Entrena los componentes A (demanda), B (captura) y C (estacionalidad)."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment("cinepredict")

    analytic = _load_analytic()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # --- Componente C: estacionalidad / series de tiempo ---
    with mlflow.start_run(run_name="C_estacionalidad"):
        from cinepredict.models import seasonality

        long_df = seasonality.to_long_format(analytic)
        meses = (settings.forecast_horizon_year - pd.Timestamp.now().year + 1) * 12
        fcst = seasonality.fit_forecast(long_df, horizon_months=max(meses, 12))
        fcst.to_parquet(MODELS_DIR / "forecast_estacional.parquet")
        mlflow.log_param("series", long_df["unique_id"].nunique())
        logger.success("Componente C entrenado.")

    # --- Componentes A y B requieren features demográficas/accesibilidad ---
    # TODO: ensamblar features (demographic + accessibility) y entrenar A y B.
    logger.info(
        "Componentes A y B: pendientes de ensamblar features demográficas y de "
        "accesibilidad (ver features/). La estructura ya está en models/demand.py "
        "y models/capture.py."
    )
