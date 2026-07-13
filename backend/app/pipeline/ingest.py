"""
ingest.py — Ingesta y normalizacion de los 5 Excel crudos (fuente SIREC).

Produce tablas limpias en parquet dentro de data/processed/, ya pseudonimizadas,
mas un manifiesto (catalog_manifest.json) que alimenta la seccion "Catalogo de
datos" del tablero (que contiene cada Excel, con que se cruza y como se usa).

Tablas de salida:
  fact_taquilla                 detalle transaccional 2026 (sala x titulo x fecha)
  serie_diaria_nacional         asistencia diaria nacional 2007-2026
  dim_complejos                 oferta: complejos con nº salas y capacidad
  admisiones_municipio_anual    admisiones + salas activas por municipio 2024/25/26
  dim_peliculas                 catalogo de largometrajes exhibidos (2020+)
  dim_estrenos_colombia         estrenos de cine colombiano

Ejecucion:  python -m backend.app.pipeline.ingest
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import pandas as pd

from ..config import (
    DATOS_RAW,
    DATA_PROCESSED,
    DATA_INTERIM,
    TAQUILLA_ANIO,
    TAQUILLA_CORTE,
)
from .anonymize import Pseudonymizer
from .text_utils import norm_text

warnings.filterwarnings("ignore")

F_TAQUILLA = "Taquilla 2026-Colarco.xlsx"
F_DATOS = "Datos abiertos.xlsx"
F_SALAS = "Salas de Cine Registradas y Activas.xlsx"
F_ESTR_TOTAL = "HISTORICO Estrenos Total.xlsx"
F_ESTR_COL = "HISTORICO Estrenos Colombia.xlsx"


def _canon(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Renombra columnas emparejando por nombre normalizado (robusto a acentos,
    espacios sobrantes y mayusculas)."""
    ren = {}
    for c in df.columns:
        key = norm_text(c)
        if key in mapping:
            ren[c] = mapping[key]
    return df.rename(columns=ren)


# ---------------------------------------------------------------- TAQUILLA
def ingest_taquilla() -> pd.DataFrame:
    df = pd.read_excel(DATOS_RAW / F_TAQUILLA, sheet_name="Base")
    df = _canon(df, {
        "ano reporte": "anio_reporte",
        "fecha exhibicion": "fecha_exhibicion",
        "id exhibidor": "id_exhibidor",
        "exhibidor": "exhibidor",
        "complejo": "complejo",
        "id complejo": "id_complejo",
        "id sala": "id_sala",
        "titulo": "titulo",
        "admisiones": "admisiones",
        "compl departamento": "departamento",
        "compl municipio": "municipio",
        "titulo genero": "genero",
        "titulo duracion": "duracion_tipo",
        "titulo clasificacion": "clasificacion",
        "titulo nacion": "nacion",
        "titulo fecha 1ra exh": "fecha_1ra_exh",
        "diasemana": "dia_semana",
        "ano estreno": "anio_estreno",
        "catalogo estreno": "catalogo_estreno",
        "titulo tipo": "titulo_tipo",
    })
    keep = [c for c in [
        "anio_reporte", "fecha_exhibicion", "id_exhibidor", "exhibidor",
        "complejo", "id_complejo", "id_sala", "titulo", "admisiones",
        "departamento", "municipio", "genero", "duracion_tipo", "clasificacion",
        "nacion", "fecha_1ra_exh", "dia_semana", "anio_estreno",
        "catalogo_estreno", "titulo_tipo",
    ] if c in df.columns]
    df = df[keep].copy()
    df["fecha_exhibicion"] = pd.to_datetime(df["fecha_exhibicion"], errors="coerce")
    df["admisiones"] = pd.to_numeric(df["admisiones"], errors="coerce").fillna(0).astype(int)
    df["mes"] = df["fecha_exhibicion"].dt.month
    # el ID propietario se descarta; exhibidor/complejo se tokenizan en run()
    if "id_exhibidor" in df.columns:
        df = df.drop(columns=["id_exhibidor"])
    return df


