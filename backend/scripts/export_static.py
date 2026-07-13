"""
export_static.py — Exporta todas las respuestas de la API como JSON estático para
desplegar el tablero como SPA en GitHub Pages (sin backend).

Genera en frontend/public/api/:
  overview.json, catalog.json, methodology.json, municipios.json, forecast.json
  demand_<banda>.json     (una por banda de edad)
  map_<banda>.json        (mapa enriquecido con rend_base por municipio)

Las partes interactivas (detalle por municipio, simulador, narrativa) se calculan
en el navegador a partir de estos JSON (ver frontend/src/app/core/static-compute.ts).

Uso:  python -m backend.scripts.export_static
"""
from __future__ import annotations

import json
import math
import warnings
from pathlib import Path

import numpy as np

from backend.app.models import overview, demand, forecast, catalog
from backend.app.models.data import municipal_panel
from backend.app.models.exhibitor import _rendimiento_comparables
from backend.app.models.methodology import PARAMS, METODOLOGIA

warnings.filterwarnings("ignore")

OUT = Path(__file__).resolve().parents[2] / "frontend" / "public" / "api"
OUT.mkdir(parents=True, exist_ok=True)
BANDAS = ["pob_15_30", "pob_15_45", "pob_15_60"]


def sanitize(obj):
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        v = float(obj)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def write(name: str, data) -> None:
    (OUT / name).write_text(json.dumps(sanitize(data), ensure_ascii=False), encoding="utf-8")
    print(f"  [ok] {name}")


def main():
    print("Exportando JSON estático a", OUT)
    write("overview.json", overview.compute())
    write("catalog.json", catalog.compute())
    write("methodology.json", {"parametros": PARAMS, "metodologia": METODOLOGIA})
    write("forecast.json", forecast.compute())

    panel_ref = municipal_panel(PARAMS["anio_referencia_demanda"], PARAMS["banda_objetivo_default"])
    munis = panel_ref[panel_ref["poblacion_objetivo"].notna()][
        ["cod_mpio", "municipio", "departamento", "salas_activas", "poblacion_objetivo"]
    ].sort_values("municipio").to_dict("records")
    write("municipios.json", munis)

    for banda in BANDAS:
        d = demand.compute(banda=banda)
        write(f"demand_{banda}.json", d)

        panel = municipal_panel(PARAMS["anio_referencia_demanda"], banda)
        geo = demand.geo_table(banda=banda)
        tasa = d["parametros"]["tasa_referencia"]
        for m in geo:
            salas = m.get("salas_activas") or 0
            if salas > 0 and m.get("admisiones"):
                m["rend_base"] = float(m["admisiones"]) / float(salas)  # sin redondear (paridad)
                m["origen_rend"] = "propio del municipio"
            else:
                rend, _ = _rendimiento_comparables(panel, float(m.get("poblacion_objetivo") or 0))
                m["rend_base"] = float(rend)
                m["origen_rend"] = "municipios comparables (sin oferta local)"
        write(f"map_{banda}.json", {
            "anio": PARAMS["anio_referencia_demanda"], "banda": banda,
            "tasa_referencia": tasa, "metodo_tasa": d["parametros"]["metodo_tasa"],
            "umbral_conurbacion_km": PARAMS["umbral_conurbacion_km"],
            "municipios": geo,
        })
    print("Listo.")


if __name__ == "__main__":
    main()
