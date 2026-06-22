"""Interfaz de línea de comandos del proyecto.

Uso:
    cinepredict download --source sirec
    cinepredict clean
    cinepredict train
    cinepredict report
"""

from __future__ import annotations

from enum import Enum

import typer
from loguru import logger

from cinepredict.config import ensure_dirs

app = typer.Typer(
    help="CinePredict — pipeline de predicción de espectadores de cine en Colombia.",
    no_args_is_help=True,
)


class Source(str, Enum):
    sirec = "sirec"
    dane = "dane"
    all = "all"


@app.command()
def download(
    source: Source = typer.Option(Source.all, help="Fuente de datos a descargar."),
) -> None:
    """Descarga datos crudos desde datos.gov.co (Socrata) y fuentes externas."""
    ensure_dirs()
    from cinepredict.data import download as dl

    if source in (Source.sirec, Source.all):
        logger.info("Descargando SIREC…")
        dl.download_sirec()
    if source in (Source.dane, Source.all):
        logger.info("Descargando proyecciones DANE…")
        dl.download_dane_poblacion()
    logger.success("Descarga finalizada.")


@app.command()
def clean() -> None:
    """Limpia y normaliza a la unidad de análisis sala × municipio × período."""
    from cinepredict.data import clean as cl

    cl.build_analytic_table()
    logger.success("Tabla analítica construida en data/processed/.")


@app.command()
def train() -> None:
    """Entrena los tres componentes del modelo (A, B, C)."""
    from cinepredict.models import train as tr

    tr.run()
    logger.success("Entrenamiento finalizado. Ver MLflow para las métricas.")


@app.command()
def report() -> None:
    """Genera figuras y reportes para la presentación final."""
    from cinepredict.viz import report as rp

    rp.generate()
    logger.success("Reportes generados en reports/.")


if __name__ == "__main__":
    app()
