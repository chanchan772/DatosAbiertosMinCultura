"""Tablero CinePredict — consulta de proyecciones de espectadores de cine.

Ejecutar:  streamlit run app/streamlit_app.py

Permite consultar por departamento, municipio y perfil de exhibidor, ver la
desagregación mensual y obtener una narrativa automática del territorio.
Tiene una vista espejo en Power BI para la apropiación institucional.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from cinepredict.config import PROCESSED_DIR

st.set_page_config(
    page_title="CinePredict · Espectadores de cine en Colombia",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 CinePredict — Proyección de espectadores de cine en Colombia")
st.caption(
    "Concurso Datos al Ecosistema 2026 · Reto 8 Cultura y Turismo · "
    "DACMI — Ministerio de las Culturas · Fuentes: SIREC + DANE"
)


@st.cache_data
def load_analytic() -> pd.DataFrame | None:
    path = PROCESSED_DIR / "analytic.parquet"
    if not path.exists():
        return None
    return pd.read_parquet(path)


df = load_analytic()

if df is None:
    st.warning(
        "Aún no hay datos procesados. Ejecuta el pipeline:\n\n"
        "```\ncinepredict download\ncinepredict clean\ncinepredict train\n```"
    )
    st.stop()

col1, col2, col3 = st.columns(3)
with col1:
    depto = st.selectbox("Departamento", sorted(df["departamento"].dropna().unique()))
with col2:
    munis = df.loc[df["departamento"] == depto, "municipio"].dropna().unique()
    municipio = st.selectbox("Municipio", sorted(munis))
with col3:
    salas = st.number_input("Salas del exhibidor (hipotético)", min_value=1, value=4)

sub = df[(df["departamento"] == depto) & (df["municipio"] == municipio)]

st.subheader(f"Asistencia histórica — {municipio} ({depto})")
if not sub.empty:
    serie = sub.groupby("periodo", as_index=False)["espectadores"].sum()
    st.line_chart(serie, x="periodo", y="espectadores")
else:
    st.info("Sin registros para la selección.")

st.divider()
st.subheader("📝 Narrativa automática")
if st.button("Generar resumen con IA"):
    from cinepredict.viz.narrative import narrar_proyeccion

    resumen = (
        f"Municipio {municipio} ({depto}). "
        f"Total histórico de espectadores: {int(sub['espectadores'].sum()):,}. "
        f"Exhibidor hipotético con {salas} salas."
    )
    st.write(narrar_proyeccion(resumen))
