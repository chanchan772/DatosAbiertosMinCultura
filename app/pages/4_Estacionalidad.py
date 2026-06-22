"""Componente C — Estacionalidad, tendencia y efecto COVID (series de tiempo)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from _ui import divipola, load, page

page("Estacionalidad", icon="📈")

st.title("📈 Estacionalidad y proyección mensual")
st.markdown(
    "El **Componente C** (StatsForecast AutoARIMA por municipio + Prophet nacional) modela la "
    "**estacionalidad** (vacaciones, festivos) y la **tendencia**, incorporando el **quiebre "
    "2020–2021 por COVID-19** como intervención. Permite desagregar la proyección mes a mes."
)

serie = load("series_mensuales.parquet")
nac = load("proyeccion_nacional_prophet.parquet")
muni = load("proyeccion_mensual.parquet")
if serie is None or muni is None:
    st.warning("Falta entrenar el modelo. Ejecuta `cinepredict train`.")
    st.stop()

serie["ds"] = pd.PeriodIndex(serie["periodo"], freq="M").to_timestamp()

# ---- Serie nacional con intervención COVID ----
st.markdown("### Serie nacional: histórico, proyección y efecto COVID")
hist_nac = serie.groupby("ds", as_index=False)["espectadores"].sum()
fig = go.Figure()
fig.add_trace(go.Scatter(x=hist_nac["ds"], y=hist_nac["espectadores"],
                         name="Histórico (SIREC)", line=dict(color="#3b2a5a", width=2)))
if nac is not None:
    fut = nac[nac["ds"] > hist_nac["ds"].max()]
    fig.add_trace(go.Scatter(x=fut["ds"], y=fut["yhat"], name="Proyección (Prophet)",
                             line=dict(color="#8a5ed6", width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=list(fut["ds"]) + list(fut["ds"][::-1]),
                             y=list(fut["yhat_upper"]) + list(fut["yhat_lower"][::-1]),
                             fill="toself", fillcolor="rgba(138,94,214,0.15)",
                             line=dict(color="rgba(0,0,0,0)"), name="Intervalo", showlegend=False))
fig.add_vrect(x0="2020-03-01", x1="2021-12-31", fillcolor="rgba(230,80,60,0.12)",
              line_width=0, annotation_text="Quiebre COVID", annotation_position="top left")
fig.update_layout(height=420, margin=dict(t=30, b=0, l=0, r=0), plot_bgcolor="white",
                  legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig, use_container_width=True)
st.caption("La franja roja marca el cierre de salas 2020–2021, modelado como variable de "
           "intervención para que no contamine la tendencia proyectada.")

# ---- Serie municipal ----
st.markdown("### Proyección mensual por municipio")
div = divipola()
muni = muni.rename(columns={"unique_id": "cod_divipola"})
muni["cod_divipola"] = muni["cod_divipola"].astype(str).str.zfill(5)
con_serie = sorted(serie["cod_divipola"].unique())
opciones = div[div["cod_divipola"].isin(con_serie)].sort_values("municipio")
sel = st.selectbox("Municipio", opciones["municipio"].tolist())
cod = opciones[opciones["municipio"] == sel]["cod_divipola"].iloc[0]

h = serie[serie["cod_divipola"] == cod]
f = muni[muni["cod_divipola"] == cod]
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=h["ds"], y=h["espectadores"], name="Histórico",
                          line=dict(color="#3b2a5a")))
fig2.add_trace(go.Scatter(x=f["ds"], y=f["espectadores_pred"], name="Proyección a 2027",
                          line=dict(color="#8a5ed6", dash="dash")))
fig2.update_layout(height=380, margin=dict(t=20, b=0, l=0, r=0), plot_bgcolor="white",
                   legend=dict(orientation="h", y=1.12))
st.plotly_chart(fig2, use_container_width=True)
st.caption(f"Asistencia mensual observada y proyectada para {sel}.")
