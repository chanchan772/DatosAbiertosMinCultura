"""
overview.py — Panorama nacional (KPIs y distribuciones) desde el detalle SIREC.

Alimenta el módulo "Panorama nacional" del tablero. Todo sale de tablas
pseudonimizadas; los exhibidores se muestran por token (EXH-xxxx) con un rango.
"""
from __future__ import annotations

import pandas as pd

from .data import load
from ..config import TAQUILLA_ANIO, TAQUILLA_CORTE


def _dist(df: pd.DataFrame, col: str, valor="admisiones") -> list[dict]:
    g = df.groupby(col, as_index=False)[valor].sum().sort_values(valor, ascending=False)
    total = g[valor].sum()
    return [{"categoria": str(k), "admisiones": int(v), "pct": round(100 * v / total, 2)}
            for k, v in zip(g[col], g[valor])]


def compute() -> dict:
    tq = load("fact_taquilla")
    serie = load("serie_diaria_nacional")

    total_adm = int(tq["admisiones"].sum())
    kpis = {
        "anio": TAQUILLA_ANIO,
        "corte": TAQUILLA_CORTE,
        "admisiones_total": total_adm,
        "exhibidores": int(tq["exhibidor_tok"].nunique()),
        "complejos": int(tq["complejo_tok"].nunique()),
        "salas": int(tq["id_sala"].nunique()),
        "municipios": int(tq["municipio"].nunique()),
        "departamentos": int(tq["departamento"].nunique()),
        "titulos": int(tq["titulo"].nunique()),
    }

    # Concentración (indicadores de inequidad territorial/empresarial)
    por_muni = tq.groupby("municipio")["admisiones"].sum().sort_values(ascending=False)
    por_exh = tq.groupby("exhibidor_tok")["admisiones"].sum().sort_values(ascending=False)
    concentracion = {
        "top1_municipio_pct": round(100 * por_muni.iloc[0] / total_adm, 1),
        "top5_municipios_pct": round(100 * por_muni.head(5).sum() / total_adm, 1),
        "top3_exhibidores_pct": round(100 * por_exh.head(3).sum() / total_adm, 1),
    }

    # Top exhibidores (anonimizados, con rango) y municipios
    top_exh = [{"rank": i + 1, "exhibidor": tok, "admisiones": int(v)}
               for i, (tok, v) in enumerate(por_exh.head(10).items())]
    muni_geo = tq.groupby(["departamento", "municipio"])["admisiones"].sum().reset_index()
    top_muni = [{"rank": i + 1, "municipio": r.municipio, "departamento": r.departamento,
                 "admisiones": int(r.admisiones)}
                for i, r in enumerate(muni_geo.nlargest(12, "admisiones").itertuples())]

    # Admisiones mensuales 2026
    mensual = tq.groupby("mes", as_index=False)["admisiones"].sum()
    mensual = [{"mes": int(r.mes), "admisiones": int(r.admisiones)} for r in mensual.itertuples()]

    # Serie anual histórica
    serie_anual = serie.groupby("anio", as_index=False)["asistencia"].sum()
    serie_anual = [{"anio": int(r.anio), "asistencia": int(r.asistencia)}
                   for r in serie_anual.itertuples()]

    return {
        "kpis": kpis,
        "concentracion": concentracion,
        "top_exhibidores": top_exh,
        "top_municipios": top_muni,
        "admisiones_mensual": mensual,
        "serie_anual": serie_anual,
        "por_genero": _dist(tq, "genero"),
        "por_clasificacion": _dist(tq, "clasificacion"),
        "por_nacion": _dist(tq, "nacion"),
        "por_dia_semana": _dist(tq, "dia_semana"),
        "por_catalogo_estreno": _dist(tq, "catalogo_estreno"),
    }


if __name__ == "__main__":
    import json
    r = compute()
    print(json.dumps(r["kpis"], ensure_ascii=False, indent=2))
    print("Concentración:", r["concentracion"])
    print("Top 3 exhibidores:", [(e["exhibidor"], e["admisiones"]) for e in r["top_exhibidores"][:3]])
    print("Por nación:", r["por_nacion"])
    print("Por género:", [(g["categoria"], g["pct"]) for g in r["por_genero"]])
