"""
population.py — Poblacion municipal por bandas de edad (DANE, base CNPV 2018).

FUENTE PRIMARIA (upstream): archivo oficial DANE de proyecciones municipales por
area, sexo y edad simple, actualizacion post-COVID, periodo 2020-2035. Es la
UNICA fuente que combina: proyeccion + edad simple + todos los municipios +
codigo DIVIPOLA de 5 digitos. Se descarga directo de dane.gov.co (no esta en
Socrata a nivel nacional-por-edad).

FUENTE datos.gov.co (obligatoria del concurso):
  - DIVIPOLA (gdxc-w37w) para la reconciliacion territorial (ver external.py).
  - Antioquia por edad (evm3-92yw) como VALIDACION CRUZADA independiente de las
    bandas de edad calculadas (transparencia: contrastamos el dato DANE contra
    otra publicacion oficial en el portal obligatorio).

Bandas de edad (asistencia a cine se concentra en jovenes-adultos):
  banda 15-30 = suma de edades simples 15..30 (inclusive)
  banda 15-45 = suma de edades simples 15..45 (inclusive)
  banda 15-60 = suma de edades simples 15..60 (inclusive)

Salida: data/external/poblacion_municipal.parquet
  cod_mpio, anio, poblacion_total, pob_15_30, pob_15_45, pob_15_60
"""
from __future__ import annotations

import json
import re
import warnings
from datetime import datetime, timezone

import pandas as pd
import requests

from ..config import DATA_EXTERNAL, DATOS_GOV_BASE

warnings.filterwarnings("ignore")

DANE_URL = (
    "https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Municipal/"
    "DCD-area-sexo-edad-proypoblacion-Mun-2020-2035-ActPostCOVID-19.xlsx"
)
DANE_XLSX = DATA_EXTERNAL / "DANE_proyecciones_mun_edad_2020_2035.xlsx"
OUT = DATA_EXTERNAL / "poblacion_municipal.parquet"
ANTIOQUIA_ID = "evm3-92yw"

ANIOS = [2024, 2025, 2026, 2027]
BANDAS = {"pob_15_30": (15, 30), "pob_15_45": (15, 45), "pob_15_60": (15, 60)}


def download_dane(force: bool = False) -> None:
    if DANE_XLSX.exists() and not force:
        print(f"  DANE xlsx ya en cache ({DANE_XLSX.stat().st_size:,} bytes)")
        return
    print("  Descargando archivo DANE (~66 MB, puede tardar) ...")
    with requests.get(DANE_URL, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(DANE_XLSX, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    print(f"  Descargado: {DANE_XLSX.stat().st_size:,} bytes")


def _age_columns(cols) -> dict[int, str]:
    """Mapea edad simple -> nombre de columna 'Total_N'."""
    out = {}
    for c in cols:
        m = re.match(r"^Total[_ ]?(\d+)$", str(c).strip())
        if m:
            out[int(m.group(1))] = c
    return out


def build_population(force: bool = False) -> pd.DataFrame:
    if OUT.exists() and not force:
        return pd.read_parquet(OUT)

    download_dane(force=force)
    print("  Leyendo hoja DANE (skiprows=8) ...")
    df = pd.read_excel(DANE_XLSX, sheet_name=0, skiprows=8)
    df.columns = [str(c).strip() for c in df.columns]

    # Estructura fija DANE (verificada en los datos): columnas 0..5 son
    #   0=DP  1=DPNOM  2=codigo 5 digitos (etiqueta 'MPIO')  3=nombre municipio
    #   4=AÑO  5=ÁREA GEOGRÁFICA. Las etiquetas 'MPIO'/'DPMP' del DANE estan
    #   invertidas respecto a lo intuitivo, por lo que detectamos por CONTENIDO:
    #   la columna de codigo es la que trae valores numericos de 4-5 digitos.
    cod_idx = 2
    for idx in (2, 3):
        sample = df.iloc[:50, idx].astype(str).str.fullmatch(r"\d{4,5}")
        if sample.mean() > 0.8:
            cod_idx = idx
            break
    df = df.rename(columns={
        df.columns[cod_idx]: "cod_mpio",
        df.columns[4]: "anio",
        df.columns[5]: "area",
    })
    df["cod_mpio"] = df["cod_mpio"].astype(str).str.extract(r"(\d+)")[0].str.zfill(5)
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df["area_n"] = df["area"].astype(str).str.strip().str.lower()

    # agregado municipal (ÁREA = 'Total', no las de cabecera/rural) y años objetivo
    total_mask = df["area_n"] == "total"
    df = df[total_mask & df["anio"].isin(ANIOS)].copy()
    print(f"  filas tras filtro (Total, {ANIOS}): {len(df)}")

    age_cols = _age_columns(df.columns)  # {edad_simple: 'Total_N'}
    if not age_cols:
        raise RuntimeError("No se encontraron columnas de edad 'Total_N' en el archivo DANE")

    # columna de poblacion total municipal ('Total' a secas)
    col_total = next((c for c in df.columns if str(c).strip().lower() == "total"), None)

    out = df[["cod_mpio", "anio"]].copy()
    for band, (lo, hi) in BANDAS.items():
        cols = [age_cols[a] for a in range(lo, hi + 1) if a in age_cols]
        out[band] = df[cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
    out["poblacion_total"] = (
        pd.to_numeric(df[col_total], errors="coerce") if col_total else pd.NA
    )
    out = out.groupby(["cod_mpio", "anio"], as_index=False).sum()
    out["anio"] = out["anio"].astype(int)
    out.to_parquet(OUT, index=False)
    _register("poblacion_municipal_dane", "DANE (dane.gov.co)", DANE_URL, len(out))
    print(f"  poblacion_municipal.parquet: {len(out)} filas (municipio x año)")
    return out


def validate_antioquia() -> dict:
    """Validacion cruzada vs datos.gov.co (Antioquia por edad, evm3-92yw).
    Compara la banda 15-30 (censo 2018) contra nuestra poblacion DANE 2020 para
    Medellin, como control de coherencia de magnitud. Solo informativo.
    """
    url = (f"{DATOS_GOV_BASE}/resource/{ANTIOQUIA_ID}.json"
           "?$select=codigomunicipio,sum(hombres_cabecera%2Bmujeres_cabecera"
           "%2Bhombres_centropoblado%2Bmujeres_centropoblado"
           "%2Bhombresruraldisperso%2Bmujeresruraldisperso) as pob_15_30"
           "&$where=codigomunicipio%3D%2705001%27 AND edad%3E=15 AND edad%3C=30"
           "&$group=codigomunicipio")
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        data = r.json()
        val = float(data[0]["pob_15_30"]) if data else None
    except Exception as e:
        return {"ok": False, "error": str(e)}
    _register("validacion_antioquia_edad", ANTIOQUIA_ID,
              f"{DATOS_GOV_BASE}/resource/{ANTIOQUIA_ID}.json", 1)
    return {"ok": True, "medellin_15_30_censo2018_datosgov": val, "query": url}


def _register(name: str, dataset_id: str, url: str, n: int) -> None:
    path = DATA_EXTERNAL / "external_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    manifest[name] = {
        "fuente": "DANE" if "dane" in url else "datos.gov.co (Socrata)",
        "dataset_id": dataset_id, "url": url, "filas": n,
        "descargado": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    print("Construyendo poblacion municipal por bandas de edad ...")
    pop = build_population(force=True)
    print(pop.head(6).to_string())
    print("\nValidacion cruzada Antioquia (datos.gov.co):")
    print(validate_antioquia())
