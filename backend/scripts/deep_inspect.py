"""
deep_inspect.py — Inspeccion profunda de las hojas clave.
Vuelca contenido real (agregado / diccionarios) para diseñar el pipeline.
"""
from __future__ import annotations
import warnings
from pathlib import Path
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", 40)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 40)

ROOT = Path(__file__).resolve().parents[2]
DATOS = ROOT / "Datos"


def banner(t):
    print("\n" + "=" * 90 + f"\n{t}\n" + "=" * 90)


# ---------------------------------------------------------------- TAQUILLA (core)
banner("TAQUILLA 2026-Colarco :: hoja 'Base' (dataset transaccional central)")
tq = pd.read_excel(DATOS / "Taquilla 2026-Colarco.xlsx", sheet_name="Base")
print("shape:", tq.shape)
print("\ndtypes:\n", tq.dtypes)
# normaliza nombre de columnas para conveniencia
tq.columns = [c.strip() for c in tq.columns]
fecha_col = [c for c in tq.columns if "Fecha Exhib" in c][0]
tq[fecha_col] = pd.to_datetime(tq[fecha_col], errors="coerce")
print("\nRango fechas exhibicion:", tq[fecha_col].min(), "->", tq[fecha_col].max())
print("Años reporte:", sorted(tq["Año Reporte"].dropna().unique().tolist()))
adm_col = [c for c in tq.columns if c.lower().startswith("admis")][0]
print("Total admisiones:", int(tq[adm_col].sum()))
print("N exhibidores unicos:", tq["ID EXHIBIDOR"].nunique(), "| N complejos:", tq["ID COMPLEJO"].nunique(),
      "| N salas:", tq["ID SALA"].nunique())
print("N titulos:", tq["TITULO"].nunique())
print("N departamentos:", tq["COMPL Departamento"].nunique(), "| N municipios:", tq["COMPL Municipio"].nunique())
print("\nTop 10 exhibidores por admisiones:")
print(tq.groupby("EXHIBIDOR")[adm_col].sum().sort_values(ascending=False).head(10))
print("\nTop 12 municipios por admisiones:")
print(tq.groupby(["COMPL Departamento", "COMPL Municipio"])[adm_col].sum().sort_values(ascending=False).head(12))
print("\nGeneros:", tq["TITULO Genero"].dropna().unique().tolist()[:20])
print("\nClasificaciones:", tq["TITULO Clasificación"].dropna().unique().tolist()[:20])
print("\nNacionalidad (col TITULO Nacion):", tq["TITULO Nacion"].dropna().unique().tolist()[:20])
print("Catalogo/Estreno:", tq["Catalogo/Estreno"].dropna().unique().tolist())
print("DiaSemana:", tq["DiaSemana"].dropna().unique().tolist())
print("\nAdmisiones por año-reporte:")
print(tq.groupby("Año Reporte")[adm_col].sum())

# ---------------------------------------------------------------- ESPECTADORES POR DIA
banner("Datos abiertos :: 'Espectadores por dia' (serie temporal diaria)")
esp = pd.read_excel(DATOS / "Datos abiertos.xlsx", sheet_name="Espectadores por dia")
esp["FECHA"] = pd.to_datetime(esp["FECHA"], errors="coerce")
print("shape:", esp.shape, "| rango:", esp["FECHA"].min(), "->", esp["FECHA"].max())
print(esp["ASISTENCIA"].describe())
print("\nprimeras filas:\n", esp.head())
print("\nasistencia anual:")
print(esp.assign(y=esp["FECHA"].dt.year).groupby("y")["ASISTENCIA"].sum())

# ---------------------------------------------------------------- DICCIONARIOS
for fname in ["Datos abiertos.xlsx", "HISTORICO Estrenos Total.xlsx", "HISTORICO Estrenos Colombia.xlsx"]:
    try:
        xl = pd.ExcelFile(DATOS / fname)
        if "Diccionario de datos" in xl.sheet_names:
            banner(f"{fname} :: Diccionario de datos")
            dd = xl.parse("Diccionario de datos")
            print(dd.to_string())
    except Exception as e:
        print(f"[X] {fname} diccionario: {e}")

# ---------------------------------------------------------------- SALAS (re-parse con header)
banner("Salas de Cine Registradas y Activas :: deteccion de encabezado real")
for sheet in ["Base Datos", "Por Exhibidor", "Por Ubicación", "AdmisionesXmunicipio"]:
    try:
        raw = pd.read_excel(DATOS / "Salas de Cine Registradas y Activas.xlsx", sheet_name=sheet, header=None)
        print(f"\n--- hoja '{sheet}' primeras 6 filas crudas ---")
        print(raw.head(6).to_string())
    except Exception as e:
        print(f"[X] {sheet}: {e}")
