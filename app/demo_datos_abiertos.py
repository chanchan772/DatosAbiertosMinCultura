"""Demo de CONSUMO DE DATOS ABIERTOS EN VIVO — datos.gov.co (API SODA / Socrata).

Página autocontenida (solo stdlib + streamlit + pandas + pydeck) pensada para
*ver* el proceso: la URL que se llama, la respuesta cruda, los datos cargados y
un mapa de los municipios. Da certeza visual de que el proyecto consume datos
abiertos por API.

Ejecutar:
    streamlit run app/demo_datos_abiertos.py
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="CinePredict · Consumo de Datos Abiertos en vivo",
    page_icon="🛰️",
    layout="wide",
)

BASE = "https://www.datos.gov.co"

# Catálogo de recursos verificados en datos.gov.co (API SODA)
RECURSOS = {
    "DIVIPOLA — Códigos de municipios (DANE)": {
        "id": "gdxc-w37w",
        "descripcion": "Llave territorial canónica (5 dígitos) + coordenadas de cada municipio.",
        "tiene_mapa": True,
    },
    "Estadísticas en educación por municipio (MEN) — incluye población": {
        "id": "nudc-7mev",
        "descripcion": "Población escolar (5-16) y coberturas por municipio y año, nacional.",
        "tiene_mapa": False,
    },
}


def soda_url(dataset_id: str, **params) -> str:
    """Construye la URL del endpoint SODA con parámetros SoQL."""
    qs = urllib.parse.urlencode(params)
    return f"{BASE}/resource/{dataset_id}.json" + (f"?{qs}" if qs else "")


def fetch(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "CinePredict/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


# ----------------------------------------------------------------------------- UI
st.title("🛰️ Consumo de Datos Abiertos en vivo")
st.caption(
    "CinePredict · Reto 8 Cultura y Turismo · Fuente: **datos.gov.co** (API SODA / Socrata). "
    "Cada paso de abajo ejecuta una llamada real a la API pública."
)

col_sel, col_n = st.columns([3, 1])
with col_sel:
    nombre = st.selectbox("Recurso de datos abiertos", list(RECURSOS.keys()))
with col_n:
    limite = st.number_input("Filas a traer", min_value=10, max_value=5000, value=1000, step=50)

recurso = RECURSOS[nombre]
dataset_id = recurso["id"]
st.info(recurso["descripcion"])

meta_url = f"{BASE}/api/views/{dataset_id}.json"
data_url = soda_url(dataset_id, **{"$limit": limite})

st.markdown("### 1️⃣ Endpoints que se van a consumir")
st.code(f"# Metadatos (esquema del dataset)\nGET {meta_url}\n\n# Datos (API SODA)\nGET {data_url}", language="http")

if st.button("▶️ Ejecutar consumo de la API", type="primary"):
    # Paso 2: metadatos
    st.markdown("### 2️⃣ Metadatos del recurso")
    with st.status("Llamando a la API de metadatos…", expanded=True) as status:
        t0 = time.time()
        meta = fetch(meta_url)
        ms = (time.time() - t0) * 1000
        cols = [c["fieldName"] for c in meta.get("columns", [])]
        st.write(f"**Nombre:** {meta.get('name')}")
        st.write(f"**Columnas ({len(cols)}):** {', '.join(cols)}")
        st.write(f"⏱️ Respuesta en {ms:.0f} ms · HTTP 200")
        status.update(label=f"Metadatos recibidos ({ms:.0f} ms)", state="complete")

    # Paso 3: datos
    st.markdown("### 3️⃣ Datos crudos (respuesta JSON de la API)")
    with st.status("Descargando datos por API SODA…", expanded=True) as status:
        t0 = time.time()
        rows = fetch(data_url)
        ms = (time.time() - t0) * 1000
        st.write(f"✅ **{len(rows):,} filas** recibidas en {ms:.0f} ms")
        st.json(rows[0], expanded=False)
        status.update(label=f"{len(rows):,} filas descargadas ({ms:.0f} ms)", state="complete")

    df = pd.DataFrame.from_records(rows)

    # Paso 4: tabla
    st.markdown("### 4️⃣ Datos cargados en el pipeline")
    st.dataframe(df.head(200), use_container_width=True, height=300)
    st.download_button(
        "⬇️ Descargar CSV", df.to_csv(index=False).encode("utf-8"),
        file_name=f"{dataset_id}.csv", mime="text/csv",
    )

    # Paso 5: mapa (si aplica)
    if recurso["tiene_mapa"] and {"longitud", "latitud"}.issubset(df.columns):
        st.markdown("### 5️⃣ Visualización territorial (coordenadas del propio dataset)")
        import pydeck as pdk

        geo = df.copy()
        geo["lon"] = geo["longitud"].str.replace(",", ".", regex=False).astype(float)
        geo["lat"] = geo["latitud"].str.replace(",", ".", regex=False).astype(float)
        geo = geo.dropna(subset=["lon", "lat"])
        st.write(f"🗺️ {len(geo):,} municipios georreferenciados")
        st.pydeck_chart(
            pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(latitude=4.6, longitude=-74.1, zoom=4.2),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=geo,
                        get_position="[lon, lat]",
                        get_radius=6000,
                        get_fill_color=[200, 30, 80, 140],
                        pickable=True,
                    )
                ],
                tooltip={"text": "{nom_mpio} ({dpto})"},
            )
        )

    st.success(
        "Consumo de datos abiertos verificado de extremo a extremo: "
        "metadatos → datos por API → carga → visualización."
    )
else:
    st.warning("Pulsa **▶️ Ejecutar consumo de la API** para ver el proceso en vivo.")
