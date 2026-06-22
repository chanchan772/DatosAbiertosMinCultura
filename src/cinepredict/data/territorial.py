"""Reconciliación territorial contra el código DIVIPOLA del DANE.

Los nombres de municipio en SIREC pueden no coincidir literalmente con los
oficiales (tildes, mayúsculas, homónimos entre departamentos). Aquí se
normaliza el texto y se resuelve al código DIVIPOLA de 5 dígitos, que es la
llave territorial canónica del proyecto.
"""

from __future__ import annotations

import unicodedata

import pandas as pd

from cinepredict.config import REFERENCE_DIR


def normalize_name(name: str) -> str:
    """Minúsculas, sin tildes y sin espacios extra para hacer matching robusto."""
    if not isinstance(name, str):
        return ""
    nfkd = unicodedata.normalize("NFKD", name)
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().split())


def load_divipola() -> pd.DataFrame:
    """Carga el diccionario DIVIPOLA de referencia (municipio -> código).

    Se espera un CSV en data/reference/divipola.csv con columnas:
        cod_divipola, municipio, departamento
    Descargable del Marco Geoestadístico Nacional / DANE.
    """
    path = REFERENCE_DIR / "divipola.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró {path}. Descargar el diccionario DIVIPOLA del DANE "
            "y guardarlo como data/reference/divipola.csv."
        )
    df = pd.read_csv(path, dtype={"cod_divipola": str})
    df["_key"] = (df["municipio"].map(normalize_name) + "|"
                  + df["departamento"].map(normalize_name))
    return df


def reconcile(df: pd.DataFrame, municipio_col: str, departamento_col: str) -> pd.DataFrame:
    """Añade la columna `cod_divipola` resolviendo municipio+departamento.

    Reporta las filas no resueltas para revisión manual (vacíos estructurales).
    """
    divipola = load_divipola()
    df = df.copy()
    df["_key"] = (df[municipio_col].map(normalize_name) + "|"
                  + df[departamento_col].map(normalize_name))
    merged = df.merge(
        divipola[["_key", "cod_divipola"]], on="_key", how="left"
    ).drop(columns="_key")

    sin_match = merged["cod_divipola"].isna().sum()
    if sin_match:
        from loguru import logger

        logger.warning(f"{sin_match} filas sin código DIVIPOLA; revisar manualmente.")
    return merged
