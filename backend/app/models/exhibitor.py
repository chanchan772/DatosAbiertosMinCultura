"""
exhibitor.py — Simulador de exhibidor hipotético (captura de espectadores).

Responde: "¿cuántos espectadores captaría un exhibidor con N salas en el
municipio X?". El cálculo es transparente y contextualizado: no entrega un
número aislado, sino el rendimiento por sala del municipio, la captura estimada
y el CONTEXTO de mercado (demanda potencial, realizada e insatisfecha) para que
el usuario entienda si esa captura es demanda nueva o redistribución.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import municipal_panel
from .demand import reference_rate
from .methodology import PARAMS, METODOLOGIA
from .trace import CalculationTrace


def _rendimiento_comparables(panel: pd.DataFrame, pob_obj: float) -> tuple[float, dict]:
    """Rendimiento por sala (adm/sala) mediano de municipios COMPARABLES por
    tamaño de población objetivo (para municipios sin salas donde no hay dato
    propio). Comparables = municipios con oferta en el mismo quintil de población.
    """
    con = panel[(panel["salas_activas"] > 0) & (panel["poblacion_objetivo"] > 0)].copy()
    con["rend"] = con["admisiones"] / con["salas_activas"]
    # quintil de poblacion objetivo del municipio consultado
    try:
        bins = pd.qcut(con["poblacion_objetivo"], 5, duplicates="drop")
        con["bin"] = bins
        objetivo_bin = pd.cut([pob_obj], bins=bins.cat.categories)[0]
        grupo = con[con["bin"] == objetivo_bin]
        if len(grupo) < 3:
            grupo = con
    except Exception:
        grupo = con
    rend = float(grupo["rend"].median())
    return rend, {"n_comparables": int(len(grupo)),
                  "rend_mediano_comparables": round(rend, 1)}


def simulate(cod_mpio: str, n_salas: int, anio_ref: int | None = None,
             banda: str | None = None) -> dict:
    anio_ref = anio_ref or PARAMS["anio_referencia_demanda"]
    banda = banda or PARAMS["banda_objetivo_default"]
    cod_mpio = str(cod_mpio).zfill(5)
    panel = municipal_panel(anio_ref, banda)
    row = panel[panel["cod_mpio"] == cod_mpio]
    if row.empty:
        return {"error": f"Municipio {cod_mpio} no encontrado"}
    r = row.iloc[0]

    tasa_ref, _ = reference_rate(panel)
    pob_obj = float(r["poblacion_objetivo"] or 0)
    salas_actuales = float(r["salas_activas"])
    adm_actuales = float(r["admisiones"])
    potencial = pob_obj * tasa_ref
    insatisfecha_ctx = max(0.0, potencial - adm_actuales)

    tr = CalculationTrace(
        f"Simulación de exhibidor — {r['municipio']} ({r['departamento']})",
        f"{n_salas} sala(s) hipotética(s), año de referencia {anio_ref}, banda {banda}.",
    )
    tr.fuente("Admisiones y salas (SIREC)", "AdmisionesXmunicipio (Salas registradas y activas)",
              f"Año {anio_ref} completo")
    tr.fuente("Población objetivo (DANE)", f"banda {banda}", f"{pob_obj:,.0f} hab.")
    for s in METODOLOGIA["captura_exhibidor"]["supuestos"]:
        tr.supuesto(s)
    for l in METODOLOGIA["captura_exhibidor"]["limitaciones"]:
        tr.limitacion(l)

    # Paso 1: rendimiento por sala del municipio (o comparables si no hay oferta)
    if salas_actuales > 0:
        rend = adm_actuales / salas_actuales
        origen_rend = "propio del municipio"
        tr.paso("1. Rendimiento por sala (municipio)",
                "rendimiento_sala = admisiones_municipio / salas_activas",
                {"admisiones_municipio": round(adm_actuales), "salas_activas": salas_actuales},
                round(rend), "espectadores/sala/año")
    else:
        rend, diag = _rendimiento_comparables(panel, pob_obj)
        origen_rend = "municipios comparables (sin oferta local)"
        tr.paso("1. Rendimiento por sala (comparables)",
                "rendimiento_sala = mediana( adm/sala ) de municipios de tamaño similar",
                {"n_comparables": diag["n_comparables"], "poblacion_objetivo": round(pob_obj)},
                round(rend), "espectadores/sala/año",
                "El municipio no tiene salas activas; se usa un grupo comparable por población.")

    # Paso 2: captura bruta
    captura_bruta = n_salas * rend
    tr.paso("2. Captura bruta estimada",
            "captura_bruta = N_salas × rendimiento_sala",
            {"N_salas": n_salas, "rendimiento_sala": round(rend)},
            round(captura_bruta), "espectadores/año")

    # Paso 3: ajuste por saturación de mercado (headroom)
    #   Si el mercado ya está saturado, gran parte de la captura es redistribución.
    headroom = (insatisfecha_ctx / potencial) if potencial > 0 else 0.0
    demanda_nueva = min(captura_bruta, insatisfecha_ctx)
    redistribucion = max(0.0, captura_bruta - insatisfecha_ctx)
    tr.paso("3. Descomposición demanda nueva vs redistribución",
            "demanda_nueva = min(captura_bruta, demanda_insatisfecha) ; "
            "redistribución = captura_bruta − demanda_nueva",
            {"captura_bruta": round(captura_bruta), "demanda_insatisfecha_local": round(insatisfecha_ctx)},
            {"demanda_nueva": round(demanda_nueva), "redistribucion": round(redistribucion)},
            "espectadores/año",
            "Transparencia: parte de la captura puede provenir de competidores, no ser demanda nueva.")

    # Paso 4: cuota de mercado estimada
    cuota = captura_bruta / potencial if potencial > 0 else None
    tr.paso("4. Cuota de mercado estimada",
            "cuota = captura_bruta / demanda_potencial_municipio",
            {"captura_bruta": round(captura_bruta), "demanda_potencial": round(potencial)},
            round(cuota, 3) if cuota is not None else None, "ratio")

    return {
        "cod_mpio": cod_mpio, "municipio": r["municipio"], "departamento": r["departamento"],
        "n_salas": n_salas,
        "rendimiento_sala": round(rend),
        "origen_rendimiento": origen_rend,
        "captura_estimada": round(captura_bruta),
        "demanda_nueva": round(demanda_nueva),
        "redistribucion": round(redistribucion),
        "cuota_mercado": round(cuota, 4) if cuota is not None else None,
        "contexto": {
            "poblacion_objetivo": pob_obj,
            "demanda_potencial": round(potencial),
            "demanda_realizada": round(adm_actuales),
            "demanda_insatisfecha": round(insatisfecha_ctx),
            "salas_actuales": salas_actuales,
            "headroom_pct": round(100 * headroom, 1),
        },
        "lat": _f(r["lat"]), "lon": _f(r["lon"]),
        "trace": tr.to_dict(),
    }


def _f(v):
    try:
        return None if pd.isna(v) else float(v)
    except Exception:
        return None


if __name__ == "__main__":
    # ejemplos: municipio sin oferta grande y uno con oferta
    for cod, n in [("44001", 3), ("05001", 5), ("11001", 8)]:
        s = simulate(cod, n)
        if "error" in s:
            print(s); continue
        print(f"\n{s['municipio']} ({s['departamento']}) — {n} salas")
        print(f"  rendimiento/sala: {s['rendimiento_sala']:,} ({s['origen_rendimiento']})")
        print(f"  captura estimada: {s['captura_estimada']:,}/año "
              f"| nueva={s['demanda_nueva']:,} redistrib={s['redistribucion']:,} "
              f"| cuota={s['cuota_mercado']}")
        print(f"  contexto: potencial={s['contexto']['demanda_potencial']:,} "
              f"realizada={s['contexto']['demanda_realizada']:,} "
              f"insatisf={s['contexto']['demanda_insatisfecha']:,} "
              f"salas_actuales={s['contexto']['salas_actuales']}")
