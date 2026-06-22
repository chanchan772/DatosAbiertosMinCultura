"""Variables de accesibilidad a salas de cine.

Para cada municipio se calcula la **distancia al municipio con salas más cercano**
usando las coordenadas oficiales del DIVIPOLA (DANE). Los municipios con oferta
propia tienen distancia 0. Esta variable captura la fricción territorial que
explica parte de la brecha de acceso del Reto 8.

Se usa la fórmula de Haversine (rápida, escala nacional). OSMnx/NetworkX permiten
refinar a tiempos de viaje reales sobre la red vial; se deja como mejora futura
en `accesibilidad_osmnx()` por su costo computacional a escala nacional.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RADIO_TIERRA_KM = 6371.0


def _haversine_matrix(lat: np.ndarray, lon: np.ndarray,
                      lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Distancia Haversine (km) entre cada punto de (lat,lon) y cada (lat2,lon2)."""
    lat = np.radians(lat)[:, None]
    lon = np.radians(lon)[:, None]
    lat2 = np.radians(lat2)[None, :]
    lon2 = np.radians(lon2)[None, :]
    dlat = lat2 - lat
    dlon = lon2 - lon
    a = np.sin(dlat / 2) ** 2 + np.cos(lat) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return RADIO_TIERRA_KM * 2 * np.arcsin(np.sqrt(a))


def distancia_a_sala_cercana(
    divipola: pd.DataFrame, municipios_con_cine: set[str]
) -> pd.DataFrame:
    """Devuelve, por municipio, la distancia (km) a la sala más cercana.

    `divipola`: columnas cod_divipola, lat, lon.
    `municipios_con_cine`: códigos DIVIPOLA con al menos una sala.
    """
    df = divipola.dropna(subset=["lat", "lon"]).copy()
    df["cod_divipola"] = df["cod_divipola"].astype(str).str.zfill(5)

    destino = df[df["cod_divipola"].isin(municipios_con_cine)]
    if destino.empty:
        df["dist_km_sala_cercana"] = np.nan
        df["tiene_cine"] = 0
        return df[["cod_divipola", "dist_km_sala_cercana", "tiene_cine"]]

    dist = _haversine_matrix(
        df["lat"].to_numpy(), df["lon"].to_numpy(),
        destino["lat"].to_numpy(), destino["lon"].to_numpy(),
    )
    df["dist_km_sala_cercana"] = dist.min(axis=1)
    df["tiene_cine"] = df["cod_divipola"].isin(municipios_con_cine).astype(int)
    # Los municipios con cine tienen distancia 0
    df.loc[df["tiene_cine"] == 1, "dist_km_sala_cercana"] = 0.0
    return df[["cod_divipola", "dist_km_sala_cercana", "tiene_cine"]]


def accesibilidad_osmnx(*args, **kwargs):  # pragma: no cover - mejora futura
    """Refinamiento con tiempos de viaje reales (OSMnx/NetworkX).

    Construye el grafo vial y resuelve rutas con peso 'travel_time'. Costoso a
    escala nacional; se reserva para análisis focalizados por subregión.
    """
    raise NotImplementedError(
        "Accesibilidad por red vial (OSMnx) reservada para análisis regional focalizado."
    )
