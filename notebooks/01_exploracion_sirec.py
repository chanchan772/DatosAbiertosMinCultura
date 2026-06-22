"""Notebook reactivo (Marimo) — exploración inicial de SIREC.

Ejecutar:  marimo edit notebooks/01_exploracion_sirec.py

Marimo se usa en lugar de Jupyter clásico para garantizar reproducibilidad real:
no hay estado oculto entre celdas.
"""

import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import duckdb
    import marimo as mo

    from cinepredict.config import RAW_DIR

    return RAW_DIR, duckdb, mo


@app.cell
def _(RAW_DIR, duckdb, mo):
    sirec_path = RAW_DIR / "sirec.parquet"
    if sirec_path.exists():
        con = duckdb.connect()
        df = con.execute(
            f"SELECT * FROM read_parquet('{sirec_path.as_posix()}') LIMIT 1000"
        ).fetchdf()
        out = mo.ui.table(df)
    else:
        out = mo.md(
            "⚠️ No hay datos. Ejecuta primero `cinepredict download --source sirec`."
        )
    out
    return


if __name__ == "__main__":
    app.run()
