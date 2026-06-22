"""Ensamblaje de la matriz de features para los tres componentes del modelo.

Une la tabla analítica (SIREC) con la demografía (DANE 15–44) y la accesibilidad
(distancia a sala más cercana), y materializa tres insumos en data/processed/:

  features_demanda.parquet   municipio × año   → Componente A (demanda potencial)
  features_captura.parquet   municipio × exhibidor × año → Componente B (captura)
  series_mensuales.parquet   municipio × mes   → Componente C (estacionalidad)
"""

from __future__ import annotations

import pandas as pd
from loguru import logger

from cinepredict.config import PROCESSED_DIR, REFERENCE_DIR
from cinepredict.features.accessibility import distancia_a_sala_cercana


def _load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    analytic = pd.read_parquet(PROCESSED_DIR / "analytic.parquet")
    analytic["cod_divipola"] = analytic["cod_divipola"].astype(str).str.zfill(5)
    analytic["anio"] = analytic["periodo"].str.slice(0, 4).astype(int)
    dane = pd.read_parquet(PROCESSED_DIR / "dane_poblacion.parquet")
    dane["cod_divipola"] = dane["cod_divipola"].astype(str).str.zfill(5)
    divipola = pd.read_csv(REFERENCE_DIR / "divipola.csv", dtype={"cod_divipola": str})
    return analytic, dane, divipola


def build_all() -> None:
    analytic, dane, divipola = _load()

    # Accesibilidad (constante en el tiempo): distancia a sala más cercana
    municipios_con_cine = set(
        analytic.loc[analytic["num_salas"] > 0, "cod_divipola"].unique()
    )
    acc = distancia_a_sala_cercana(divipola, municipios_con_cine)

    # ---- Componente A: demanda municipal por año ----
    dem_muni = (
        analytic.groupby(["cod_divipola", "anio"], as_index=False)
        .agg(espectadores=("espectadores", "sum"),
             num_salas=("num_salas", "sum"),
             n_exhibidores=("exhibidor", "nunique"))
    )
    # Todos los municipios × años del DANE (para poder estimar demanda potencial en los sin cine)
    base = dane.merge(acc, on="cod_divipola", how="left")
    demanda = base.merge(dem_muni, on=["cod_divipola", "anio"], how="left")
    demanda[["espectadores", "num_salas", "n_exhibidores"]] = (
        demanda[["espectadores", "num_salas", "n_exhibidores"]].fillna(0)
    )
    demanda.to_parquet(PROCESSED_DIR / "features_demanda.parquet", index=False)
    logger.success(f"features_demanda: {len(demanda):,} filas (municipio × año)")

    # ---- Componente B: captura por exhibidor y año ----
    # num_salas: nº representativo de salas (promedio mensual), NO la suma anual,
    # para que la escala coincida con la entrada del simulador.
    cap = (
        analytic.groupby(["cod_divipola", "exhibidor", "anio"], as_index=False)
        .agg(espectadores=("espectadores", "sum"), num_salas=("num_salas", "mean"))
    )
    cap["num_salas"] = cap["num_salas"].round().clip(lower=1).astype(int)
    cap = cap.merge(dane, on=["cod_divipola", "anio"], how="left").merge(
        acc, on="cod_divipola", how="left"
    )
    cap.to_parquet(PROCESSED_DIR / "features_captura.parquet", index=False)
    logger.success(f"features_captura: {len(cap):,} filas (municipio × exhibidor × año)")

    # ---- Componente C: series mensuales por municipio ----
    serie = (
        analytic.groupby(["cod_divipola", "periodo"], as_index=False)
        .agg(espectadores=("espectadores", "sum"))
        .sort_values(["cod_divipola", "periodo"])
    )
    serie.to_parquet(PROCESSED_DIR / "series_mensuales.parquet", index=False)
    logger.success(f"series_mensuales: {len(serie):,} filas (municipio × mes)")
