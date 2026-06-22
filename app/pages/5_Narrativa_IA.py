"""Narrativa automática con la API de Claude — apropiación por tomadores de decisión."""

from __future__ import annotations

import streamlit as st
from _ui import divipola, load, page

page("Narrativa IA", icon="📝")

st.title("📝 Narrativa automática con IA")
st.markdown(
    "La **API de Claude (Anthropic)** está embebida para traducir las proyecciones de cada "
    "territorio a **lenguaje claro**, facilitando que tomadores de decisión sin perfil técnico "
    "se apropien de los resultados."
)

dem = load("proyeccion_demanda_2027.parquet")
if dem is None:
    st.warning("Falta entrenar el modelo. Ejecuta `cinepredict train`.")
    st.stop()

div = divipola()
g = dem.merge(div, on="cod_divipola", how="left")
depto = st.selectbox("Departamento", sorted(g["departamento"].dropna().unique()))
sub = g[g["departamento"] == depto]

# Resumen estructurado que alimenta a la IA
con_cine = int((sub["tiene_cine"] == 1).sum())
sin_cine = int((sub["tiene_cine"] == 0).sum())
brecha_total = int(sub[sub["tiene_cine"] == 0]["brecha"].sum())
top = (sub[sub["tiene_cine"] == 0].sort_values("brecha", ascending=False)
       .head(5)[["municipio", "brecha"]])

c1, c2, c3 = st.columns(3)
c1.metric("Municipios con sala", con_cine)
c2.metric("Municipios sin sala", sin_cine)
c3.metric("Demanda insatisfecha 2027", f"{brecha_total:,}")

resumen = (
    f"Departamento: {depto}. Municipios con salas de cine: {con_cine}. Municipios sin salas: "
    f"{sin_cine}. Demanda insatisfecha total proyectada a 2027: {brecha_total:,} espectadores. "
    f"Municipios con mayor demanda insatisfecha: "
    + ", ".join(f"{m} ({int(b):,})" for m, b in zip(top['municipio'], top['brecha'])) + "."
)
with st.expander("Datos que se envían a la IA"):
    st.code(resumen)

if st.button("✨ Generar narrativa con Claude", type="primary"):
    with st.spinner("Generando narrativa…"):
        try:
            from cinepredict.viz.narrative import narrar_proyeccion
            texto = narrar_proyeccion(resumen)
        except Exception as e:  # noqa: BLE001
            texto = f"(No se pudo generar la narrativa: {e})"
    st.markdown(f'<div class="card">{texto}</div>', unsafe_allow_html=True)
    st.caption("Generado por la API de Claude a partir de las proyecciones del modelo. "
               "Configura ANTHROPIC_API_KEY en .env para habilitarlo.")
