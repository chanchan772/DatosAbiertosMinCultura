# CinePredict — Modelo predictivo de espectadores de cine en Colombia

**Concurso Datos al Ecosistema 2026 · Reto 8 — Cultura y Turismo**
Equipo: Grupo de Producción y Gestión de la Información — DACMI, Ministerio de las Culturas.

CinePredict integra las fuentes abiertas del **SIREC** con **DIVIPOLA** y las **proyecciones
de población del DANE** para responder, de forma transparente y auditable, tres preguntas del
reto:

1. **Proyección para un exhibidor hipotético** — ¿cuántos espectadores captaría con N salas en
   un municipio? (con descomposición honesta *demanda nueva* vs *redistribución*).
2. **Municipios con demanda insatisfecha** — brechas de acceso, clasificadas sin mezclar
   métricas y distinguiendo aislamiento real de conurbación aparente.
3. **Estacionalidad y proyección 2027** — descomposición clásica, reportada como rango de
   escenarios con validación (backtest), no como cifra puntual.

Su rasgo distintivo es la **transparencia total**: cada cifra del tablero trae un panel
"¿Cómo se calcula?" con las fuentes, la fórmula, los valores de entrada y el resultado de
cada paso, para que un jurado pueda reconstruirla a mano.

Stack: **Angular 21** (frontend) + **Python / FastAPI** (backend). Narrativas con **DeepSeek**.

---

## Ejecución rápida

```bash
./run.sh
```

El script instala dependencias (si faltan), genera los datos si es necesario y levanta el
**backend en http://127.0.0.1:8000** y el **frontend en http://127.0.0.1:4200**. Opciones:

```bash
./run.sh --pipeline   # fuerza regenerar el pipeline de datos antes de arrancar
./run.sh --build      # sirve el frontend compilado (producción) en vez de ng serve
./run.sh --backend    # solo backend
```

> El repositorio incluye los datos **ya anonimizados** (`backend/data/processed` y
> `backend/data/external`), de modo que la aplicación corre tras `git clone` sin los Excel
> crudos ni la descarga de 66 MB del DANE. La llave de DeepSeek viene incluida como valor por
> defecto para que los evaluadores puedan probar el tablero sin configuración adicional.

### Ejecución manual

```bash
pip install -r backend/requirements.txt
python -m backend.run_pipeline                 # opcional: regenera datos (idempotente)
uvicorn backend.app.main:app --port 8000       # backend
cd frontend && npm install && ng serve --port 4200   # frontend
```

---

## Arquitectura

```
Concurso Datos Abiertos/
├── run.sh                     # levanta toda la aplicación
├── Datos/                     # 5 Excel crudos del SIREC (no versionados: nombres reales)
├── backend/                   # Python 3.12+ · FastAPI
│   ├── app/
│   │   ├── config.py          # rutas, credenciales, parámetros
│   │   ├── pipeline/          # ingesta, anonimización, DIVIPOLA, población DANE, reconciliación
│   │   ├── models/            # demanda, forecast, exhibidor, panorama, catálogo, metodología, TRAZA
│   │   ├── services/          # cliente DeepSeek (narrativas)
│   │   └── main.py            # API FastAPI
│   ├── data/                  # processed/ external/ (anonimizados, versionados) · private/ (no)
│   ├── run_pipeline.py        # orquestador reproducible del pipeline
│   └── requirements.txt
└── frontend/                  # Angular 21 (standalone, signals, zoneless)
    └── src/app/
        ├── core/              # ApiService + modelos
        ├── shared/            # trace-panel (¿Cómo se calcula?), charts SVG, formato
        └── pages/             # panorama · brechas · simulador · proyeccion · datos · metodologia
```

## Fuentes de datos

| Fuente | Origen | Uso |
|---|---|---|
| Taquilla 2026 (281k filas) | SIREC | Panorama, rendimiento por sala |
| Espectadores por día 2007–2026 | SIREC | Estacionalidad y proyección 2027 |
| Salas registradas + AdmisionesXmunicipio | SIREC | Oferta y demanda insatisfecha |
| Históricos de estrenos (total y Colombia) | SIREC | Contexto de contenido |
| **DIVIPOLA** (`gdxc-w37w`) | **datos.gov.co** (obligatoria) | Reconciliación territorial y mapa |
| Proyecciones municipales por edad 2020–2035 | DANE (CNPV 2018) | Población objetivo por banda de edad |
| Validación por edad Antioquia (`evm3-92yw`) | datos.gov.co | Control de coherencia de las bandas |

> datos.gov.co no publica la proyección nacional municipal-por-edad; se usa el archivo primario
> del DANE (upstream del mismo dato) y se valida contra datos.gov.co, dejando constancia.

## Metodología y transparencia

Todos los parámetros que afectan resultados viven en `backend/app/models/methodology.py`
(fuente única de verdad). Cada modelo construye una `CalculationTrace` que la API expone en el
campo `trace`, y el frontend renderiza en el panel **"¿Cómo se calcula?"**.

- **Demanda insatisfecha**: clasifica cada municipio en *sin oferta* / *subatendido* /
  *saturado-polo* con una fórmula distinta por grupo (nunca se suman métricas heterogéneas). La
  tasa de referencia es un promedio ponderado por población que **excluye los polos de atracción**
  (winsorización p90) para no inflar el potencial. La cobertura se calcula sobre residentes:
  `(potencial − insatisfecha) / potencial`. Para el fomento, la brecha estructural distingue
  **aislamiento real** de **conurbación aparente** midiendo la distancia (haversine) al polo con
  cine más cercano.
- **Proyección 2027**: descomposición clásica (nivel × factor estacional). Con solo 4 años
  completos post-COVID, se reporta un **rango de escenarios** (conservador / central / optimista),
  un **backtest** walk-forward (ajustar 2022–2024, predecir 2025) y el **R²** del ajuste, en
  lugar de una cifra puntual de crecimiento.
- **Simulador**: separa *demanda nueva* de *redistribución* de mercado, evitando cifras engañosas.

## Anonimización

Los datos de los Excel se **pseudonimizan antes de procesarse** asignando seudónimos
secuenciales estables (EXH-001, CPX-001, …) sin relación con el nombre real; se eliminan
direcciones (PII). El token no deriva del nombre, por lo que **no es reidentificable** aunque el
universo sea pequeño; la única correspondencia vive en `backend/data/private/` (no versionado).
Al ser determinista, **todo agregado da exactamente el mismo número** que con los nombres reales.

## Aseguramiento de calidad (revisión por jurados)

El proyecto fue auditado por un **panel de 3 agentes-jurado** (metodología ML, política pública /
dominio, e ingeniería de datos / transparencia). Se aplicaron todas las correcciones obligatorias:
proyección 2027 como rango con backtest (central ≈ 51.2M, no 55.2M puntual); cobertura coherente
sobre residentes (≈54%); anonimización irreversible por seudónimos; distancia al polo para separar
aislamiento de conurbación; y unificación de la tasa de referencia. El detalle de fórmulas,
supuestos y limitaciones está en la pestaña **Metodología** del tablero.

## Licencia
Código abierto, para auditoría, réplica y extensión por terceros — en línea con los principios
de gobierno abierto y datos abiertos del Estado colombiano.
