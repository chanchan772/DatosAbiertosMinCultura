"""
external.py — Descarga y cache de fuentes obligatorias de datos.gov.co.

Fuentes:
  - DIVIPOLA municipios (gdxc-w37w): codigos oficiales DANE/DNP + geolocalizacion.
    Se usa para reconciliacion territorial y para el mapa del tablero.
  - Poblacion municipal por edad (DANE): se integra en population.py una vez
    identificada la fuente Socrata; aqui se deja el fetch generico de Socrata.

Todo se cachea en data/external/ como parquet para reproducibilidad offline.
Cada descarga registra su procedencia (id, url, fecha) en un manifiesto.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
import requests

from ..config import (
    DATOS_GOV_BASE,
    DIVIPOLA_MUNICIPIOS_ID,
    DIVIPOLA_DEPARTAMENTOS_ID,
    DATA_EXTERNAL,
)

TIMEOUT = 40


def socrata_get(dataset_id: str, params: dict | None = None) -> pd.DataFrame:
    """Descarga un recurso Socrata completo como DataFrame."""
    url = f"{DATOS_GOV_BASE}/resource/{dataset_id}.json"
    p = {"$limit": 50000}
    if params:
        p.update(params)
    r = requests.get(url, params=p, timeout=TIMEOUT)
    r.raise_for_status()
    return pd.DataFrame(r.json())


def _to_float_coma(s: pd.Series) -> pd.Series:
    """Convierte '-75,581775' -> -75.581775 (coma decimal DANE)."""
    return pd.to_numeric(
        s.astype(str).str.replace(",", ".", regex=False), errors="coerce"
    )


def fetch_divipola(force: bool = False) -> pd.DataFrame:
    cache = DATA_EXTERNAL / "divipola_municipios.parquet"
    if cache.exists() and not force:
        return pd.read_parquet(cache)

    df = socrata_get(DIVIPOLA_MUNICIPIOS_ID, {"$limit": 2000})
    # normalizacion de columnas esperadas
    ren = {"cod_dpto": "cod_dpto", "dpto": "departamento", "cod_mpio": "cod_mpio",
           "nom_mpio": "municipio", "tipo_municipio": "tipo",
           "longitud": "lon", "latitud": "lat"}
    df = df.rename(columns={k: v for k, v in ren.items() if k in df.columns})
    if "lon" in df.columns:
        df["lon"] = _to_float_coma(df["lon"])
    if "lat" in df.columns:
        df["lat"] = _to_float_coma(df["lat"])
    df["cod_mpio"] = df["cod_mpio"].astype(str).str.zfill(5)
    df["cod_dpto"] = df["cod_dpto"].astype(str).str.zfill(2)

    df.to_parquet(cache, index=False)
    _register("divipola_municipios", DIVIPOLA_MUNICIPIOS_ID, len(df))
    return df


def fetch_divipola_departamentos(force: bool = False) -> pd.DataFrame:
    cache = DATA_EXTERNAL / "divipola_departamentos.parquet"
    if cache.exists() and not force:
        return pd.read_parquet(cache)
    df = socrata_get(DIVIPOLA_DEPARTAMENTOS_ID, {"$limit": 100})
    df.to_parquet(cache, index=False)
    _register("divipola_departamentos", DIVIPOLA_DEPARTAMENTOS_ID, len(df))
    return df


def _register(name: str, dataset_id: str, n: int) -> None:
    path = DATA_EXTERNAL / "external_manifest.json"
    manifest = {}
    if path.exists():
        manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest[name] = {
        "fuente": "datos.gov.co (Socrata)",
        "dataset_id": dataset_id,
        "url": f"{DATOS_GOV_BASE}/resource/{dataset_id}.json",
        "filas": n,
        "descargado": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    print("Descargando DIVIPOLA municipios ...")
    d = fetch_divipola(force=True)
    print(f"  {len(d)} municipios | cols: {list(d.columns)}")
    print(d.head(3).to_string())
    print("Descargando DIVIPOLA departamentos ...")
    dd = fetch_divipola_departamentos(force=True)
    print(f"  {len(dd)} departamentos")
