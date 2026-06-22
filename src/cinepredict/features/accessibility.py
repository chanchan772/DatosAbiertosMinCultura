"""Variables de accesibilidad intermunicipal a salas de cine.

Para cada municipio sin oferta (o con oferta limitada) se estima el tiempo de
desplazamiento al municipio con salas más cercano, usando la red vial de
OpenStreetMap (OSMnx) y grafos de NetworkX. INVIAS/DNP complementan la red
primaria/secundaria.

El cálculo de matrices de tiempo es costoso; se cachea por municipio.
"""

from __future__ import annotations

import pandas as pd
from loguru import logger


def municipios_con_salas(analytic: pd.DataFrame) -> set[str]:
    """Conjunto de códigos DIVIPOLA que registran al menos una sala en SIREC."""
    con_salas = analytic.loc[analytic["num_salas"] > 0, "cod_divipola"]
    return set(con_salas.astype(str).str.zfill(5).unique())


def tiempo_a_sala_mas_cercana(
    centroides: pd.DataFrame, municipios_oferta: set[str]
) -> pd.DataFrame:
    """Tiempo de viaje (min) de cada municipio a la sala más cercana.

    `centroides`: columnas cod_divipola, lat, lon (centroide poblado del MGN).
    Devuelve: cod_divipola, min_tiempo_a_sala, cod_destino.

    TODO: construir el grafo vial con osmnx.graph_from_place / graph_from_bbox y
    resolver rutas con networkx.shortest_path_length(weight="travel_time").
    Por ahora se deja la firma y el cacheo para implementar en Fase 1/2.
    """
    logger.warning(
        "tiempo_a_sala_mas_cercana: implementación OSMnx pendiente; "
        "se devuelve estructura vacía como placeholder."
    )
    return pd.DataFrame(columns=["cod_divipola", "min_tiempo_a_sala", "cod_destino"])