# ---------------------------------------------------------------- SERIE DIARIA
def ingest_serie_diaria() -> pd.DataFrame:
    df = pd.read_excel(DATOS_RAW / F_DATOS, sheet_name="Espectadores por dia")
    df = _canon(df, {
        "fecha": "fecha", "asistencia": "asistencia",
        "semana calendario": "semana_calendario",
    })
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["asistencia"] = pd.to_numeric(df["asistencia"], errors="coerce")
    df = df.dropna(subset=["fecha"]).sort_values("fecha").reset_index(drop=True)
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["dia_semana"] = df["fecha"].dt.dayofweek  # 0=lunes
    return df[["fecha", "anio", "mes", "dia_semana", "semana_calendario", "asistencia"]]


# ---------------------------------------------------------------- COMPLEJOS (oferta)
def ingest_complejos() -> pd.DataFrame:
    df = pd.read_excel(DATOS_RAW / F_SALAS, sheet_name="Base Datos", header=1)
    df = _canon(df, {
        "exhibidor": "exhibidor",
        "exhibidor nombre comercial": "exhibidor_comercial",
        "complejo nombre": "complejo",
        "complejo departamento": "departamento",
        "complejo municipio": "municipio",
        "complejo direccion": "direccion",   # se ELIMINA (PII)
        "no salas": "n_salas",
        "capacidad esp": "capacidad",
    })
    keep = [c for c in ["exhibidor", "complejo", "departamento", "municipio",
                        "n_salas", "capacidad"] if c in df.columns]
    df = df[keep].copy()
    df = df.dropna(subset=["municipio"])
    df["n_salas"] = pd.to_numeric(df["n_salas"], errors="coerce").fillna(0).astype(int)
    df["capacidad"] = pd.to_numeric(df["capacidad"], errors="coerce").fillna(0).astype(int)
    return df  # exhibidor/complejo se tokenizan en run()


