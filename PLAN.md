# 📋 PLAN DE TRABAJO — CinePredict

> **Documento vivo de seguimiento.** Se actualiza a medida que avanza el proyecto.
> Última actualización: **2026-06-22** (verificación de fuentes vía API SODA)

**Proyecto:** Modelo predictivo de espectadores de cine en Colombia (horizonte 2027)
**Concurso:** Datos al Ecosistema 2026 — **Reto 8: Cultura y Turismo**
**Equipo:** Grupo de Producción y Gestión de la Información — DACMI, Ministerio de las Culturas
**Final presencial:** primera semana de agosto 2026 (GovCamps)
**Repositorio:** https://github.com/chanchan772/DatosAbiertosMinCultura

---

## 🎯 Estado global

| Fase | Descripción | Estado | Avance |
|------|-------------|--------|--------|
| **0** | Scaffold del repositorio | ✅ Completo | 100% |
| **1** | Integración y limpieza de datos | ✅ Pipeline E2E sobre SIREC sintético + DANE/DIVIPOLA reales | 90% |
| **2** | Modelado predictivo (A·B·C) | ✅ A/B/C entrenados, proyección 2027, MLflow/Optuna/SHAP | 90% |
| **3** | Visualización e interfaz | ✅ Tablero multipágina + narrativa Claude + vista Power BI | 95% |

> **Pendiente real para el 100%:** reemplazar el SIREC sintético por el SIREC real del
> equipo y reentrenar; afinar accesibilidad con OSMnx por subregión.

### 🧪 Resultados de la corrida end-to-end (datos sintéticos)
- **Fase 1:** 130.514 filas SIREC sintético → 14.688 filas en `analytic.parquet` (121 municipios con sala, 10,8% — concentración realista).
- **Componente A (LightGBM):** R²≈0.99 · demanda potencial nacional 2027 ≈ 76 M · demanda insatisfecha (municipios sin sala) ≈ 44 M.
- **Componente B (CatBoost):** R²≈0.97 · simulador de exhibidor con techo per cápita.
- **Componente C (StatsForecast + Prophet):** 121 series municipales, horizonte 36 meses, intervención COVID.
- **Stack instalado y verificado** en entorno Python 3.12 (uv): 27/28 librerías de la propuesta importan (incluye torch/neuralforecast, statsforecast, prophet, geopandas, osmnx). Tests: 6/6 ✅.

Leyenda: ✅ completo · 🟡 en curso · ⬜ pendiente · 🔴 bloqueado

---

## 🧩 Las 3 preguntas que el modelo debe responder

1. **Proyección por exhibidor** → ¿cuántos espectadores captaría un exhibidor hipotético dado nº de salas y ubicación? *(Componente B)*
2. **Demanda insatisfecha** → ¿qué municipios tienen demanda potencial sin oferta? *(Componente A)*
3. **Estacionalidad** → ¿cómo se desagrega mes a mes la proyección? *(Componente C)*

---

## 📦 FASE 0 — Scaffold del repositorio ✅

Estructura del proyecto, empaquetado, contenedor, documentación y control de versiones.

**Tecnología:** `git` + `GitHub`, `pyproject.toml` (hatchling, Python 3.12), `Docker`,
`MkDocs Material`, `Makefile`, `pydantic-settings`, `typer` (CLI), `loguru`.

**Hecho:**
- [x] Paquete `src/cinepredict` con CLI (`cinepredict download/clean/train/report`).
- [x] Configuración central y por entorno (`config.py`, `.env.example`, `conf/params.yaml`).
- [x] Dockerfile + docker-compose para el tablero.
- [x] Documentación base en MkDocs (fuentes, modelo de datos, arquitectura).
- [x] Tests que corren sin datos. `.gitignore`/`.gitattributes`.
- [x] Primer commit subido a `origin/main`.

---

## 📥 FASE 1 — Integración y limpieza de datos 🟡

**Objetivo:** normalizar todas las fuentes a la unidad de análisis
`sala × municipio × período` y dejar una tabla analítica validada.

### Tecnología por paso
| Paso | Herramienta | Archivo |
|------|-------------|---------|
| Descarga datos abiertos | `sodapy` (API Socrata) → Parquet | `data/download.py` |
| Consulta/agregación masiva | `DuckDB` sobre Parquet | `data/clean.py` |
| Manipulación de dataframes | `Polars` / `pandas` | (transversal) |
| Reconciliación territorial | normalización + merge a `DIVIPOLA` | `data/territorial.py` |
| Validación de esquema | `Pandera` | `data/schemas.py` |
| Validación de calidad | `Great Expectations` | `validation/` |
| Exploración automática | `ydata-profiling` | (notebook) |
| Geoprocesamiento | `GeoPandas`, `Shapely`, `H3` | `features/` |

