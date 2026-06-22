"""Componente B — Simulador de captura por exhibidor (CatBoost)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from _ui import divipola, load, page

page("Simulador de Exhibidor", icon="🎟️")

st.title("🎟️ Simulador de exhibidor hipotético · 2027")
st.markdown(
    "El **Componente B** (CatBoost) estima cuántos espectadores **captaría un exhibidor** según "
    "el número de salas y las características del municipio. Responde la pregunta: *¿cuántos "
    "espectadores tendría un exhibidor que abra N salas en un municipio dado?*"
)

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "captura_catboost.cbm"
dem = load("proyeccion_demanda_2027.parquet")
dane = load("dane_poblacion.parquet")
if dem is None or dane is None or not MODEL_PATH.exists():
    st.warning("Falta entrenar el modelo. Ejecuta `cinepredict train`.")
    st.stop()


@st.cache_resource
def cargar_modelo():
    from catboost import CatBoostRegressor
    m = CatBoostRegressor()
    m.load_model(str(MODEL_PATH))
    return m


model = cargar_modelo()
div = divipola()
dane27 = dane[dane["anio"] == 2027].set_index("cod_divipola")

c1, c2, c3, c4 = st.columns(4)
with c1:
    depto = st.selectbox("Departamento", sorted(div["departamento"].unique()))
with c2:
    munis = div[div["departamento"] == depto].sort_values("municipio")
    municipio = st.selectbox("Municipio", munis["municipio"].tolist())
with c3:
    n_salas = st.slider("Salas del exhibidor", 1, 20, 4)
with c4:
    exhibidor = st.selectbox("Cadena", ["Cine Colombia", "Cinemark", "Royal Films",
                                         "Procinal", "Cinemateca/Independiente"])

cod = munis[munis["municipio"] == municipio]["cod_divipola"].iloc[0]
fila_dem = dem[dem["cod_divipola"] == cod]
dist = float(fila_dem["dist_km_sala_cercana"].iloc[0]) if not fila_dem.empty else 0.0
if cod in dane27.index:
    pob = float(dane27.loc[cod, "poblacion_15_44"]); prop = float(dane27.loc[cod, "prop_15_44"])
else:
    pob, prop = 0.0, 0.0

# Techo plausible: las admisiones anuales por persona 15–44 rara vez superan ~6
# (incluso en los mercados más activos). Acota la extrapolación fuera de muestra.
TECHO_PER_CAPITA = 6.0


def _predecir(salas: int) -> int:
    X = pd.DataFrame([{
        "num_salas": salas, "poblacion_15_44": pob, "prop_15_44": prop,
        "dist_km_sala_cercana": dist, "exhibidor": exhibidor,
    }])
    p = max(0, int(model.predict(X)[0]))
    if pob > 0:
        p = min(p, int(TECHO_PER_CAPITA * pob))
    return p


pred = _predecir(n_salas)

st.divider()
m1, m2, m3 = st.columns(3)
m1.metric("Espectadores estimados / año", f"{pred:,}")
m2.metric("Población 15–44 (2027)", f"{int(pob):,}")
m3.metric("Distancia a sala más cercana", f"{dist:,.0f} km")

st.markdown("#### Sensibilidad al número de salas")
filas = [{"salas": n, "espectadores": _predecir(n)} for n in range(1, 21)]
st.bar_chart(pd.DataFrame(filas), x="salas", y="espectadores", height=320)
st.caption("Proyección del Componente B (CatBoost) para un exhibidor hipotético. "
           "Permite dimensionar una apuesta de exhibición antes de invertir.")
