"""
main.py — API FastAPI de CinePredict.

Expone panorama nacional, catálogo de datos, demanda insatisfecha (con mapa y
drill-down por municipio), estacionalidad/proyección 2027, simulador de exhibidor
y narrativas DeepSeek. CADA respuesta analítica incluye su traza de cálculo
(campo 'trace') para el panel de transparencia del tablero.

Ejecutar:  uvicorn backend.app.main:app --reload --port 8000
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models import overview, demand, forecast, exhibitor, catalog
from .models.methodology import PARAMS, METODOLOGIA
from .models.data import municipal_panel
from .services.deepseek import generar_narrativa
from .services import nlquery

app = FastAPI(title="CinePredict API", version="1.0",
              description="Modelo predictivo de espectadores de cine — Reto 8 (SIREC + DANE)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Saneador JSON (numpy / NaN -> nativo) para evitar errores de serialización
# --------------------------------------------------------------------------- #
def sanitize(obj):
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    return {"status": "ok", "servicio": "CinePredict", "version": "1.0"}


@app.get("/api/methodology")
def methodology():
    return sanitize({"parametros": PARAMS, "metodologia": METODOLOGIA})


@lru_cache(maxsize=1)
def _catalog_cached():
    return sanitize(catalog.compute())


@app.get("/api/catalog")
def get_catalog():
    return _catalog_cached()


@lru_cache(maxsize=1)
def _overview_cached():
    return sanitize(overview.compute())


@app.get("/api/overview")
def get_overview():
    return _overview_cached()


@lru_cache(maxsize=16)
def _demand_cached(anio: int, banda: str):
    return sanitize(demand.compute(anio, banda))


@app.get("/api/demand")
def get_demand(anio: int = Query(PARAMS["anio_referencia_demanda"]),
               banda: str = Query(PARAMS["banda_objetivo_default"])):
    return _demand_cached(anio, banda)


@lru_cache(maxsize=16)
def _map_cached(anio: int, banda: str):
    return sanitize({"anio": anio, "banda": banda, "municipios": demand.geo_table(anio, banda)})


@app.get("/api/demand/map")
def get_demand_map(anio: int = Query(PARAMS["anio_referencia_demanda"]),
                   banda: str = Query(PARAMS["banda_objetivo_default"])):
    return _map_cached(anio, banda)


@app.get("/api/demand/municipio/{cod_mpio}")
def get_municipio(cod_mpio: str,
                  anio: int = Query(PARAMS["anio_referencia_demanda"]),
                  banda: str = Query(PARAMS["banda_objetivo_default"])):
    return sanitize(demand.municipio_detail(cod_mpio, anio, banda))


@lru_cache(maxsize=4)
def _forecast_cached(anio: int):
    return sanitize(forecast.compute(anio))


@app.get("/api/forecast")
def get_forecast(anio: int = Query(PARAMS["anio_proyeccion"])):
    return _forecast_cached(anio)


@lru_cache(maxsize=1)
def _municipios_list():
    panel = municipal_panel(PARAMS["anio_referencia_demanda"], PARAMS["banda_objetivo_default"])
    sub = panel[panel["poblacion_objetivo"].notna()][
        ["cod_mpio", "municipio", "departamento", "salas_activas", "poblacion_objetivo"]
    ].sort_values("municipio")
    return sanitize(sub.to_dict("records"))


@app.get("/api/municipios")
def get_municipios():
    return _municipios_list()


class SimRequest(BaseModel):
    cod_mpio: str
    n_salas: int = 3
    banda: str = PARAMS["banda_objetivo_default"]
    anio: int = PARAMS["anio_referencia_demanda"]


@app.post("/api/simulate")
def post_simulate(req: SimRequest):
    return sanitize(exhibitor.simulate(req.cod_mpio, req.n_salas, req.anio, req.banda))


class NarrativeRequest(BaseModel):
    tipo: str = "territorio"     # territorio | nacional | simulacion
    contexto: dict


@app.post("/api/narrative")
def post_narrative(req: NarrativeRequest):
    return sanitize(generar_narrativa(req.contexto, req.tipo))


class QueryRequest(BaseModel):
    pregunta: str
    banda: str = PARAMS["banda_objetivo_default"]


@app.post("/api/query")
def post_query(req: QueryRequest):
    """Consulta en lenguaje natural sobre los datos (DeepSeek, contexto curado)."""
    return sanitize(nlquery.answer(req.pregunta, banda=req.banda))


@app.get("/api/query/context")
def get_query_context(banda: str = Query(PARAMS["banda_objetivo_default"])):
    """Contexto curado de datos (para consultas cliente en modo estático)."""
    return sanitize(nlquery.build_context(banda))


class InterpretRequest(BaseModel):
    modulo: str
    datos: dict


@app.post("/api/interpret")
def post_interpret(req: InterpretRequest):
    """Interpretación larga y accesible de los datos de un módulo (DeepSeek)."""
    return sanitize(nlquery.interpret_module(req.modulo, req.datos))


@app.get("/")
def root():
    return {"servicio": "CinePredict API", "docs": "/docs",
            "endpoints": ["/api/overview", "/api/demand", "/api/demand/map",
                          "/api/forecast", "/api/simulate", "/api/catalog",
                          "/api/methodology", "/api/narrative"]}
