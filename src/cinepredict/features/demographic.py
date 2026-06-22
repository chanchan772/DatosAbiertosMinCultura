"""Variables demográficas por municipio a partir de las proyecciones DANE.

Construye, por `cod_divipola` y año, indicadores como población total,
proporción en rango etario de mayor consumo cinematográfico (p.ej. 15-44) y
densidad, que alimentan el componente A (demanda potencial municipal).
"""

from __future__ import annotations

import pandas as pd

# Rango etario de mayor propensión al consumo de cine (ajustable con la evidencia)
EDAD_CINEFILA = (15, 44)


def build_demographic_features(dane: pd.DataFrame) -> pd.DataFrame:
    """Devuelve features demográficas por (cod_divipola, anio).

    Espera columnas DANE normalizadas: cod_divipola, anio, edad, poblacion.
    """
    df = dane.copy()
    df["cod_divipola"] = df["cod_divipola"].astype(str).str.zfill(5)

    total = (
        df.groupby(["cod_divipola", "anio"], as_index=False)["poblacion"]
        .sum()
        .rename(columns={"poblacion": "poblacion_total"})
    )

    lo, hi = EDAD_CINEFILA
    cinefila = (
        df[df["edad"].between(lo, hi)]
        .groupby(["cod_divipola", "anio"], as_index=False)["poblacion"]
        .sum()
        .rename(columns={"poblacion": "poblacion_cinefila"})
    )

    out = total.merge(cinefila, on=["cod_divipola", "anio"], how="left")
    out["poblacion_cinefila"] = out["poblacion_cinefila"].fillna(0)
    out["prop_cinefila"] = out["poblacion_cinefila"] / out["poblacion_total"]
    return out
