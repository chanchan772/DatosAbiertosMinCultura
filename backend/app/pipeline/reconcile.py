"""
reconcile.py — Reconciliacion territorial contra codigo DIVIPOLA (DANE).

Toma los pares (departamento, municipio) presentes en las tablas SIREC y les
asigna el codigo DIVIPOLA de 5 digitos, mas lat/lon oficiales. El emparejamiento
se hace DENTRO de cada departamento para evitar colisiones entre municipios
homonimos (p.ej. hay varios "La Union"). Se produce ademas un reporte de calidad
que el tablero muestra para dar transparencia sobre la cobertura de la union.

Salida:
  data/processed/crosswalk_municipios.parquet
  data/interim/reconcile_report.json
"""
from __future__ import annotations

import json

import pandas as pd

from ..config import DATA_PROCESSED, DATA_INTERIM
from .external import fetch_divipola
from .text_utils import norm_text, best_match, ALIAS_DEPARTAMENTOS


def _dep_lookup(divi: pd.DataFrame) -> dict[str, str]:
    """{departamento_norm: cod_dpto} para DIVIPOLA."""
    out = {}
    for _, r in divi[["cod_dpto", "departamento"]].drop_duplicates().iterrows():
        out[norm_text(r["departamento"])] = r["cod_dpto"]
    return out


def _mpios_by_dep(divi: pd.DataFrame) -> dict[str, dict[str, str]]:
    """{cod_dpto: {municipio_norm: cod_mpio}}"""
    out: dict[str, dict[str, str]] = {}
    for _, r in divi.iterrows():
        out.setdefault(r["cod_dpto"], {})[norm_text(r["municipio"])] = r["cod_mpio"]
    return out


def _match_departamento(dep_src: str, dep_lut: dict[str, str]) -> str | None:
    n = norm_text(dep_src)
    if n in ALIAS_DEPARTAMENTOS:
        n = ALIAS_DEPARTAMENTOS[n]
    if n in dep_lut:
        return dep_lut[n]
    # aproximado
    val, score, _ = best_match(dep_src, dep_lut, threshold=0.82)
    return val


def build_crosswalk() -> pd.DataFrame:
    divi = fetch_divipola()
    dep_lut = _dep_lookup(divi)
    mpios = _mpios_by_dep(divi)
    geo = divi.set_index("cod_mpio")[["municipio", "departamento", "lat", "lon"]].to_dict("index")

    # pares unicos (departamento, municipio) de todas las tablas SIREC
    pairs = set()
    for tbl in ["fact_taquilla", "admisiones_municipio_anual", "dim_complejos"]:
        path = DATA_PROCESSED / f"{tbl}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=None)
        if "departamento" in df.columns and "municipio" in df.columns:
            for d, m in df[["departamento", "municipio"]].drop_duplicates().itertuples(index=False):
                pairs.add((str(d), str(m)))

    rows = []
    for dep_src, mpio_src in sorted(pairs):
        cod_dpto = _match_departamento(dep_src, dep_lut)
        cod_mpio, score, metodo = None, 0.0, "sin_departamento"
        if cod_dpto and cod_dpto in mpios:
            cod_mpio, score, metodo = best_match(mpio_src, mpios[cod_dpto], threshold=0.84)
        g = geo.get(cod_mpio, {})
        rows.append({
            "departamento_src": dep_src,
            "municipio_src": mpio_src,
            "cod_dpto": cod_dpto,
            "cod_mpio": cod_mpio,
            "municipio_divipola": g.get("municipio"),
            "departamento_divipola": g.get("departamento"),
            "lat": g.get("lat"),
            "lon": g.get("lon"),
            "score": score,
            "metodo": metodo,
        })
    cw = pd.DataFrame(rows)
    cw.to_parquet(DATA_PROCESSED / "crosswalk_municipios.parquet", index=False)

    matched = int(cw["cod_mpio"].notna().sum())
    report = {
        "pares_totales": int(len(cw)),
        "emparejados": matched,
        "sin_emparejar": int(len(cw) - matched),
        "cobertura_pct": round(100 * matched / len(cw), 2) if len(cw) else 0,
        "por_metodo": cw["metodo"].apply(lambda m: m.split("~")[0]).value_counts().to_dict(),
        "no_emparejados_detalle": cw[cw["cod_mpio"].isna()][
            ["departamento_src", "municipio_src", "score", "metodo"]
        ].to_dict("records"),
    }
    (DATA_INTERIM / "reconcile_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return cw, report


if __name__ == "__main__":
    cw, rep = build_crosswalk()
    print(f"Pares: {rep['pares_totales']} | emparejados: {rep['emparejados']} "
          f"({rep['cobertura_pct']}%)")
    print("Por metodo:", rep["por_metodo"])
    if rep["no_emparejados_detalle"]:
        print("\nNO emparejados (revisar):")
        for x in rep["no_emparejados_detalle"][:30]:
            print(f"  - {x['departamento_src']} / {x['municipio_src']}  (score {x['score']}, {x['metodo']})")
