"""Consumo de Datos Abiertos en vivo — datos.gov.co (API SODA / Socrata)."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

import pandas as pd
import streamlit as st
from _ui import page

page("Datos Abiertos en vivo", icon="🛰️")

BASE = "https://www.datos.gov.co"
RECURSOS = {
    "🗺️ DIVIPOLA (DANE)": {
        "id": "gdxc-w37w",
        "registros": "1.122 municipios", "categoria": "Mapas Nacionales", "actualizado": "dic 2024",
        "oficial": "Código de la División Político-Administrativa del país. Corte 30 dic 2024.",
        "que_es": "Catálogo oficial de municipios de Colombia: código único de 5 dígitos (DIVIPOLA) "
                  "y coordenadas de cada uno.",
        "rol": "Llave maestra que une todas las fuentes y aporta los centros de cada municipio "
               "para medir accesibilidad.",
        "mapa": True,
    },
    "👥 Población / Educación (MinEducación)": {
        "id": "nudc-7mev",
        "registros": "15.707 registros", "categoria": "Educación", "actualizado": "2024",
        "oficial": "Indicadores educativos por municipio (2011–2024); coberturas calculadas con "
                   "proyecciones de población del Censo 2018.",
        "que_es": "Estadísticas educativas por municipio y año, incluida la población en edad "
                  "escolar (ejemplo adicional de consumo por API).",
        "rol": "Ejemplo complementario de consumo por API. La demografía del modelo usa la "
               "proyección por edad del DANE (franja 15–44).",
        "mapa": False,
    },
}


def fetch(url: str, retries: int = 4):
    last = None
    for i in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CinePredict/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            last = e
            if i < retries:
                time.sleep(1.5 * i)
    raise last


st.markdown(
    """
    <div class="hero"><h1>🛰️ Datos Abiertos en vivo</h1>
    <p>Así alimentamos el modelo: consumiendo datos públicos directamente desde
    <b>datos.gov.co</b> por su API, de forma transparente y reproducible.</p></div>
    """, unsafe_allow_html=True)
st.markdown('<span class="pill">Gobierno abierto</span><span class="pill">Reproducible</span>'
            '<span class="pill">Sin descargas manuales</span>', unsafe_allow_html=True)
st.markdown("")
st.markdown("> Cada vez que ejecutas el proceso, el aplicativo **llama en vivo a la API pública "
            "del Estado**: así tienes certeza de que el modelo se construye sobre datos abiertos "
            "y auditables.")

st.markdown("### 📂 Elige la fuente de datos abiertos")
try:
    nombre = st.segmented_control("Fuente", list(RECURSOS), default=list(RECURSOS)[0],
                                  label_visibility="collapsed")
except Exception:  # noqa: BLE001
    nombre = st.radio("Fuente", list(RECURSOS), horizontal=True, label_visibility="collapsed")
nombre = nombre or list(RECURSOS)[0]
r = RECURSOS[nombre]
ds = r["id"]

a, b, c = st.columns(3)
a.metric("Categoría", r["categoria"]); b.metric("Volumen", r["registros"].split(" ")[0])
c.metric("Actualizado", r["actualizado"])
st.markdown(f'<div class="card"><div style="color:#8a7aa8;font-size:.82rem">📡 datos.gov.co · '
            f'id <code>{ds}</code></div><p><b>¿Qué es?</b> {r["que_es"]}</p>'
            f'<p><b>Descripción oficial:</b> <i>{r["oficial"]}</i></p>'
            f'<p><b>Uso en CinePredict:</b> {r["rol"]}</p></div>', unsafe_allow_html=True)

meta_url = f"{BASE}/api/views/{ds}.json"
data_url = f"{BASE}/resource/{ds}.json?" + urllib.parse.urlencode({"$limit": 60000})
st.markdown("### 🔌 Endpoints (API SODA)")
st.code(f"GET {meta_url}\nGET {data_url}", language="http")

if st.button("Consumir la API de datos abiertos ahora", type="primary",
             use_container_width=True, icon=":material/bolt:"):
    with st.status("Consultando metadatos…", expanded=True) as s:
        t0 = time.time(); meta = fetch(meta_url); ms = (time.time()-t0)*1000
        cols = [c["fieldName"] for c in meta.get("columns", [])]
        st.write(f"**{meta.get('name')}** — {len(cols)} columnas")
        s.update(label=f"Esquema recibido ({ms:.0f} ms · HTTP 200)", state="complete")
    with st.status("Descargando datos…", expanded=True) as s:
        t0 = time.time(); rows = fetch(data_url); ms = (time.time()-t0)*1000
        s.update(label=f"{len(rows):,} registros descargados en vivo ({ms:.0f} ms)", state="complete")
    df = pd.DataFrame.from_records(rows)
    st.dataframe(df.head(200), use_container_width=True, height=280)

    if r["mapa"] and {"longitud", "latitud"}.issubset(df.columns):
        import pydeck as pdk
        df["lon"] = df["longitud"].str.replace(",", ".", regex=False).astype(float)
        df["lat"] = df["latitud"].str.replace(",", ".", regex=False).astype(float)
        df = df.dropna(subset=["lon", "lat"])
        st.markdown("#### 🗺️ Los municipios consumidos, en el mapa")
        st.pydeck_chart(pdk.Deck(map_style="light",
            initial_view_state=pdk.ViewState(latitude=4.6, longitude=-74.3, zoom=4.3),
            layers=[pdk.Layer("ScatterplotLayer", data=df[["nom_mpio", "dpto", "lon", "lat"]],
                              get_position="[lon, lat]", get_radius=7000,
                              get_fill_color="[106,72,189,150]", pickable=True)],
            tooltip={"text": "{nom_mpio} — {dpto}"}))
        st.caption(f"🟣 {len(df):,} municipios georreferenciados con las coordenadas del dataset.")
    st.success("Ciclo completo: API del Estado → esquema → datos → tabla → mapa, en vivo.")
