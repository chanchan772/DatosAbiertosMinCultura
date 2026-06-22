"""Componente A — Demanda potencial y brecha de acceso (mapa 2027)."""

from __future__ import annotations

import pydeck as pdk
import streamlit as st
from _ui import divipola, load, page

page("Demanda y Brecha", icon="🗺️")

st.title("🗺️ Demanda potencial y brecha de acceso · 2027")
st.markdown(
    "El **Componente A** (regresión LightGBM sobre población 15–44 y accesibilidad) estima la "
    "**demanda potencial** de cada municipio. La diferencia con la asistencia observada revela "
    "la **demanda insatisfecha**: territorios con público pero sin oferta de salas."
)

dem = load("proyeccion_demanda_2027.parquet")
if dem is None:
    st.warning("Falta entrenar el modelo. Ejecuta `cinepredict train`.")
    st.stop()

geo = dem.merge(divipola(), on="cod_divipola", how="left").dropna(subset=["lat", "lon"])

c1, c2, c3 = st.columns(3)
c1.metric("Demanda potencial nacional", f"{dem['demanda_potencial'].sum()/1e6:,.1f} M")
c2.metric("Demanda insatisfecha (sin sala)",
          f"{dem[dem.tiene_cine==0]['brecha'].sum()/1e6:,.1f} M", delta_color="inverse")
c3.metric("Municipios sin sala con demanda", f"{(dem[dem.tiene_cine==0]['brecha']>0).sum()}")

solo_sin = st.toggle("Mostrar solo municipios SIN salas (brecha pura)", value=True)
g = geo[geo["tiene_cine"] == 0] if solo_sin else geo
g = g[g["brecha"] > 0].copy()
g["radio"] = (g["brecha"] ** 0.5) * 30  # escala visual

st.markdown("#### Mapa de la brecha")
st.caption("Cada burbuja es un municipio; su tamaño y color representan la **demanda insatisfecha** "
           "proyectada para 2027. Pasa el cursor para ver el detalle.")
st.pydeck_chart(pdk.Deck(
    map_style="light",
    initial_view_state=pdk.ViewState(latitude=4.6, longitude=-74.3, zoom=4.3),
    layers=[pdk.Layer(
        "ScatterplotLayer", data=g[["municipio", "departamento", "lon", "lat", "brecha", "radio"]],
        get_position="[lon, lat]", get_radius="radio",
        get_fill_color="[230, 80, 60, 150]", pickable=True,
    )],
    tooltip={"text": "{municipio} ({departamento})\nDemanda insatisfecha: {brecha}"},
))

st.markdown("#### Top 15 municipios con mayor demanda insatisfecha (2027)")
top = (g.sort_values("brecha", ascending=False)
       .head(15)[["municipio", "departamento", "poblacion_15_44", "dist_km_sala_cercana", "brecha"]])
top = top.rename(columns={"poblacion_15_44": "población 15-44",
                          "dist_km_sala_cercana": "km a sala más cercana",
                          "brecha": "demanda insatisfecha"})
st.dataframe(top, use_container_width=True, hide_index=True)
st.caption("Estos municipios son candidatos prioritarios para instrumentos de fomento a la "
           "exhibición regional (Ley 814 de 2003).")
