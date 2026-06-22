"""Componente B — Captura por exhibidor.

Estima cuántos espectadores captura un exhibidor en un territorio dado, en
función del número de salas y las características municipales. Permite responder
la pregunta de **proyección para un exhibidor hipotético**: dado un municipio y
un número de salas, ¿cuántos espectadores esperaría capturar?

Se usa CatBoost por su manejo nativo de variables categóricas de alta
cardinalidad (exhibidor, municipio).
"""

from __future__ import annotations

import pandas as pd
from catboost import CatBoostRegressor, Pool

NUMERIC_FEATURES = ["num_salas", "poblacion_total", "prop_cinefila", "min_tiempo_a_sala"]
CATEGORICAL_FEATURES = ["cod_divipola", "exhibidor"]
TARGET = "espectadores"


def _pool(df: pd.DataFrame) -> Pool:
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    return Pool(
        data=df[features],
        label=df[TARGET] if TARGET in df else None,
        cat_features=CATEGORICAL_FEATURES,
    )


def train_capture_model(df: pd.DataFrame, params: dict | None = None) -> CatBoostRegressor:
    """Entrena el modelo de captura por exhibidor."""
    params = params or {
        "iterations": 1000,
        "learning_rate": 0.03,
        "depth": 8,
        "loss_function": "RMSE",
        "verbose": False,
    }
    model = CatBoostRegressor(**params)
    model.fit(_pool(df))
    return model


def proyectar_exhibidor(
    model: CatBoostRegressor,
    cod_divipola: str,
    num_salas: int,
    contexto_municipal: dict,
) -> float:
    """Predice espectadores para un exhibidor hipotético en un municipio."""
    fila = pd.DataFrame(
        [{
            "cod_divipola": cod_divipola,
            "exhibidor": "HIPOTETICO",
            "num_salas": num_salas,
            **contexto_municipal,
        }]
    )
    return float(model.predict(_pool(fila))[0])
