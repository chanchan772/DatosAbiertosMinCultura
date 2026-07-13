"""
run_pipeline.py — Orquesta el pipeline completo de datos (reproducible).

Orden:
  1. Ingesta y anonimización de los 5 Excel SIREC       -> data/processed
  2. Descarga DIVIPOLA (datos.gov.co)                    -> data/external
  3. Descarga/parseo población DANE por edad + validación-> data/external
  4. Reconciliación territorial contra DIVIPOLA          -> data/processed

Uso:  python -m backend.run_pipeline
"""
from __future__ import annotations

from backend.app.pipeline import ingest, external, population, reconcile


def main():
    print("== 1/4 Ingesta y anonimización ==")
    ingest.run()
    print("\n== 2/4 DIVIPOLA (datos.gov.co) ==")
    external.fetch_divipola()
    external.fetch_divipola_departamentos()
    print("\n== 3/4 Población DANE por edad ==")
    population.build_population()
    print("  validación datos.gov.co:", population.validate_antioquia().get("ok"))
    print("\n== 4/4 Reconciliación territorial ==")
    _, rep = reconcile.build_crosswalk()
    print(f"  cobertura DIVIPOLA: {rep['cobertura_pct']}%")
    print("\nPipeline completo.")


if __name__ == "__main__":
    main()