### Hecho
- [x] Cliente Socrata con paginación → Parquet.
- [x] Esquemas Pandera (crudo SIREC y tabla analítica).
- [x] Reconciliación DIVIPOLA con normalización de texto (tildes/mayúsculas).
- [x] Plantilla de limpieza con DuckDB.

### Falta
- [ ] **IDs reales de dataset** de SIREC y DANE en `.env` (identificador 4×4 de datos.gov.co).
- [ ] Descargar SIREC real e **inspeccionar columnas** → ajustar la consulta de `clean.py`.
- [ ] Conseguir y cargar `data/reference/divipola.csv` (DANE / MGN).
- [ ] Tratamiento explícito del **quiebre COVID 2020-2021** en la serie.
- [ ] Suites de Great Expectations (rangos, nulos, unicidad de la llave).
- [ ] Descargar fuentes complementarias (DANE población, INVIAS, DNP-MDM, MGN).

### 🤖 IA en esta fase
- **Asistencia al desarrollo** (Claude Code / GitHub Copilot): construir los pipelines
  de limpieza y los esquemas de validación más rápido.

---

## 🧠 FASE 2 — Modelado predictivo 🟡

**Objetivo:** arquitectura híbrida de 3 componentes que responde las 3 preguntas del reto.

### Componentes del modelo
| Comp. | Qué estima | Técnica | Herramienta | Archivo |
|-------|-----------|---------|-------------|---------|
| **A** | Demanda potencial municipal | Regresión sobre demografía + accesibilidad | `LightGBM` | `models/demand.py` |
| **B** | Captura por exhibidor (nº salas × territorio) | Boosting con categóricas de alta cardinalidad | `CatBoost` | `models/capture.py` |
| **C** | Estacionalidad y tendencia (mensual) | Series de tiempo + intervención COVID | `StatsForecast` (SARIMAX/AutoARIMA), `Prophet` baseline, `NeuralForecast`/TFT (avanzado) | `models/seasonality.py` |

### Tecnología de soporte
| Función | Herramienta |
|---------|-------------|
| Optimización de hiperparámetros | `Optuna` |
| Trazabilidad de experimentos | `MLflow` |
| Explicabilidad / auditabilidad | `SHAP` |
| Validación cruzada temporal | `scikit-learn`, `sktime` |

### Hecho
- [x] Estructura de los 3 componentes (firmas, features candidatas).
- [x] Variable de intervención COVID parametrizada.
- [x] Conversión a formato largo Nixtla (`unique_id, ds, y`) para series.
- [x] Orquestación con registro en MLflow (componente C operativo de extremo a extremo).

### Falta
- [ ] Ensamblar **features demográficas** (DANE) y de **accesibilidad** (OSMnx) y unirlas a la tabla analítica.
- [ ] Entrenar y evaluar componentes A y B con datos reales.
- [ ] Definir esquema de **validación temporal** (sin fuga de datos del futuro).
- [ ] Optimización con Optuna + registro de métricas en MLflow.
- [ ] Explicabilidad con SHAP por componente.
- [ ] Ensamble final: A × B × C → proyección 2027 desagregada.
- [ ] Métricas objetivo (MAE/MAPE) y baseline vs. modelo avanzado.

### 🤖 IA en esta fase
- **El modelo predictivo en sí** (LightGBM/CatBoost/series de tiempo/TFT) es el núcleo de IA.
- **SHAP** garantiza que las predicciones sean **auditables y comunicables** al sector.
- **Asistencia al desarrollo** (Claude Code / Copilot) para feature engineering.

---

## 📊 FASE 3 — Visualización e interfaz 🟡

**Objetivo:** tablero interactivo de consulta por departamento, municipio y perfil de
exhibidor, con vista espejo en Power BI para apropiación institucional.

### Tecnología por componente
| Componente | Herramienta | Archivo |
|------------|-------------|---------|
| Tablero principal | `Streamlit` (desplegado en Docker) | `app/streamlit_app.py` |
| Mapas | `PyDeck`, `Folium` | `viz/` |
| Gráficos interactivos | `Plotly` | `viz/` |
| Narrativa automática | **API de Claude (Anthropic)** | `viz/narrative.py` |
| Capa institucional espejo | `Power BI` | (externo) |
| Consultas en lenguaje natural | `Vanna.ai` / `PandasAI` *(en evaluación)* | (pendiente) |

### Hecho
- [x] Esqueleto del tablero Streamlit (selección depto/municipio/salas, serie histórica).
- [x] Módulo de narrativa automática con la API de Claude (system prompt orientado a decisores).

