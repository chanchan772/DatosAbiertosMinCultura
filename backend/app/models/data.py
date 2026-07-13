"""
data.py — Capa de acceso a datos y construccion del panel municipal.

Carga las tablas procesadas (parquet) y las externas (DIVIPOLA, poblacion DANE),
y arma el PANEL MUNICIPAL: la tabla analitica base con una fila por municipio del
universo nacional (1.122 municipios DIVIPOLA), enriquecida con:
  - poblacion por banda de edad (DANE) del año de referencia,
  - admisiones realizadas y salas activas (SIREC 'AdmisionesXmunicipio'),
  - geolocalizacion (DIVIPOLA).
Los municipios sin actividad de cine aparecen con salas=0 y admisiones=0
(candidatos a brecha estructural).
"""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from ..config import DATA_PROCESSED, DATA_EXTERNAL


@lru_cache(maxsize=None)
def load(name: str) -> pd.DataFrame:
    for base in (DATA_PROCESSED, DATA_EXTERNAL):
        p = base / f"{name}.parquet"
        if p.exists():
            return pd.read_parquet(p)
    raise FileNotFoundError(f"No existe la tabla {name}.parquet")


def crosswalk() -> pd.DataFrame:
    return load("crosswalk_municipios")


@lru_cache(maxsize=8)
def municipal_panel(anio_ref: int = 2025, banda: str = "pob_15_45") -> pd.DataFrame:
    """Panel municipal para el año de referencia.

    Devuelve una fila por municipio DIVIPOLA con poblacion objetivo, admisiones
    realizadas, salas activas y geolocalizacion.
    """
    divi = load("divipola_municipios")[["cod_mpio", "municipio", "departamento", "lat", "lon"]].copy()
    pop = load("poblacion_municipal")
    pop_y = pop[pop["anio"] == anio_ref][["cod_mpio", banda, "poblacion_total"]].rename(
        columns={banda: "poblacion_objetivo"}
    )

    # admisiones realizadas + salas activas del año de referencia, ya con cod_mpio
    adm = load("admisiones_municipio_anual")
    cw = crosswalk()[["departamento_src", "municipio_src", "cod_mpio"]]
    adm = adm.merge(
        cw,
        left_on=["departamento", "municipio"],
        right_on=["departamento_src", "municipio_src"],
        how="left",
    )
    adm_y = adm[adm["anio"] == anio_ref][["cod_mpio", "salas_activas", "admisiones"]].copy()
    # un municipio puede repetirse si el crosswalk mapeo variantes: agregamos
    adm_y = adm_y.dropna(subset=["cod_mpio"]).groupby("cod_mpio", as_index=False).agg(
        salas_activas=("salas_activas", "sum"),
        admisiones=("admisiones", "sum"),
    )

    panel = divi.merge(pop_y, on="cod_mpio", how="left")
    panel = panel.merge(adm_y, on="cod_mpio", how="left")
    panel["salas_activas"] = panel["salas_activas"].fillna(0.0)
    panel["admisiones"] = panel["admisiones"].fillna(0.0)
    panel["anio_ref"] = anio_ref
    panel["banda"] = banda
    # densidad de oferta: salas por 100k habitantes objetivo
    panel["salas_por_100k"] = panel.apply(
        lambda r: (r["salas_activas"] / r["poblacion_objetivo"] * 1e5)
        if r["poblacion_objetivo"] and r["poblacion_objetivo"] > 0 else 0.0,
        axis=1,
    )
    return panel
