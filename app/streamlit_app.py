"""CinePredict — Tablero principal (Inicio).

Ejecutar:  streamlit run app/streamlit_app.py
Tablero multipágina: ver el menú lateral (Datos Abiertos, Demanda y Brecha,
Simulador de Exhibidor, Estacionalidad).
"""

from __future__ import annotations

import streamlit as st
from _ui import divipola, load, page

page("Inicio", icon="🎬")

st.markdown(
    """
    <div class="hero">
      <h1>🎬 CinePredict</h1>
      <p>Modelo predictivo y abierto de espectadores de cine en Colombia, con
      proyección a 2027, para medir y cerrar la brecha de acceso cultural.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<span class="pill">Datos abiertos</span><span class="pill">IA explicable</span>'
    '<span class="pill">Código abierto</span>',
    unsafe_allow_html=True,
)

st.markdown("")
st.markdown(
    "> **El problema (Reto 8 · Cultura y Turismo).** La infraestructura de salas de cine "
    "se concentra en pocas ciudades, generando una distribución inequitativa del acceso "
    "cinematográfico. CinePredict modela ese fenómeno con datos abiertos para orientar el "
    "fomento a la exhibición regional (Ley 814 de 2003)."
)

# --- KPIs ---
demanda = load("proyeccion_demanda_2027.parquet")
analytic = load("analytic.parquet")
dane = load("dane_poblacion.parquet")

st.markdown("### 📊 Panorama")
c1, c2, c3, c4 = st.columns(4)
if analytic is not None:
    con_cine = analytic.loc[analytic["num_salas"] > 0, "cod_divipola"].nunique()
    total_mpios = dane["cod_divipola"].nunique() if dane is not None else 1122
    c1.metric("Municipios con salas", f"{con_cine}", f"{100*con_cine/total_mpios:.0f}% del país")
    c2.metric("Municipios SIN salas", f"{total_mpios - con_cine}",
              "brecha de acceso", delta_color="inverse")
if demanda is not None:
    c3.metric("Demanda potencial 2027", f"{demanda['demanda_potencial'].sum()/1e6:,.1f} M")
    sin = demanda[demanda["tiene_cine"] == 0]["brecha"].sum()
    c4.metric("Demanda insatisfecha 2027", f"{sin/1e6:,.1f} M", "en municipios sin sala",
              delta_color="inverse")

st.divider()
st.markdown("### 🧭 ¿Qué responde el modelo? (usa el menú lateral)")
q1, q2, q3 = st.columns(3)
q1.markdown(
    '<div class="card"><b>1 · Demanda y brecha</b><p>¿Qué municipios tienen demanda '
    "potencial sin oferta de salas? Mapa de la brecha 2027.</p></div>", unsafe_allow_html=True)
q2.markdown(
    '<div class="card"><b>2 · Simulador de exhibidor</b><p>¿Cuántos espectadores captaría '
    "un exhibidor con N salas en un municipio dado?</p></div>", unsafe_allow_html=True)
q3.markdown(
    '<div class="card"><b>3 · Estacionalidad</b><p>¿Cómo se desagrega mes a mes la '
    "asistencia, con el efecto del quiebre COVID?</p></div>", unsafe_allow_html=True)

if demanda is None:
    st.warning("Aún no hay modelos entrenados. Ejecuta el pipeline:\n\n"
               "```\ncinepredict download --source divipola\ncinepredict download --source dane\n"
               "cinepredict synth\ncinepredict clean\ncinepredict features\ncinepredict train\n```")

st.caption("Fuentes: SIREC (exhibición) · DANE (DIVIPOLA + proyecciones de población) · "
           "consumidas como datos abiertos. Modelo: LightGBM · CatBoost · StatsForecast/Prophet.")
