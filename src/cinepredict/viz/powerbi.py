"""Exportación a Power BI — vista espejo institucional.

Genera CSVs limpios (esquema estrella, codificación UTF-8 con BOM para que Power BI
respete las tildes) a partir de las proyecciones del modelo. Power BI Desktop los
importa directamente y reproduce el tablero para apropiación del Ministerio.

Tablas generadas en `powerbi/datos/`:
  dim_municipio.csv     dimensión territorial (DIVIPOLA + coords + departamento)
  fact_demanda.csv      demanda potencial / brecha 2027 por municipio
  fact_mensual.csv      serie mensual (histórico + proyección) por municipio
  fact_captura.csv      espectadores por exhibidor, municipio y año
"""

from __future__ import annotations

import pandas as pd
from loguru import logger

from cinepredict.config import PROCESSED_DIR, REFERENCE_DIR, ROOT_DIR

OUT_DIR = ROOT_DIR / "powerbi" / "datos"
ENC = "utf-8-sig"  # BOM: Power BI lee tildes correctamente


def export_powerbi() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    div = pd.read_csv(REFERENCE_DIR / "divipola.csv", dtype={"cod_divipola": str})
    div["cod_divipola"] = div["cod_divipola"].str.zfill(5)

    # --- Dimensión municipio ---
    dem = pd.read_parquet(PROCESSED_DIR / "proyeccion_demanda_2027.parquet")
    dem["cod_divipola"] = dem["cod_divipola"].astype(str).str.zfill(5)
    dim = div.merge(dem[["cod_divipola", "tiene_cine"]], on="cod_divipola", how="left")
    dim["tiene_cine"] = dim["tiene_cine"].fillna(0).astype(int)
    dim["tiene_sala"] = dim["tiene_cine"].map({1: "Con sala", 0: "Sin sala"})
    dim[["cod_divipola", "municipio", "departamento", "lat", "lon", "tiene_sala"]].to_csv(
        OUT_DIR / "dim_municipio.csv", index=False, encoding=ENC)

    # --- Hecho: demanda y brecha 2027 ---
    dem[["cod_divipola", "demanda_potencial", "espectadores_obs", "brecha",
         "poblacion_15_44", "dist_km_sala_cercana"]].to_csv(
        OUT_DIR / "fact_demanda.csv", index=False, encoding=ENC)

    # --- Hecho: serie mensual (histórico + proyección) ---
    serie = pd.read_parquet(PROCESSED_DIR / "series_mensuales.parquet")
    serie["fecha"] = pd.PeriodIndex(serie["periodo"], freq="M").to_timestamp()
    hist = serie[["cod_divipola", "fecha", "espectadores"]].copy()
    hist["tipo"] = "Histórico"
    fact_m = hist
    proy_path = PROCESSED_DIR / "proyeccion_mensual.parquet"
    if proy_path.exists():
        proy = pd.read_parquet(proy_path).rename(
            columns={"unique_id": "cod_divipola", "ds": "fecha",
                     "espectadores_pred": "espectadores"})
        proy["cod_divipola"] = proy["cod_divipola"].astype(str).str.zfill(5)
        proy["tipo"] = "Proyección"
        fact_m = pd.concat([hist, proy[["cod_divipola", "fecha", "espectadores", "tipo"]]],
                           ignore_index=True)
    fact_m["cod_divipola"] = fact_m["cod_divipola"].astype(str).str.zfill(5)
    fact_m.to_csv(OUT_DIR / "fact_mensual.csv", index=False, encoding=ENC)

    # --- Hecho: captura por exhibidor ---
    cap = pd.read_parquet(PROCESSED_DIR / "features_captura.parquet")
    cap["cod_divipola"] = cap["cod_divipola"].astype(str).str.zfill(5)
    cap[["cod_divipola", "exhibidor", "anio", "num_salas", "espectadores"]].to_csv(
        OUT_DIR / "fact_captura.csv", index=False, encoding=ENC)

    logger.success(f"Power BI: 4 tablas exportadas a {OUT_DIR}")
