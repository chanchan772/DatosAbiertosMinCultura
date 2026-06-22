"""Descarga de datos crudos desde datos.gov.co (API Socrata) y fuentes externas.

Usa `sodapy` para paginar sobre los datasets de Socrata. Los datos se guardan en
Parquet en `data/raw/` para consultas posteriores con DuckDB.

NOTA: los IDs de dataset (`SIREC_DATASET_ID`, `DANE_POBLACION_DATASET_ID`) deben
definirse en `.env` con el identificador 4x4 real del recurso en datos.gov.co.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from cinepredict.config import RAW_DIR, REFERENCE_DIR, settings

PAGE_SIZE = 50_000

# IDs de recurso (4x4) verificados en datos.gov.co
DIVIPOLA_DATASET_ID = "gdxc-w37w"  # DIVIPOLA - Códigos municipios (DANE), con lat/lon


def _socrata_client():
    from sodapy import Socrata

    # timeout amplio: algunos datasets de SIREC son grandes
    return Socrata(settings.socrata_domain, settings.socrata_app_token, timeout=120)


def download_socrata_dataset(dataset_id: str, out_path: Path) -> Path:
    """Descarga un dataset completo de Socrata paginando y lo guarda en Parquet."""
    client = _socrata_client()
    frames: list[pd.DataFrame] = []
    offset = 0
    while True:
        rows = client.get(dataset_id, limit=PAGE_SIZE, offset=offset)
        if not rows:
            break
        frames.append(pd.DataFrame.from_records(rows))
        logger.info(f"{dataset_id}: {offset + len(rows)} filas descargadas…")
        if len(rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    if not frames:
        raise RuntimeError(f"El dataset {dataset_id} no devolvió filas.")

    df = pd.concat(frames, ignore_index=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    logger.success(f"Guardado {out_path} ({len(df):,} filas).")
    return out_path


def download_sirec() -> Path:
    """Descarga las estadísticas de exhibición del SIREC."""
    if not settings.sirec_dataset_id:
        raise RuntimeError(
            "Falta SIREC_DATASET_ID en .env (identificador 4x4 del recurso en datos.gov.co)."
        )
    return download_socrata_dataset(settings.sirec_dataset_id, RAW_DIR / "sirec.parquet")


def download_dane_poblacion() -> Path:
    """Descarga las proyecciones de población del DANE."""
    if not settings.dane_poblacion_dataset_id:
        raise RuntimeError("Falta DANE_POBLACION_DATASET_ID en .env.")
    return download_socrata_dataset(
        settings.dane_poblacion_dataset_id, RAW_DIR / "dane_poblacion.parquet"
    )


def download_divipola() -> Path:
    """Descarga el diccionario DIVIPOLA del DANE desde datos.gov.co (API SODA).

    Recurso verificado `gdxc-w37w`: 1.122 municipios con código, nombre,
    departamento y coordenadas (longitud/latitud con coma decimal en origen).
    Se guarda en `data/reference/divipola.csv` (sí versionado), que es la llave
    territorial canónica del proyecto y la fuente de centroides para accesibilidad.
    """
    client = _socrata_client()
    rows = client.get(DIVIPOLA_DATASET_ID, limit=5000)
    df = pd.DataFrame.from_records(rows)

    # Normaliza al esquema interno; las coords vienen con coma decimal ("-75,58")
    out_df = pd.DataFrame({
        "cod_divipola": df["cod_mpio"],
        "municipio": df["nom_mpio"],
        "departamento": df["dpto"],
        "tipo": df.get("tipo_municipio"),
        "lon": df["longitud"].str.replace(",", ".", regex=False).astype(float),
        "lat": df["latitud"].str.replace(",", ".", regex=False).astype(float),
    })

    out_path = REFERENCE_DIR / "divipola.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False, encoding="utf-8")
    logger.success(f"DIVIPOLA: {len(out_df):,} municipios -> {out_path}")
    return out_path