# ---------------------------------------------------------------- ADMISIONES x MUNICIPIO
def ingest_admisiones_municipio() -> pd.DataFrame:
    """Hoja 'AdmisionesXmunicipio': encabezado en filas 2-3 (multinivel).
    Columnas por posicion tras skiprows=4:
      0 clave(depto+mpio) | 1 Departamento | 2 Ciudad
      3 #salas 2024 | 4 adm(miles) 2024 | 5 #salas 2025 | 6 adm 2025 | 7 #salas 2026 | 8 adm 2026
    Se transforma a formato largo. Admisiones vienen en MILES.
    """
    raw = pd.read_excel(DATOS_RAW / F_SALAS, sheet_name="AdmisionesXmunicipio",
                        header=None, skiprows=4)
    cols = ["clave", "departamento", "municipio",
            "salas_2024", "adm_2024", "salas_2025", "adm_2025",
            "salas_2026", "adm_2026"]
    raw = raw.iloc[:, :len(cols)]
    raw.columns = cols
    raw = raw.dropna(subset=["departamento", "municipio"], how="any")
    rows = []
    for _, r in raw.iterrows():
        for anio in (2024, 2025, 2026):
            salas = pd.to_numeric(r.get(f"salas_{anio}"), errors="coerce")
            adm = pd.to_numeric(r.get(f"adm_{anio}"), errors="coerce")
            rows.append({
                "departamento": str(r["departamento"]).strip(),
                "municipio": str(r["municipio"]).strip(),
                "anio": anio,
                "salas_activas": None if pd.isna(salas) else int(salas),
                "admisiones": None if pd.isna(adm) else float(adm) * 1000.0,  # miles -> unidades
                "admisiones_miles": None if pd.isna(adm) else float(adm),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- PELICULAS (catalogo)
def ingest_peliculas() -> pd.DataFrame:
    df = pd.read_excel(DATOS_RAW / F_ESTR_TOTAL, sheet_name="Detalle Largometrajes",
                       header=2)
    df = _canon(df, {
        "ano": "anio", "fecha 1ra exhibicion": "fecha_1ra_exh",
        "titulo local": "titulo", "duracion tipo": "duracion_tipo",
        "duracion en minutos": "duracion_min", "genero": "genero",
        "clasificacion": "clasificacion", "nacionalidad": "nacionalidad",
        "nacion": "nacion", "admisiones": "admisiones",
        "municipios de exhibicion": "n_municipios",
        "exhibidores": "n_exhibidores", "complejos de exhibicion": "n_complejos",
        "pantallas de exhibicion": "n_pantallas",
        "semanas de exhibicion": "n_semanas", "dias de exhibicion": "n_dias",
    })
    keep = [c for c in ["anio", "titulo", "duracion_tipo", "duracion_min",
                        "genero", "clasificacion", "nacionalidad", "nacion",
                        "admisiones", "n_municipios", "n_exhibidores",
                        "n_complejos", "n_pantallas", "n_semanas", "n_dias"]
            if c in df.columns]
    df = df[keep].copy()
    df = df.dropna(subset=["titulo"])
    for c in ["admisiones", "n_municipios", "n_exhibidores", "n_complejos",
              "n_pantallas", "duracion_min"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def ingest_estrenos_colombia() -> pd.DataFrame:
    df = pd.read_excel(DATOS_RAW / F_ESTR_COL, sheet_name="ESTRENOS Consolidado",
                       header=1)
    df = _canon(df, {
        "ano estreno": "anio", "fecha 1ra exhibicion": "fecha_1ra_exh",
        "titulo local": "titulo", "duracion tipo": "duracion_tipo",
        "duracion en minutos": "duracion_min", "genero": "genero",
        "clasificacion": "clasificacion", "nacionalidad": "nacionalidad",
        "admisiones": "admisiones",
    })
    keep = [c for c in ["anio", "fecha_1ra_exh", "titulo", "duracion_tipo",
                        "duracion_min", "genero", "clasificacion",
                        "nacionalidad", "admisiones"] if c in df.columns]
    df = df[keep].copy().dropna(subset=["titulo"])
    df["admisiones"] = pd.to_numeric(df["admisiones"], errors="coerce")
    df["fecha_1ra_exh"] = pd.to_datetime(df["fecha_1ra_exh"], errors="coerce")
    return df


# ---------------------------------------------------------------- ORQUESTADOR
def run() -> dict:
    taquilla = ingest_taquilla()
    complejos = ingest_complejos()

    # --- anonimizacion: registrar todos los valores, finalizar y tokenizar ---
    anon = Pseudonymizer()
    for df in (taquilla, complejos):
        anon.register_series(df["exhibidor"], "EXH")
        anon.register_series(df["complejo"], "CPX")
    anon.finalize()
    for df in (taquilla, complejos):
        df["exhibidor_tok"] = anon.tokenize_series(df["exhibidor"], "EXH")
        df["complejo_tok"] = anon.tokenize_series(df["complejo"], "CPX")
        df.drop(columns=[c for c in ["exhibidor", "complejo"] if c in df.columns], inplace=True)
    anon.save_mapping()

    tables: dict[str, pd.DataFrame] = {
        "fact_taquilla": taquilla,
        "serie_diaria_nacional": ingest_serie_diaria(),
        "dim_complejos": complejos,
        "admisiones_municipio_anual": ingest_admisiones_municipio(),
        "dim_peliculas": ingest_peliculas(),
        "dim_estrenos_colombia": ingest_estrenos_colombia(),
    }

    manifest = {"tablas": {}, "anonimizacion": {
        "tecnica": "Seudonimos secuenciales estables (EXH-001, CPX-001, ...) sin relacion con el nombre",
        "campos_pseudonimizados": ["exhibidor", "complejo"],
        "campos_eliminados": ["direccion (PII)", "id_exhibidor propietario"],
        "preserva_resultados": True,
        "irreversible_desde_token": True,
    }}
    for name, df in tables.items():
        out = DATA_PROCESSED / f"{name}.parquet"
        df.to_parquet(out, index=False)
        manifest["tablas"][name] = {
            "filas": int(df.shape[0]),
            "columnas": list(map(str, df.columns)),
            "archivo": out.name,
        }
        print(f"  [ok] {name:28} {df.shape[0]:>7,} filas -> {out.name}")

    (DATA_INTERIM / "catalog_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print("Ingesta CinePredict (SIREC) ...")
    run()
    print("Listo.")
