"""
forecast.py — Estacionalidad, tendencia y proyección 2027 (serie nacional).

Descomposición clásica multiplicativa sobre la serie mensual de asistencia:
    serie ≈ tendencia × factor_estacional
La tendencia se ajusta por regresión lineal sobre los años COMPLETOS post-COVID
(2022–2025), excluyendo 2020–2021 (cierre de salas) y 2026 (año parcial). Los
factores estacionales se estiman como el promedio mensual relativo de esos mismos
años. Todo el procedimiento es aritmético y auditable (sin caja negra).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import load
from .methodology import PARAMS, METODOLOGIA
from .trace import CalculationTrace

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
ANIO_TREND_INI = 2022  # primer año completo post-COVID usado para tendencia/estacionalidad


def _serie_mensual() -> pd.DataFrame:
    s = load("serie_diaria_nacional")
    m = s.groupby(["anio", "mes"], as_index=False)["asistencia"].sum()
    return m


def _anios_completos(m: pd.DataFrame) -> list[int]:
    """Años con los 12 meses presentes (excluye 2026 parcial)."""
    cont = m.groupby("anio")["mes"].nunique()
    return sorted([int(a) for a, n in cont.items() if n == 12])


def compute(anio_proy: int | None = None) -> dict:
    anio_proy = anio_proy or PARAMS["anio_proyeccion"]
    m = _serie_mensual()
    completos = _anios_completos(m)
    covid = set(PARAMS["anios_covid"])
    base_anios = [a for a in completos if ANIO_TREND_INI <= a and a not in covid]

    tr = CalculationTrace(
        "Estacionalidad y proyección de asistencia nacional",
        f"Proyección a {anio_proy} por descomposición clásica multiplicativa.",
    )
    tr.fuente("Serie diaria nacional", "SIREC — 'Espectadores por día' (Datos abiertos.xlsx)",
              "2007–2026, agregada a total mensual.")
    for s in METODOLOGIA["estacionalidad_proyeccion"]["supuestos"]:
        tr.supuesto(s)
    for l in METODOLOGIA["estacionalidad_proyeccion"]["limitaciones"]:
        tr.limitacion(l)

    # Totales anuales
    anual = m.groupby("anio", as_index=False)["asistencia"].sum()
    serie_anual = anual.set_index("anio")["asistencia"]

    def linfit(anios):
        xs = np.array(anios, dtype=float)
        ys = serie_anual.loc[anios].to_numpy(dtype=float)
        slope, intercept = np.polyfit(xs, ys, 1)
        pred = slope * xs + intercept
        ss_res = float(((ys - pred) ** 2).sum())
        ss_tot = float(((ys - ys.mean()) ** 2).sum())
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return float(slope), float(intercept), r2

    # Años normalizados = completos y >= 2023 (recuperacion ya agotada; 2022 se
    # trata como año de recuperacion, no proyectable como tendencia).
    anio_norm_ini = PARAMS["anio_normalizacion_post_covid"]  # 2023
    anios_norm = [a for a in base_anios if a >= anio_norm_ini]
    tr.paso("1. Años usados",
            f"años completos post-COVID: base {base_anios}; normalizados (>= {anio_norm_ini}) "
            f"{anios_norm}. 2022 se marca como recuperacion (no proyectable como tendencia).",
            {}, anios_norm)

    # ESCENARIOS de proyeccion (no un unico punto):
    #  - base: nivel estable = promedio de años normalizados (2023-2025).
    #  - conservador: extrapolacion lineal SOLO con años normalizados.
    #  - optimista: extrapolacion lineal incluyendo 2022 (recuperacion).
    base_nivel = float(serie_anual.loc[anios_norm].mean())
    s_c, i_c, r2_c = linfit(anios_norm)
    s_o, i_o, r2_o = linfit(base_anios)
    proy_conservador = float(s_c * anio_proy + i_c)
    proy_optimista = float(s_o * anio_proy + i_o)
    tendencia_proy = base_nivel  # el valor CENTRAL usado para la proyeccion mensual
    lo = min(proy_conservador, proy_optimista, base_nivel)
    hi = max(proy_conservador, proy_optimista, base_nivel)
    tr.paso("2. Proyeccion central y escenarios",
            "central = promedio(años normalizados) ; conservador/optimista = regresion lineal "
            "(sin/con 2022). Se reporta un RANGO, no un punto.",
            {"base_nivel": round(base_nivel),
             "conservador_sin_2022": round(proy_conservador),
             "optimista_con_2022": round(proy_optimista),
             "R2_con_2022": round(r2_o, 3)},
            round(tendencia_proy), "espectadores/año",
            "El escenario optimista depende del año de recuperacion 2022; su R2 bajo indica "
            "ajuste debil sobre 4 puntos.")

    # Backtest walk-forward: ajustar 2022-2024, predecir 2025, medir error.
    backtest = None
    if all(a in serie_anual.index for a in (2022, 2023, 2024, 2025)):
        s_b, i_b, _ = linfit([2022, 2023, 2024])
        pred_2025 = s_b * 2025 + i_b
        real_2025 = float(serie_anual.loc[2025])
        err = abs(pred_2025 - real_2025) / real_2025
        backtest = {"predicho_2025": round(pred_2025), "real_2025": round(real_2025),
                    "error_pct": round(100 * err, 1)}
        tr.paso("3. Validacion (backtest walk-forward)",
                "ajustar 2022-2024 -> predecir 2025 -> comparar con el real",
                {"predicho_2025": round(pred_2025), "real_2025": round(real_2025)},
                f"{round(100*err,1)}% error", "error a 1 año")

    # Factores estacionales (promedio del share mensual relativo en base_anios)
    mb = m[m["anio"].isin(base_anios)].copy()
    piv = mb.pivot_table(index="anio", columns="mes", values="asistencia", aggfunc="sum")
    media_mensual_por_anio = piv.mean(axis=1)          # promedio mensual de cada año
    factores = (piv.div(media_mensual_por_anio, axis=0)).mean(axis=0)  # factor por mes
    factores = factores / factores.mean()              # normaliza a media 1
    factores_d = {int(k): round(float(v), 4) for k, v in factores.items()}
    tr.paso("4. Factores estacionales por mes",
            "factor(mes) = promedio_años( asistencia(mes) / asistencia_media_mensual(año) ), "
            "normalizado a media 1",
            {}, factores_d, "índice (1 = mes promedio)")

    # Proyección mensual (usa el valor CENTRAL = nivel estable)
    base_mensual = tendencia_proy / 12.0
    proy = []
    for mes in range(1, 13):
        f = float(factores.get(mes, 1.0))
        val = base_mensual * f
        proy.append({"mes": mes, "mes_nombre": MESES[mes - 1],
                     "factor_estacional": round(f, 4),
                     "asistencia_proyectada": round(val)})
    tr.paso("5. Proyección mensual (escenario central)",
            f"proyección({anio_proy}, mes) = (central_{anio_proy} / 12) × factor(mes)",
            {"central_anual": round(tendencia_proy), "base_mensual": round(base_mensual)},
            round(tendencia_proy), "espectadores/año")

    # Serie historica anual para el grafico (todos los años)
    hist = [{"anio": int(r.anio), "asistencia": int(r.asistencia),
             "es_covid": int(r.anio) in covid,
             "completo": int(r.anio) in completos}
            for r in anual.itertuples()]

    return {
        "anio_proyeccion": anio_proy,
        "tendencia_anual_proyectada": round(tendencia_proy),   # central = nivel estable
        "anios_base_tendencia": anios_norm,
        "pendiente_anual": round(s_c),                          # pendiente de años normalizados
        "escenarios": {
            "central_nivel_estable": round(base_nivel),
            "conservador_sin_2022": round(proy_conservador),
            "optimista_con_2022": round(proy_optimista),
        },
        "intervalo": {"bajo": round(lo), "alto": round(hi)},
        "backtest": backtest,
        "r2_ajuste_con_2022": round(r2_o, 3),
        "nota_2022": "2022 es un año de recuperacion post-COVID; incluirlo en la tendencia "
                     "genera una pendiente positiva que la serie estable 2023-2025 no respalda. "
                     "Por eso la proyeccion se reporta como rango.",
        "factores_estacionales": [
            {"mes": mm, "mes_nombre": MESES[mm - 1], "factor": factores_d.get(mm, 1.0)}
            for mm in range(1, 13)
        ],
        "proyeccion_mensual": proy,
        "historico_anual": hist,
        "trace": tr.to_dict(),
    }


if __name__ == "__main__":
    r = compute()
    print(f"Proyección {r['anio_proyeccion']}: {r['tendencia_anual_proyectada']:,} espectadores/año "
          f"(pendiente {r['pendiente_anual']:,}/año)")
    print("Años base tendencia:", r["anios_base_tendencia"])
    print("\nFactores estacionales:")
    for f in r["factores_estacionales"]:
        bar = "#" * int(f["factor"] * 20)
        print(f"  {f['mes_nombre']}: {f['factor']:.3f} {bar}")
    print("\nProyección mensual 2027 (miles):")
    for p in r["proyeccion_mensual"]:
        print(f"  {p['mes_nombre']}: {p['asistencia_proyectada']/1000:,.0f}")
