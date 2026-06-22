"""Esquemas declarativos de validación (Pandera) para las tablas del proyecto.

Validar temprano y fallar rápido: los datos crudos de SIREC se validan al
ingresar y la tabla analítica se valida antes del modelado. Ajustar los nombres
de columna a los del recurso real de datos.gov.co una vez confirmados.
"""

from __future__ import annotations

import pandera.pandas as pa
from pandera.typing import Series

CODIGO_DIVIPOLA = r"^\d{5}$"  # 2 dígitos depto + 3 municipio


class SirecRawSchema(pa.DataFrameModel):
    """Esquema laxo para los datos crudos de SIREC (antes de normalizar)."""

    municipio: Series[str] = pa.Field(nullable=True)
    espectadores: Series[float] = pa.Field(ge=0, nullable=True, coerce=True)

    class Config:
        strict = False  # SIREC trae más columnas; no fallar por ellas
        coerce = True


class AnalyticTableSchema(pa.DataFrameModel):
    """Tabla analítica normalizada: unidad sala × municipio × período."""

    cod_divipola: Series[str] = pa.Field(str_matches=CODIGO_DIVIPOLA)
    municipio: Series[str]
    departamento: Series[str]
    periodo: Series[str] = pa.Field(str_matches=r"^\d{4}-\d{2}$")  # YYYY-MM
    exhibidor: Series[str] = pa.Field(nullable=True)
    num_salas: Series[int] = pa.Field(ge=0, coerce=True)
    espectadores: Series[int] = pa.Field(ge=0, coerce=True)

    class Config:
        strict = False
        coerce = True


def validate_analytic(df):
    """Valida la tabla analítica y devuelve el dataframe validado."""
    return AnalyticTableSchema.validate(df, lazy=True)
