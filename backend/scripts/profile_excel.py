"""
profile_excel.py
Perfilado exhaustivo de los archivos Excel crudos de la carpeta Datos/.
Objetivo: entender estructura (hojas, columnas, tipos, nulos, cardinalidad,
rangos temporales, muestras) SIN exponer datos sensibles en claro.

Salida:
  - backend/data/interim/profile_report.json  (estructura completa, legible por maquina)
  - stdout: resumen legible por humano

Uso: python backend/scripts/profile_excel.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATOS = ROOT / "Datos"
OUT = ROOT / "backend" / "data" / "interim"
OUT.mkdir(parents=True, exist_ok=True)


def summarize_column(s: pd.Series) -> dict:
    n = len(s)
    nn = int(s.notna().sum())
    nulls = n - nn
    nunique = int(s.nunique(dropna=True))
    info = {
        "dtype": str(s.dtype),
        "non_null": nn,
        "nulls": nulls,
        "pct_null": round(100 * nulls / n, 2) if n else None,
        "nunique": nunique,
        "cardinality_ratio": round(nunique / nn, 4) if nn else None,
    }
    # muestra de valores (top frecuentes), truncando strings largos
    try:
        vc = s.dropna().value_counts().head(8)
        info["top_values"] = [
            {"value": (str(k)[:60]), "count": int(v)} for k, v in vc.items()
        ]
    except Exception as e:
        info["top_values_error"] = str(e)

    # rango numerico
    if pd.api.types.is_numeric_dtype(s):
        desc = s.describe()
        info["numeric"] = {
            k: (float(desc[k]) if k in desc else None)
            for k in ["min", "25%", "50%", "75%", "max", "mean", "std"]
        }
    # rango fecha
    if pd.api.types.is_datetime64_any_dtype(s):
        info["date_range"] = {
            "min": str(s.min()),
            "max": str(s.max()),
        }
    return info


def profile_file(path: Path) -> dict:
    xls = pd.ExcelFile(path)
    file_info = {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "sheets": {},
    }
    for sheet in xls.sheet_names:
        try:
            df = xls.parse(sheet)
        except Exception as e:
            file_info["sheets"][sheet] = {"error": str(e)}
            continue
        # intento de deteccion de header desplazado: si muchas columnas 'Unnamed'
        unnamed = sum(1 for c in df.columns if str(c).startswith("Unnamed"))
        sheet_info = {
            "rows": int(df.shape[0]),
            "cols": int(df.shape[1]),
            "unnamed_cols": unnamed,
            "columns": list(map(str, df.columns)),
            "column_profiles": {},
        }
        for c in df.columns:
            sheet_info["column_profiles"][str(c)] = summarize_column(df[c])
        # muestra de 3 primeras filas (valores truncados)
        head = df.head(3).astype(str)
        sheet_info["head_sample"] = [
            {col: (str(row[col])[:50]) for col in df.columns}
            for _, row in head.iterrows()
        ]
        file_info["sheets"][sheet] = sheet_info
    return file_info


def main():
    if not DATOS.exists():
        print(f"ERROR: no existe {DATOS}", file=sys.stderr)
        sys.exit(1)
    files = sorted(DATOS.glob("*.xlsx"))
    report = {"root": str(ROOT), "n_files": len(files), "files": []}
    for f in files:
        print(f"Perfilando: {f.name} ...", flush=True)
        try:
            report["files"].append(profile_file(f))
        except Exception as e:
            report["files"].append({"file": f.name, "error": str(e)})
            print(f"  ERROR: {e}", file=sys.stderr)

    out_path = OUT / "profile_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReporte JSON: {out_path}")

    # resumen humano
    print("\n" + "=" * 78)
    print("RESUMEN LEGIBLE")
    print("=" * 78)
    for fi in report["files"]:
        if "error" in fi:
            print(f"\n[X] {fi['file']}: {fi['error']}")
            continue
        print(f"\n### {fi['file']}  ({fi['size_bytes']:,} bytes)")
        for sheet, si in fi["sheets"].items():
            if "error" in si:
                print(f"  - hoja '{sheet}': ERROR {si['error']}")
                continue
            print(f"  - hoja '{sheet}': {si['rows']:,} filas x {si['cols']} cols "
                  f"(unnamed={si['unnamed_cols']})")
            print(f"      columnas: {si['columns']}")


if __name__ == "__main__":
    main()