### Falta
- [ ] Conectar el tablero a las **proyecciones reales** (no solo histórico).
- [ ] Mapa coroplético de **demanda insatisfecha** (PyDeck/Folium).
- [ ] Simulador de **exhibidor hipotético** (entrada interactiva → componente B).
- [ ] Desagregación mensual interactiva (componente C) con Plotly.
- [ ] Vista espejo en **Power BI**.
- [ ] Evaluar **Vanna.ai / PandasAI** para consultas en lenguaje natural.
- [ ] Despliegue del contenedor en infraestructura pública.

### 🤖 IA en esta fase
- **API de Claude embebida**: genera **narrativas automáticas** que resumen las
  proyecciones por territorio en lenguaje claro, para que decisores sin perfil
  técnico se apropien de los resultados.
- **Vanna.ai / PandasAI** (en evaluación): permitiría preguntar al modelo en
  lenguaje natural ("¿qué municipios del Cauca tienen más demanda insatisfecha?").

---

## 🤖 Dónde está la Inteligencia Artificial — resumen

| Tipo de IA | Dónde | Qué hace |
|------------|-------|----------|
| **IA predictiva (núcleo)** | Fase 2 | Modelos LightGBM/CatBoost + series de tiempo/TFT que proyectan espectadores a 2027 |
| **IA explicable (XAI)** | Fase 2 | SHAP: hace auditables y comunicables las predicciones |
| **IA generativa (producto)** | Fase 3 | API de Claude: narrativas automáticas por territorio para decisores |
| **IA conversacional (eval.)** | Fase 3 | Vanna.ai/PandasAI: consultas en lenguaje natural sobre el modelo |
| **IA asistente (desarrollo)** | Todas | Claude Code + GitHub Copilot: aceleran la construcción del código |

---

## 🗂️ Fuentes de datos — verificadas en datos.gov.co (API SODA)

> Catálogo completo en [`conf/fuentes.yaml`](conf/fuentes.yaml). Endpoint de consumo:
> `https://www.datos.gov.co/resource/<ID>.json` · metadatos: `/api/views/<ID>.json`.

| Fuente | ID dataset | Consumo | Estado |
|--------|-----------|---------|--------|
| **DIVIPOLA — Códigos municipios** (DANE) | `gdxc-w37w` | ✅ **API SODA** (1.122 mpios, con lat/lon) | ✅ **Cableado y descargado** → `data/reference/divipola.csv` |
| **DANE proyecciones por edad** (CNPV 2018, 2018-2042) | anexo `PPED-AreaSexoEdadMun` | ✅ Descarga oficial DANE (.xlsx, ~126 MB) | ✅ **Descargado y procesado** → `data/processed/dane_poblacion.parquet` (población 15–44) |
| **Población escolar** por municipio (MinEducación) | `nudc-7mev` | ✅ API SODA (demo) | Solo demo de consumo; no es la demografía del modelo |
| **SIREC** exhibición (DACMI) | — | Aporte directo del equipo | ⬜ No publicado en datos abiertos aún |
| Salas de cine y cinematecas | `p2nc-v3da` | ❌ No tabular (mapa/historia) | Descartado para API |
| INVIAS / DNP red vial | — | Descarga / servicios geo | ⬜ En evaluación |
| OpenStreetMap (OSMnx) | — | API Overpass | ⬜ En evaluación |

> **Decisión (2026-06-22):** para la demografía del modelo usamos la **proyección
> municipal por edad del DANE** (franja **15–44 años**, la de mayor consumo de cine),
> no la población escolar 5–16 del MinEducación (esa queda solo como ejemplo de
> consumo por API en la demo).

**Prueba de consumo por API (reproducible):**
```bash
# Metadatos del recurso
curl "https://www.datos.gov.co/api/views/gdxc-w37w.json"
# Datos (primeras 2 filas)
curl "https://www.datos.gov.co/resource/gdxc-w37w.json?\$limit=2"
# Desde el pipeline del proyecto
cinepredict download --source divipola
```

---

## ⚖️ Principios transversales

- **Gobierno abierto:** todo el código, docs y modelo bajo licencia MIT en GitHub.
- **Reproducibilidad real:** Marimo (sin estado oculto), Docker, descarga reproducible.
- **Ética y auditabilidad:** SHAP para explicar; validación temporal sin fuga de datos.
- **Articulación de política:** potencial conexión con la **Ley 814 de 2003** (fomento a la exhibición regional).

---

## ✅ Próximos pasos inmediatos

1. [ ] Obtener los **IDs 4×4** de SIREC y DANE en datos.gov.co → completar `.env`.
2. [ ] `cinepredict download --source sirec` e inspeccionar columnas reales.
3. [ ] Cargar `data/reference/divipola.csv`.
4. [ ] Ajustar la consulta de `clean.py` al esquema real y generar `analytic.parquet`.
5. [ ] EDA con ydata-profiling + documentar vacíos estructurales (COVID).
