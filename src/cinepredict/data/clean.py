"""Construcción de la tabla analítica: unidad sala × municipio × período.

Usa DuckDB para consultar los Parquet crudos sin cargarlos completos en memoria,
reconcilia territorio contra DIVIPOLA y valida el resultado con Pandera antes de
escribir `data/processed/analytic.parquet`.

Las transformaciones concretas dependen del esquema real de SIREC; los pasos
están marcados con TODO para completarse al inspeccionar los datos crudos.
"""

from __future__ import annotations

import duckdb
from loguru import logger

from cinepredict.config import PROCESSED_DIR, RAW_DIR
from cinepredict.data.schemas import validate_analytic


def build_analytic_table():
    """Cruza SIREC + DANE, normaliza al grano analítico y valida."""
    sirec_path = RAW_DIR / "sirec.parquet"
    if not sirec_path.exists():
        raise FileNotFoundError(
            f"No existe {sirec_path}. Ejecuta primero: cinepredict download --source sirec"
        )

    con = duckdb.connect()
    con.execute(f"CREATE VIEW sirec AS SELECT * FROM read_parquet('{sirec_path.as_posix()}')")

    logger.info("Columnas detectadas en SIREC:")
    logger.info(con.execute("DESCRIBE sirec").fetchdf().to_string())

    # TODO: ajustar esta consulta a los nombres de columna reales de SIREC.
    # Objetivo: agrupar a periodo YYYY-MM × municipio × exhibidor con
    #           num_salas y espectadores agregados.
    df = con.execute(
        """
        SELECT
            municipio,
            departamento,
            exhibidor,
            periodo,
            COUNT(DISTINCT sala)          AS num_salas,
            SUM(espectadores)::BIGINT     AS espectadores
        FROM sirec
        GROUP BY municipio, departamento, exhibidor, periodo
        """
    ).fetchdf()

    # Reconciliación territorial contra DIVIPOLA
    from cinepredict.data.territorial import reconcile

    df = reconcile(df, municipio_col="municipio", departamento_col="departamento")

    # Validación de esquema (falla con reporte si hay inconsistencias)
    df = validate_analytic(df)

    out = PROCESSED_DIR / "analytic.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.success(f"Tabla analítica: {len(df):,} filas -> {out}")
    return out
