# CinePredict — Modelo predictivo de espectadores de cine en Colombia

> **Concurso Datos al Ecosistema 2026: IA para Colombia** — Reto 8: Cultura y Turismo
> Grupo de Producción y Gestión de la Información — DACMI, Ministerio de las Culturas, las Artes y los Saberes

Modelo predictivo y abierto de **asistencia a salas de cine** en Colombia a nivel
nacional, regional y por exhibidor, con horizonte de proyección al año **2027**.
El proyecto busca caracterizar y cerrar la **brecha de acceso cinematográfico**:
la infraestructura de salas se concentra en pocas ciudades, generando inequidad
en el consumo cultural que los datos permiten identificar pero que aún no se ha
modelado de forma sistemática y abierta.

## Preguntas que responde el modelo

1. **Proyección por exhibidor** — ¿cuántos espectadores captaría un exhibidor
   hipotético dado un número de salas y una ubicación?
2. **Demanda insatisfecha** — ¿qué municipios concentran demanda potencial sin
   oferta de salas suficiente?
3. **Estacionalidad** — ¿cómo se desagrega la proyección mes a mes incorporando
   efectos estacionales y festivos?

## Arquitectura del modelo (híbrida, 3 componentes)

| Componente | Qué estima | Técnica |
|------------|------------|---------|
| **A — Demanda potencial municipal** | Espectadores potenciales por municipio | Regresión sobre variables demográficas (DANE) y de accesibilidad (OSM/INVIAS) |
| **B — Captura por exhibidor** | Espectadores capturados según nº de salas y territorio | Gradient boosting (LightGBM/CatBoost) |
| **C — Estacionalidad y tendencia** | Desagregación mensual y tendencia | Series de tiempo (SARIMAX / Prophet / TFT) |

El quiebre **2020-2021 (COVID-19)** se modela explícitamente como variable de intervención.

## Fases del proyecto

- **Fase 1 — Integración y limpieza.** Normalización a la unidad de análisis
  `sala × municipio × período`, validación de esquemas (Pandera/Great Expectations)
  y reconciliación territorial contra el código **DIVIPOLA** del DANE.
- **Fase 2 — Modelado predictivo.** Entrenamiento de los componentes A, B y C;
  optimización con Optuna; trazabilidad con MLflow; explicabilidad con SHAP.
- **Fase 3 — Visualización e interfaz.** Tablero interactivo en Streamlit
  (consulta por departamento, municipio y perfil de exhibidor) con vista espejo
  en Power BI para apropiación institucional.

## Fuentes de datos

**Primarias**
- **SIREC** — Sistema de Información y Registro Cinematográfico (DACMI), datos
  abiertos de exhibición por sala, título, período y espectadores. → datos.gov.co
- **DANE** — Proyecciones de población municipal/departamental (Censo 2018).

**Complementarias (en evaluación)**
- INVIAS / DNP — conectividad vial (variables de accesibilidad).
- DNP — Medición de Desempeño Municipal (MDM) y categorización (Ley 617/2000).
- MGN (DANE) — cartografía oficial para cruces espaciales.
- OpenStreetMap (vía OSMnx) — red vial para matrices de tiempo de desplazamiento.

## Stack tecnológico

`Python 3.12` · `DuckDB` · `Polars`/`pandas` · `GeoPandas`/`Shapely`/`H3` ·
`OSMnx`/`NetworkX` · `Pandera`/`Great Expectations` · `ydata-profiling` ·
`StatsForecast`/`Prophet`/`NeuralForecast` · `LightGBM`/`CatBoost` ·
`Optuna`/`MLflow`/`SHAP` · `scikit-learn`/`sktime` ·
`Streamlit`/`PyDeck`/`Folium`/`Plotly` · `Power BI` (espejo) ·
`API de Claude` (narrativas automáticas) · `Marimo` · `Docker` · `MkDocs Material`.

## Estructura del repositorio

```
.
├── conf/                 # Configuración (paths, parámetros de modelo)
├── data/                 # raw / interim / processed / external / reference
├── docs/                 # Documentación (MkDocs Material)
├── notebooks/            # Notebooks reactivos (Marimo)
├── src/cinepredict/
│   ├── config.py         # Carga de configuración y rutas
│   ├── cli.py            # CLI (typer): download / clean / train / report
│   ├── data/             # Descarga (Socrata), limpieza, DIVIPOLA, esquemas
│   ├── features/         # Variables demográficas y de accesibilidad
│   ├── models/           # Componentes A (demand), B (capture), C (seasonality)
│   ├── validation/       # Suites de Great Expectations
│   └── viz/              # Mapas y gráficos
├── app/                  # Tablero Streamlit
├── reports/figures/      # Salidas para la presentación final
└── tests/
```

## Inicio rápido

Recomendado con [`uv`](https://docs.astral.sh/uv/) (gestiona Python 3.12 y el entorno):

```bash
# 1. Crear entorno Python 3.12 e instalar todo el stack
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -e ".[dev]"

# 2. Configurar credenciales
copy .env.example .env   # ANTHROPIC_API_KEY para narrativas (opcional)

# 3. Pipeline completo de extremo a extremo
.venv\Scripts\python -m cinepredict.cli download --source divipola   # API datos.gov.co
.venv\Scripts\python -m cinepredict.cli download --source dane       # anexo DANE (~126 MB)
.venv\Scripts\python -m cinepredict.cli synth                        # SIREC SINTÉTICO (ver nota)
.venv\Scripts\python -m cinepredict.cli clean                        # tabla analítica + DIVIPOLA
.venv\Scripts\python -m cinepredict.cli features                     # demografía + accesibilidad
.venv\Scripts\python -m cinepredict.cli train                        # modelos A/B/C + proyección 2027

# 4. Tablero
.venv\Scripts\python -m streamlit run app/streamlit_app.py

# 5. (Opcional) Vista espejo en Power BI
.venv\Scripts\python -m cinepredict.cli export-powerbi   # genera powerbi/datos/*.csv
```

Con Docker: `docker compose up --build`.

> ### ⚠️ Datos de SIREC sintéticos (temporal)
> Mientras se incorpora el **SIREC real** (que administra el equipo), el comando
> `cinepredict synth` genera un dataset sintético realista (concentración territorial,
> estacionalidad, quiebre COVID, cadenas de exhibidores) coherente con la población DANE
> 15–44, para construir y **probar el pipeline completo de extremo a extremo**. Al
> disponer del SIREC real basta con reemplazar `data/raw/sirec.parquet` y reentrenar.

## El tablero

Multipágina (Streamlit): **Inicio** · **Datos Abiertos en vivo** (consumo por API) ·
**Demanda y Brecha** (mapa de demanda insatisfecha 2027) · **Simulador de Exhibidor**
(Componente B) · **Estacionalidad** (Componente C con efecto COVID) · **Narrativa IA**
(resúmenes territoriales con la API de Claude).

## Reproducibilidad y gobierno abierto

Todo el código, la documentación y el modelo entrenado se publican bajo licencia
abierta (MIT) en GitHub, garantizando que el producto pueda ser auditado,
replicado y extendido por terceros, en línea con los principios de gobierno
abierto del Estado colombiano y con potencial de articulación con los
instrumentos de fomento a la exhibición regional de la **Ley 814 de 2003**.

## Licencia

[MIT](LICENSE).
