"""Narrativa automática con la API de Claude — apropiación por tomadores de decisión."""

from __future__ import annotations

import streamlit as st
from _ui import divipola, load, page

page("Narrativa IA", icon="📝")

st.title("📝 Narrativa automática con IA")
st.markdown(
    "Traduce las proyecciones de cada territorio a **lenguaje claro** para tomadores de "
    "decisión. Funciona con la **API de Claude** o cualquier proveedor compatible (Groq, "
    "Gemini, Ollama…); si no hay clave configurada, usa un **resumen por plantilla sin costo**."
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

contexto = {
    "departamento": depto, "con_cine": con_cine, "sin_cine": sin_cine,
    "brecha_total": brecha_total,
    "top": list(zip(top["municipio"], top["brecha"])),
}
with st.expander("Datos que alimentan la narrativa"):
    st.json(contexto)

if st.button("✨ Generar narrativa", type="primary"):
    with st.spinner("Generando narrativa…"):
        import re
        from cinepredict.viz.narrative import narrar_territorio
        texto, fuente = narrar_territorio(contexto)
    # Convertir negritas Markdown a HTML para que se rendericen dentro de la tarjeta
    texto_html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    st.markdown(f'<div class="card">{texto_html}</div>', unsafe_allow_html=True)
    icono = "🤖" if fuente != "plantilla (sin costo)" else "🧩"
    st.caption(f"{icono} Generado por: **{fuente}** · a partir de las proyecciones del modelo.")
    if fuente == "plantilla (sin costo)":
        st.info("ℹ️ Modo sin costo (plantilla determinística). Para narrativa con IA "
                "generativa, configura `ANTHROPIC_API_KEY` o un proveedor compatible "
                "(`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL`) en `.env`.")
