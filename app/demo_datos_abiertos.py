"""CinePredict — Consumo de Datos Abiertos en vivo (datos.gov.co, API SODA).

Página de demostración con contexto y experiencia de usuario: explica qué es el
proyecto, qué contiene cada fuente de datos abiertos, cómo se consume por API y
qué significa cada visualización. Pensada para que un usuario no técnico (o el
jurado del concurso) entienda el valor de un vistazo.

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
    page_title="CinePredict · Datos Abiertos en vivo",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- estilo
st.markdown(
    """
    <style>
      .stApp { background: #faf8f5; }
      h1, h2, h3 { color: #3b2a5a; }
      .hero {
        background: linear-gradient(120deg, #3b2a5a 0%, #5b3fa0 100%);
        color: #fff; padding: 28px 32px; border-radius: 16px; margin-bottom: 8px;
      }
      .hero h1 { color: #fff; margin: 0 0 6px 0; font-size: 2.0rem; }
      .hero p { color: #ecdffb; margin: 0; font-size: 1.02rem; }
      .pill { display:inline-block; background:#ffd97a; color:#5a3d00;
              padding:2px 10px; border-radius:999px; font-size:0.78rem;
              font-weight:600; margin-right:6px; }
      .card { background:#fff; border:1px solid #ece6f5; border-left:5px solid #5b3fa0;
              border-radius:12px; padding:18px 22px; margin:6px 0 14px 0; }
      .src  { color:#7a6a99; font-size:0.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE = "https://www.datos.gov.co"

# Catálogo de fuentes con contexto pensado para el usuario
RECURSOS = {
    "🗺️ DIVIPOLA — Mapa político de Colombia (DANE)": {
        "id": "gdxc-w37w",
        "que_es": (
            "El **catálogo oficial de municipios de Colombia** del DANE. A cada municipio "
            "le asigna un código único de 5 dígitos (DIVIPOLA) y sus coordenadas geográficas."
        ),
        "publica": "DANE — Departamento Administrativo Nacional de Estadística",
        "campos": "código de municipio, nombre, departamento, longitud y latitud",
        "rol": (
            "Es la **llave maestra del proyecto**: con ella unimos todas las fuentes "
            "(cine, población, vías) hablando del *mismo* municipio sin ambigüedad. "
            "Además, sus coordenadas nos sirven como punto central de cada municipio para "
            "calcular **qué tan lejos está la sala de cine más cercana** (accesibilidad)."
        ),
        "viz": "mapa",
        "viz_explica": (
            "Cada punto es **un municipio de Colombia** ubicado con las coordenadas que trae "
            "el propio dataset. Así verificamos que la cobertura es nacional (1.122 municipios) "
            "y que las coordenadas son utilizables para el análisis territorial."
        ),
    },
    "👥 Población y educación por municipio (MinEducación)": {
        "id": "nudc-7mev",
        "que_es": (
            "Estadísticas educativas **por municipio y por año** que incluyen la **población "
            "en edad escolar (5 a 16 años)** estimada a partir de las proyecciones del DANE."
        ),
        "publica": "Ministerio de Educación Nacional (con base en proyecciones DANE)",
        "campos": "año, municipio, departamento, población 5-16, coberturas educativas",
        "rol": (
            "Aporta una **variable demográfica** por municipio (tamaño de la población joven), "
            "que es uno de los factores que explican la **demanda potencial de cine**: a mayor "
            "población en edades de alto consumo, mayor demanda esperada."
        ),
        "viz": "barras",
        "viz_explica": (
            "Mostramos los municipios con **mayor población en edad escolar**. Es un anticipo "
            "de cómo el tamaño poblacional alimenta el modelo de demanda potencial (Componente A)."
        ),
    },
}


def soda_url(dataset_id: str, **params) -> str:
    qs = urllib.parse.urlencode(params)
    return f"{BASE}/resource/{dataset_id}.json" + (f"?{qs}" if qs else "")


def fetch(url: str, retries: int = 4):
    """Llama a la API con reintentos y backoff.

    datos.gov.co a veces responde 500/503 a peticiones anónimas (throttling o
    inestabilidad del portal). Reintentamos antes de rendirnos.
    """
    last_err = None
    for intento in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CinePredict/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 — queremos reintentar ante cualquier fallo de red
            last_err = e
            if intento < retries:
                time.sleep(1.5 * intento)  # backoff: 1.5s, 3s, 4.5s
    raise last_err


# --------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### 🎬 CinePredict")
    st.markdown(
        "Modelo predictivo y **abierto** de espectadores de cine en Colombia, "
        "con proyección a **2027**."
    )
    st.markdown("**Concurso:** Datos al Ecosistema 2026 · Reto 8 (Cultura y Turismo)")
    st.markdown("**Equipo:** DACMI — Ministerio de las Culturas")
    st.divider()
    st.markdown("#### El problema")
    st.markdown(
        "El acceso al cine es **desigual**: las salas se concentran en pocas ciudades. "
        "Queremos medir esa brecha con datos para orientar el fomento regional."
    )
    st.markdown("#### Lo que responde el modelo")
    st.markdown(
        "1. ¿Cuántos espectadores tendría un **exhibidor** en cierto lugar?\n"
        "2. ¿Qué municipios tienen **demanda sin atender**?\n"
        "3. ¿Cómo varía la asistencia **mes a mes**?"
    )
    st.divider()
    st.caption("Esta pantalla demuestra el **consumo de datos abiertos por API**, "
               "uno de los pilares del proyecto.")

# --------------------------------------------------------------------------- hero
st.markdown(
    """
    <div class="hero">
      <h1>🛰️ Datos Abiertos en vivo</h1>
      <p>Así alimentamos el modelo: consumiendo datos públicos directamente desde
      <b>datos.gov.co</b> por su API, de forma transparente y reproducible.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<span class="pill">Gobierno abierto</span>'
    '<span class="pill">Reproducible</span>'
    '<span class="pill">Sin descargas manuales</span>',
    unsafe_allow_html=True,
)

st.markdown("")
st.markdown(
    "> **¿Qué estás viendo en esta página?** No usamos archivos sueltos ni datos "
    "cargados a mano. Cada vez que ejecutas el proceso, el aplicativo **llama en vivo a la "
    "API pública del Estado** y trae la información del momento. Esto le da al jurado y a "
    "cualquier ciudadano la **certeza** de que el modelo se construye sobre datos abiertos, "
    "auditables y actualizables."
)

st.divider()

# --------------------------------------------------------------------------- paso 0
st.markdown("## 📂 Paso 1 · Elige la fuente de datos abiertos")
st.caption("Selecciona un conjunto de datos públicos y abajo verás qué contiene y para qué lo usamos.")

c1, c2 = st.columns([3, 1])
with c1:
    nombre = st.selectbox("Fuente de datos", list(RECURSOS.keys()), label_visibility="collapsed")
with c2:
    limite = st.number_input("Registros a traer", min_value=10, max_value=5000, value=1000, step=50)

r = RECURSOS[nombre]
dataset_id = r["id"]

st.markdown(
    f"""
    <div class="card">
      <div class="src">Fuente · {r['publica']} · datos.gov.co · id <code>{dataset_id}</code></div>
      <p style="margin:.5rem 0;"><b>¿Qué es?</b> {r['que_es']}</p>
      <p style="margin:.5rem 0;"><b>Campos principales:</b> {r['campos']}</p>
      <p style="margin:.5rem 0;"><b>¿Para qué lo usamos en CinePredict?</b> {r['rol']}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- paso 2
st.markdown("## 🔌 Paso 2 · Cómo lo consumimos (API SODA)")
st.markdown(
    "datos.gov.co expone cada conjunto por una **API REST** (estándar Socrata/SODA). "
    "Pedimos primero el *esquema* (qué columnas tiene) y luego los *datos*. "
    "Estas son las direcciones exactas que se van a llamar:"
)
meta_url = f"{BASE}/api/views/{dataset_id}.json"
data_url = soda_url(dataset_id, **{"$limit": limite})
st.code(
    f"# 1) Esquema / metadatos del conjunto\nGET {meta_url}\n\n"
    f"# 2) Datos ({limite} registros) — API SODA\nGET {data_url}",
    language="http",
)

run = st.button("▶️  Consumir la API de datos abiertos ahora", type="primary", use_container_width=True)

# --------------------------------------------------------------------------- ejecución
if run:
    st.markdown("## 📡 Paso 3 · Consumo en vivo")

    desde_cache = False

    # metadatos
    st.markdown("**3.1 · Pedimos el esquema del conjunto** — para saber qué columnas trae.")
    try:
        with st.status("Conectando con la API de metadatos de datos.gov.co…", expanded=True) as s:
            t0 = time.time(); meta = fetch(meta_url); ms_meta = (time.time() - t0) * 1000
            cols = [c["fieldName"] for c in meta.get("columns", [])]
            st.write(f"Conjunto: **{meta.get('name')}**")
            st.write(f"Tiene **{len(cols)} columnas**: {', '.join(cols)}")
            s.update(label=f"Esquema recibido del Estado en {ms_meta:.0f} ms (HTTP 200)", state="complete")
    except Exception:  # noqa: BLE001
        st.warning("⚠️ La API de metadatos no respondió en este intento.")

    # datos
    st.markdown("**3.2 · Traemos los datos** — la respuesta llega en formato JSON, tal cual la entrega el Estado.")
    rows = None
    try:
        with st.status("Descargando registros por API SODA…", expanded=True) as s:
            t0 = time.time(); rows = fetch(data_url); ms_data = (time.time() - t0) * 1000
            s.update(label=f"{len(rows):,} registros descargados en vivo ({ms_data:.0f} ms)", state="complete")
        df = pd.DataFrame.from_records(rows)
    except Exception:  # noqa: BLE001
        # Respaldo: usar la última copia descargada (solo DIVIPOLA está cacheado)
        from pathlib import Path

        cache = Path(__file__).resolve().parents[1] / "data" / "reference" / "divipola.csv"
        if dataset_id == "gdxc-w37w" and cache.exists():
            df = pd.read_csv(cache, dtype=str)
            df = df.rename(columns={"municipio": "nom_mpio", "departamento": "dpto"})
            desde_cache = True
            ms_data = 0
            st.warning(
                "⚠️ **La API del Estado no respondió en este momento** (datos.gov.co a veces "
                "presenta throttling o caídas temporales en peticiones anónimas). Para no "
                "interrumpir la demostración, mostramos la **última copia descargada por API** "
                "(guardada en el repositorio). Vuelve a intentar en unos segundos para ver el "
                "consumo en vivo."
            )
        else:
            st.error(
                "❌ La API de datos.gov.co no respondió tras varios reintentos y no hay copia "
                "local de este conjunto. Es una caída temporal del portal del Estado; "
                "intenta de nuevo en unos segundos."
            )
            st.stop()

    m1, m2, m3 = st.columns(3)
    m1.metric("Registros recibidos", f"{len(df):,}")
    m2.metric("Columnas", f"{df.shape[1]}")
    m3.metric("Origen", "copia local" if desde_cache else f"API en vivo · {ms_data:.0f} ms")

    if rows:
        with st.expander("Ver la respuesta JSON original (primer registro)"):
            st.json(rows[0])

    st.markdown("**3.3 · Datos ya cargados en el pipeline del proyecto**")
    st.caption("Esta es la tabla con la que trabaja el modelo. Puedes descargarla.")
    st.dataframe(df.head(200), use_container_width=True, height=280)
    st.download_button(
        "⬇️ Descargar estos datos (CSV)", df.to_csv(index=False).encode("utf-8"),
        file_name=f"{dataset_id}.csv", mime="text/csv",
    )

    # visualización con explicación
    st.markdown("## 🗺️ Paso 4 · Qué nos dicen estos datos")
    st.info(r["viz_explica"])

    tiene_coords = r["viz"] == "mapa" and (
        {"longitud", "latitud"}.issubset(df.columns) or {"lon", "lat"}.issubset(df.columns)
    )
    if tiene_coords:
        import pydeck as pdk

        geo = df.copy()
        if "longitud" in geo.columns:  # datos en vivo: coma decimal
            geo["lon"] = geo["longitud"].str.replace(",", ".", regex=False).astype(float)
            geo["lat"] = geo["latitud"].str.replace(",", ".", regex=False).astype(float)
        else:  # copia local: ya numérico
            geo["lon"] = pd.to_numeric(geo["lon"], errors="coerce")
            geo["lat"] = pd.to_numeric(geo["lat"], errors="coerce")
        geo = geo.dropna(subset=["lon", "lat"])
        cols_top = [c for c in ["nom_mpio", "dpto"] if c in geo.columns]
        st.pydeck_chart(
            pdk.Deck(
                map_style="light",
                initial_view_state=pdk.ViewState(latitude=4.6, longitude=-74.3, zoom=4.3),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=geo[cols_top + ["lon", "lat"]],
                        get_position="[lon, lat]",
                        get_radius=7000,
                        get_fill_color=[91, 63, 160, 150],
                        pickable=True,
                    )
                ],
                tooltip={"text": "{nom_mpio} — {dpto}"},
            )
        )
        st.caption(f"🟣 {len(geo):,} municipios georreferenciados · pasa el cursor sobre un punto para ver su nombre.")

    elif r["viz"] == "barras" and "poblaci_n_5_16" in df.columns:
        d = df.copy()
        d["poblaci_n_5_16"] = pd.to_numeric(d["poblaci_n_5_16"], errors="coerce")
        if "a_o" in d.columns:
            ult = d["a_o"].max()
            d = d[d["a_o"] == ult]
            st.caption(f"Año más reciente disponible: **{ult}**")
        top = (d.groupby("municipio", as_index=False)["poblaci_n_5_16"]
                 .sum().sort_values("poblaci_n_5_16", ascending=False).head(15))
        st.bar_chart(top, x="municipio", y="poblaci_n_5_16", height=380)
        st.caption("Población en edad escolar (5-16 años) — 15 municipios más poblados.")

    st.success(
        "✅ Listo. Acabas de ver el ciclo completo: **API del Estado → esquema → datos → "
        "tabla del modelo → visualización**, todo en vivo y sin intervención manual."
    )
else:
    st.info("👆 Cuando estés listo, pulsa **Consumir la API de datos abiertos ahora** "
            "para ver, paso a paso, cómo el aplicativo trae los datos públicos.")
