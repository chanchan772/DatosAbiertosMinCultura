"""
demand.py — Demanda potencial y demanda insatisfecha por municipio.

Responde a la pregunta del reto: "identificar municipios con demanda insatisfecha".
El metodo es deliberadamente transparente y NO mezcla metricas: clasifica cada
municipio en uno de tres grupos (sin oferta / subatendido / saturado-polo) y
reporta la demanda insatisfecha con una formula distinta y explicita por grupo.
Ver methodology.METODOLOGIA['demanda_insatisfecha'].
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import municipal_panel
from .methodology import PARAMS, METODOLOGIA
from .trace import CalculationTrace

CLASES = {
    "sin_oferta": "Sin oferta (brecha estructural)",
    "subatendido": "Con oferta, subatendido",
    "saturado": "Saturado / polo de atracción",
}


def reference_rate(panel: pd.DataFrame, winsor: float | None = None) -> tuple[float, dict]:
    """Tasa de asistencia per capita de referencia (robusta).

    Problema a evitar: los municipios "polo de atracción" (satélites pequeños con
    un gran complejo que capta público de toda una región — p.ej. Sabaneta, Chía)
    tienen admisiones >> población residente, con tasas per cápita disparadas. Si
    se usaran, inflarían artificialmente la demanda potencial de todo el país.

    Método: sobre los municipios CON oferta se calcula la tasa individual
    admisiones/poblacion_objetivo, se EXCLUYEN los polos extremos (por encima del
    percentil `winsor`), y la tasa de referencia es el promedio PONDERADO POR
    POBLACIÓN del grupo restante = Σ admisiones / Σ población_objetivo. La
    ponderación por población evita que municipios diminutos dominen el benchmark.
    """
    winsor = winsor or PARAMS["winsor_polos_percentil"]
    con_oferta = panel[(panel["salas_activas"] > 0) & (panel["poblacion_objetivo"] > 0)].copy()
    con_oferta["tasa_i"] = con_oferta["admisiones"] / con_oferta["poblacion_objetivo"]
    cap = float(con_oferta["tasa_i"].quantile(winsor))
    polos = con_oferta[con_oferta["tasa_i"] > cap]
    ref = con_oferta[con_oferta["tasa_i"] <= cap]
    tasa = float(ref["admisiones"].sum() / ref["poblacion_objetivo"].sum())
    # tasa nacional simple (para contraste / transparencia)
    con_pob = panel[panel["poblacion_objetivo"] > 0]
    tasa_nacional = float(con_pob["admisiones"].sum() / con_pob["poblacion_objetivo"].sum())
    diag = {
        "municipios_con_oferta": int(len(con_oferta)),
        "percentil_winsor": winsor,
        "tasa_tope_excluida": round(cap, 4),
        "n_polos_excluidos": int(len(polos)),
        "polos_excluidos": polos.nlargest(6, "tasa_i")[
            ["municipio", "departamento", "poblacion_objetivo", "admisiones", "tasa_i"]
        ].round(2).to_dict("records"),
        "tasa_referencia_ponderada": round(tasa, 4),
        "tasa_nacional_simple": round(tasa_nacional, 4),
        "n_grupo_referencia": int(len(ref)),
    }
    return tasa, diag


def classified_panel(anio_ref: int, banda: str) -> tuple[pd.DataFrame, float, dict]:
    """Panel municipal con demanda potencial, penetración, clase y demanda
    insatisfecha ya calculadas. Reutilizado por compute(), geo_table() y el
    simulador para garantizar consistencia total entre módulos.
    """
    panel = municipal_panel(anio_ref, banda).copy()
    tasa_ref, diag = reference_rate(panel)
    panel["demanda_potencial"] = panel["poblacion_objetivo"].fillna(0) * tasa_ref
    panel["penetracion"] = np.where(
        panel["demanda_potencial"] > 0,
        panel["admisiones"] / panel["demanda_potencial"], np.nan,
    )

    def clasificar(r):
        if r["salas_activas"] <= 0:
            return "sin_oferta"
        if pd.isna(r["penetracion"]) or r["penetracion"] < PARAMS["penetracion_saturacion"]:
            return "subatendido"
        return "saturado"

    panel["clase"] = panel.apply(clasificar, axis=1)

    def insatisfecha(r):
        if r["clase"] == "sin_oferta":
            return r["demanda_potencial"]
        if r["clase"] == "subatendido":
            return max(0.0, r["demanda_potencial"] - r["admisiones"])
        return 0.0

    panel["demanda_insatisfecha"] = panel.apply(insatisfecha, axis=1)

    # Distancia al polo más cercano (municipios saturados) para distinguir la
    # brecha REAL por aislamiento de la brecha APARENTE por conurbación.
    polos = panel[(panel["clase"] == "saturado") & panel["lat"].notna() & panel["lon"].notna()]
    polos_coords = polos[["lat", "lon"]].to_numpy(dtype=float)
    umbral = PARAMS["umbral_conurbacion_km"]

    def dist_polo(r):
        if len(polos_coords) == 0 or pd.isna(r["lat"]) or pd.isna(r["lon"]):
            return None
        return round(float(_haversine_min(r["lat"], r["lon"], polos_coords)), 1)

    panel["dist_polo_km"] = panel.apply(dist_polo, axis=1)

    def brecha_tipo(r):
        if r["clase"] != "sin_oferta":
            return None
        d = r["dist_polo_km"]
        if d is None:
            return "aislamiento"
        return "conurbacion" if d <= umbral else "aislamiento"

    panel["brecha_tipo"] = panel.apply(brecha_tipo, axis=1)
    return panel, tasa_ref, diag


def _haversine_min(lat, lon, coords) -> float:
    """Distancia mínima (km) de (lat,lon) a un array de coords [[lat,lon],...]."""
    R = 6371.0
    lat1 = np.radians(float(lat)); lon1 = np.radians(float(lon))
    lat2 = np.radians(coords[:, 0]); lon2 = np.radians(coords[:, 1])
    dlat = lat2 - lat1; dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return float(np.min(2 * R * np.arcsin(np.sqrt(a))))


def geo_table(anio_ref: int | None = None, banda: str | None = None) -> list[dict]:
    """Tabla geo por municipio para el mapa de brechas (todos los municipios)."""
    anio_ref = anio_ref or PARAMS["anio_referencia_demanda"]
    banda = banda or PARAMS["banda_objetivo_default"]
    panel, _, _ = classified_panel(anio_ref, banda)
    cols = ["cod_mpio", "municipio", "departamento", "clase", "poblacion_objetivo",
            "salas_activas", "admisiones", "demanda_potencial", "penetracion",
            "demanda_insatisfecha", "dist_polo_km", "brecha_tipo", "lat", "lon"]
    sub = panel[panel["poblacion_objetivo"].notna()][cols]
    return _clean_records(sub)


def compute(anio_ref: int | None = None, banda: str | None = None) -> dict:
    anio_ref = anio_ref or PARAMS["anio_referencia_demanda"]
    banda = banda or PARAMS["banda_objetivo_default"]

    tr = CalculationTrace(
        "Demanda potencial e insatisfecha por municipio",
        f"Año de referencia {anio_ref}, banda objetivo {banda}.",
    )
    tr.fuente("Población por edad", "DANE — Proyecciones municipales 2020–2035 (edades simples)",
              f"Banda {banda} del año {anio_ref}, agregada por código DIVIPOLA.")
    tr.fuente("Admisiones y salas activas", "SIREC — 'Salas de Cine Registradas y Activas' "
              "(hoja AdmisionesXmunicipio)", f"Año {anio_ref}.")
    tr.fuente("Territorio", "DIVIPOLA — datos.gov.co (gdxc-w37w)",
              "Universo de 1.122 municipios y geolocalización.")
    for s in METODOLOGIA["demanda_potencial"]["supuestos"]:
        tr.supuesto(s)
    for s in METODOLOGIA["demanda_insatisfecha"]["supuestos"]:
        tr.supuesto(s)
    for l in METODOLOGIA["demanda_insatisfecha"]["limitaciones"]:
        tr.limitacion(l)

    # Panel clasificado (misma lógica compartida con el simulador y el mapa)
    panel, tasa_ref, diag = classified_panel(anio_ref, banda)

    # Paso 1: tasa de referencia (robusta, winsorizada)
    tr.paso(
        "Tasa de asistencia per cápita de referencia (robusta)",
        f"tasa_ref = Σ admisiones / Σ poblacion_{banda}, sobre municipios con oferta "
        f"excluyendo polos de atracción (tasa > percentil 90).",
        {"municipios_con_oferta": diag["municipios_con_oferta"],
         "polos_excluidos": diag["n_polos_excluidos"],
         "tasa_nacional_simple_contraste": diag["tasa_nacional_simple"]},
        tasa_ref, "admisiones por habitante objetivo al año",
        "Promedio ponderado por población; se excluyen satélites que atraen público "
        "de otros municipios para no inflar el benchmark.",
    )
    # Paso 2: demanda potencial por municipio
    tr.paso("Demanda potencial municipal",
            "demanda_potencial(m) = poblacion_objetivo(m) × tasa_ref",
            {"tasa_ref": round(tasa_ref, 4)}, None, "espectadores/año",
            "Se aplica a los 1.122 municipios con proyección de población.")
    # Paso 3-4: penetración, clasificación y demanda insatisfecha por grupo
    tr.paso(
        "Demanda insatisfecha por grupo",
        METODOLOGIA["demanda_insatisfecha"]["formula"],
        {}, None, "espectadores/año",
        "Cada grupo usa una fórmula distinta; nunca se suman peras con manzanas.",
    )

    # Resumen nacional por clase
    resumen = []
    for clase in ["sin_oferta", "subatendido", "saturado"]:
        sub = panel[panel["clase"] == clase]
        resumen.append({
            "clase": clase,
            "etiqueta": CLASES[clase],
            "municipios": int(len(sub)),
            "poblacion_objetivo": float(sub["poblacion_objetivo"].sum()),
            "admisiones_realizadas": float(sub["admisiones"].sum()),
            "demanda_potencial": float(sub["demanda_potencial"].sum()),
            "demanda_insatisfecha": float(sub["demanda_insatisfecha"].sum()),
        })

    total_insatisfecha = float(panel["demanda_insatisfecha"].sum())
    total_potencial = float(panel["demanda_potencial"].sum())
    total_real = float(panel["admisiones"].sum())               # admisiones totales (incl. desplazamiento)
    atendida_local = total_potencial - total_insatisfecha        # demanda RESIDENTE atendida localmente
    cobertura_residente = round(100 * atendida_local / total_potencial, 2) if total_potencial else 0
    tr.paso(
        "Totales nacionales y cobertura coherente",
        "cobertura_residente = (potencial − insatisfecha) / potencial. Se calcula así (no con "
        "admisiones/potencial) porque las admisiones de municipios saturados incluyen público "
        "de otros municipios (visitantes), que no pertenecen a su demanda potencial residente.",
        {"potencial_total": round(total_potencial),
         "insatisfecha_total": round(total_insatisfecha),
         "admisiones_totales_incl_desplazamiento": round(total_real)},
        f"{cobertura_residente}%", "cobertura residente",
    )

    # Ranking de municipios con mayor demanda insatisfecha (excluye saturados)
    cols = ["cod_mpio", "municipio", "departamento", "clase", "poblacion_objetivo",
            "salas_activas", "admisiones", "demanda_potencial", "penetracion",
            "demanda_insatisfecha", "dist_polo_km", "brecha_tipo", "lat", "lon"]
    top = panel[panel["demanda_insatisfecha"] > 0].nlargest(25, "demanda_insatisfecha")[cols]

    return {
        "parametros": {"anio_ref": anio_ref, "banda": banda,
                       "metodo_tasa": "promedio ponderado por población excluyendo polos > p"
                       + str(int(PARAMS["winsor_polos_percentil"] * 100)),
                       "tasa_referencia": round(tasa_ref, 5)},
        "diagnostico_tasa": diag,
        "resumen_por_clase": resumen,
        "totales": {
            "demanda_potencial": total_potencial,
            "demanda_residente_atendida": atendida_local,
            "admisiones_totales": total_real,
            "demanda_insatisfecha": total_insatisfecha,
            "cobertura_pct": cobertura_residente,
        },
        "top_insatisfecha": _clean_records(top),
        "trace": tr.to_dict(),
    }


def municipio_detail(cod_mpio: str, anio_ref: int | None = None,
                     banda: str | None = None) -> dict:
    """Detalle paso a paso para UN municipio (drill-down '¿Cómo se calcula?')."""
    anio_ref = anio_ref or PARAMS["anio_referencia_demanda"]
    banda = banda or PARAMS["banda_objetivo_default"]
    panel, tasa_ref, _ = classified_panel(anio_ref, banda)
    row = panel[panel["cod_mpio"] == str(cod_mpio).zfill(5)]
    if row.empty:
        return {"error": f"Municipio {cod_mpio} no encontrado"}
    r = row.iloc[0]
    pob = float(r["poblacion_objetivo"] or 0)
    potencial = float(r["demanda_potencial"])
    real = float(r["admisiones"])
    salas = float(r["salas_activas"])
    penetracion = None if pd.isna(r["penetracion"]) else float(r["penetracion"])
    clase = r["clase"]
    insat = float(r["demanda_insatisfecha"])
    dist_polo = None if pd.isna(r["dist_polo_km"]) else float(r["dist_polo_km"])
    brecha_tipo = r["brecha_tipo"]
    metodo_tasa = ("promedio ponderado por población excluyendo polos > p"
                   + str(int(PARAMS["winsor_polos_percentil"] * 100)))

    tr = CalculationTrace(f"Cálculo de demanda insatisfecha — {r['municipio']} ({r['departamento']})")
    tr.fuente("Población objetivo (DANE)", f"banda {banda}, año {anio_ref}", f"{pob:,.0f} habitantes")
    tr.paso("1. Población objetivo", f"poblacion_{banda}({anio_ref})", {}, pob, "habitantes")
    tr.paso("2. Tasa de referencia (nacional)", metodo_tasa, {}, tasa_ref, "adm/hab")
    tr.paso("3. Demanda potencial", "potencial = poblacion_objetivo × tasa_ref",
            {"poblacion_objetivo": round(pob), "tasa_ref": tasa_ref}, round(potencial), "espectadores/año")
    tr.paso("4. Admisiones realizadas (SIREC)", "dato observado", {}, round(real), "espectadores/año")
    tr.paso("5. Salas activas (SIREC)", "dato observado", {}, salas, "salas")
    if penetracion is not None:
        tr.paso("6. Penetración", "penetracion = realizadas / potencial",
                {"realizadas": round(real), "potencial": round(potencial)},
                round(penetracion, 3), "ratio")
    tr.paso("7. Clasificación", "según salas y penetración", {}, CLASES[clase])
    formula = {"sin_oferta": "insatisfecha = potencial (no hay oferta local)",
               "subatendido": "insatisfecha = max(0, potencial − realizadas)",
               "saturado": "insatisfecha = 0 (satura / atrae vecinos)"}[clase]
    tr.paso("8. Demanda insatisfecha", formula,
            {"potencial": round(potencial), "realizadas": round(real)}, round(insat),
            "espectadores/año")
    if clase == "sin_oferta" and dist_polo is not None:
        tr.paso("9. Tipo de brecha (distancia al polo)",
                f"si dist_polo ≤ {PARAMS['umbral_conurbacion_km']} km → conurbación (aparente); "
                f"si no → aislamiento (real)",
                {"dist_polo_km": dist_polo}, brecha_tipo, "",
                "Distingue municipios genuinamente aislados de suburbios con un multiplex a minutos.")
    return {
        "cod_mpio": r["cod_mpio"], "municipio": r["municipio"], "departamento": r["departamento"],
        "clase": clase, "etiqueta_clase": CLASES[clase],
        "poblacion_objetivo": pob, "demanda_potencial": potencial,
        "admisiones_realizadas": real, "salas_activas": salas,
        "penetracion": penetracion, "demanda_insatisfecha": insat,
        "dist_polo_km": dist_polo, "brecha_tipo": brecha_tipo,
        "lat": _f(r["lat"]), "lon": _f(r["lon"]),
        "trace": tr.to_dict(),
    }


def _f(v):
    try:
        return None if pd.isna(v) else float(v)
    except Exception:
        return None


def _clean_records(df: pd.DataFrame) -> list[dict]:
    out = df.copy()
    for c in out.columns:
        if out[c].dtype.kind in "fc":
            out[c] = out[c].astype(float)
    return out.where(pd.notna(out), None).to_dict("records")


if __name__ == "__main__":
    import json
    res = compute()
    print("Parametros:", res["parametros"])
    print("\nResumen por clase:")
    for r in res["resumen_por_clase"]:
        print(f"  {r['etiqueta']:34} municipios={r['municipios']:4d}  "
              f"insatisfecha={r['demanda_insatisfecha']:,.0f}")
    print("\nTotales:", {k: round(v) if isinstance(v, float) else v for k, v in res["totales"].items()})
    print("\nTop 8 municipios con demanda insatisfecha:")
    for r in res["top_insatisfecha"][:8]:
        print(f"  {r['municipio']:22} ({r['departamento'][:16]:16}) [{r['clase']:11}] "
              f"insat={r['demanda_insatisfecha']:,.0f}")
