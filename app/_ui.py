"""Componentes de interfaz compartidos por las páginas del tablero CinePredict."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
REFERENCE = Path(__file__).resolve().parents[1] / "data" / "reference"
FIGURES = Path(__file__).resolve().parents[1] / "reports" / "figures"

_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap');
  html, body, [class*="st-"], .stApp, p, span, label, li, div, input, button, select {
    font-family: 'Inter', system-ui, sans-serif !important;
  }
  h1, h2, h3, h4 { font-family: 'Sora','Inter',sans-serif !important; color:#2e2150 !important;
                   letter-spacing:-0.015em; }
  .stApp, [data-testid="stAppViewContainer"] { background:#faf8f5; }
  [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color:#2b2440; }
  [data-testid="stSidebar"] { background:linear-gradient(180deg,#2a1d47,#3b2a5a) !important; }
  [data-testid="stSidebar"] * { color:#ece7f6 !important; }
  [data-testid="stSidebar"] hr { border-color:#5a4880 !important; }
  .hero { background:linear-gradient(120deg,#3b2a5a,#6a48bd); color:#fff;
          padding:28px 32px; border-radius:18px; box-shadow:0 8px 30px rgba(59,42,90,.18); }
  .hero h1 { color:#fff !important; margin:0 0 6px 0; }
  .hero p { color:#ece0fb !important; margin:0; font-size:1.04rem; }
  .pill { display:inline-block; background:#ffd36b; color:#5a3d00; padding:4px 13px;
          border-radius:999px; font-size:.8rem; font-weight:600; margin-right:7px; }
  .card { background:#fff; border:1px solid #eadff7; border-left:5px solid #6a48bd;
          border-radius:14px; padding:18px 22px; margin:6px 0 14px 0;
          box-shadow:0 2px 10px rgba(60,40,100,.05); }
  .card p { color:#2b2440 !important; line-height:1.55; }
  [data-testid="stMarkdownContainer"] blockquote { background:#f3eefc; border-left:4px solid #6a48bd;
          border-radius:10px; padding:12px 18px; color:#3a3357 !important; }
  .stButton > button[kind="primary"] { background:linear-gradient(120deg,#6a48bd,#8a5ed6);
          border:0; font-weight:600; border-radius:12px; }
</style>
"""


def page(title: str, icon: str = "🎬") -> None:
    """Configuración común de página: layout, estilo y barra lateral."""
    st.set_page_config(page_title=f"CinePredict · {title}", page_icon=icon, layout="wide",
                       initial_sidebar_state="expanded")
    st.markdown(_CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### 🎬 CinePredict")
        st.markdown("Modelo predictivo y **abierto** de espectadores de cine en Colombia · "
                    "horizonte **2027**.")
        st.markdown("**Reto 8** · Cultura y Turismo")
        st.markdown("**Equipo:** DACMI — Ministerio de las Culturas")
        st.divider()
        st.caption("Datos al Ecosistema 2026 · IA para Colombia")


@st.cache_data
def load(name: str) -> pd.DataFrame | None:
    p = PROCESSED / name
    return pd.read_parquet(p) if p.exists() else None


@st.cache_data
def divipola() -> pd.DataFrame:
    df = pd.read_csv(REFERENCE / "divipola.csv", dtype={"cod_divipola": str})
    df["cod_divipola"] = df["cod_divipola"].str.zfill(5)
    return df
