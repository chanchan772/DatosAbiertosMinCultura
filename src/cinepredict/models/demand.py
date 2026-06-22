"""Componente A — Demanda potencial municipal.

Regresión que estima los espectadores potenciales de un municipio en función de
sus variables demográficas (DANE) y de accesibilidad (OSM/INVIAS), con
independencia de la oferta instalada. La diferencia entre demanda potencial y
asistencia observada identifica los municipios con **demanda insatisfecha**.
"""

from __future__ import annotations

import lightgbm as lgb
import pandas as pd
from sklearn.metrics import mean_absolute_error

FEATURES = [
    "poblacion_total",
    "poblacion_cinefila",
    "prop_cinefila",
    "min_tiempo_a_sala",
]
TARGET = "espectadores"


def train_demand_model(df: pd.DataFrame, params: dict | None = None) -> lgb.LGBMRegressor:
    """Entrena el modelo de demanda potencial municipal."""
    params = params or {"n_estimators": 600, "learning_rate": 0.03, "num_leaves": 63}
    X = df[FEATURES]
    y = df[TARGET]
    model = lgb.LGBMRegressor(**params)
    model.fit(X, y)
    return model


def demanda_insatisfecha(df: pd.DataFrame, model: lgb.LGBMRegressor) -> pd.DataFrame:
    """Brecha = demanda potencial estimada − asistencia observada (>0 = insatisfecha)."""
    out = df.copy()
    out["demanda_potencial"] = model.predict(out[FEATURES])
    out["brecha"] = out["demanda_potencial"] - out[TARGET]
    return out.sort_values("brecha", ascending=False)


def evaluate(df_test: pd.DataFrame, model: lgb.LGBMRegressor) -> float:
    return mean_absolute_error(df_test[TARGET], model.predict(df_test[FEATURES]))
