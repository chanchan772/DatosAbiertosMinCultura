"""Generación de figuras y reportes para la presentación final."""

from __future__ import annotations

from loguru import logger

from cinepredict.config import FIGURES_DIR


def generate() -> None:
    """Genera las figuras clave (mapas de brecha, series proyectadas, ranking)."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    # TODO: mapa coroplético de demanda insatisfecha (PyDeck/Folium),
    #       series proyectadas por departamento (Plotly), ranking de municipios.
    logger.info(f"Las figuras se escribirán en {FIGURES_DIR}.")
