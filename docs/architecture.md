# Arquitectura

CinePredict es una aplicación **full-stack** con dos modos de ejecución:

- **Local/producción con backend:** frontend Angular + API FastAPI en vivo (incluye narrativas
  DeepSeek).
- **Demo estática (GitHub Pages):** SPA Angular que consume JSON precomputados y calcula las
  partes interactivas en el navegador, sin backend.

```
┌────────────────────────┐      HTTP/JSON      ┌───────────────────────────┐
│  Frontend Angular 21   │  ───────────────▶   │   Backend FastAPI          │
│  (standalone, signals) │                     │                           │
│  · panorama            │  ◀───────────────   │  models/  (traza auditable)│
│  · brechas (mapa)      │     trace + datos   │   demanda, forecast,       │
│  · simulador           │                     │   exhibidor, overview,     │
│  · proyección 2027     │                     │   catálogo, metodología    │
│  · catálogo            │                     │  services/ deepseek        │
│  · metodología         │                     └─────────────┬─────────────┘
└────────────────────────┘                                   │
        ▲  (modo estático)                                   │ lee
        │ JSON precomputados                                 ▼
        │                                       ┌───────────────────────────┐
        └───────────────────────────────────    │  pipeline/                 │
                                                 │  ingesta → anonimización   │
                                                 │  → DIVIPOLA/DANE → recon.  │
                                                 └─────────────┬─────────────┘
                                                               │ produce
                                                               ▼
                                          data/processed (parquet anonimizado)
                                          data/external  (DIVIPOLA + población)
```

## Backend (`backend/`)

- `app/config.py` — rutas, parámetros y credenciales.
- `app/pipeline/` — `ingest.py` (5 Excel → parquet + anonimización), `external.py` (DIVIPOLA),
  `population.py` (DANE por edad), `reconcile.py` (DIVIPOLA), `anonymize.py`, `text_utils.py`.
- `app/models/` — `demand.py`, `forecast.py`, `exhibitor.py`, `overview.py`, `catalog.py`,
  `methodology.py` (fuente única de parámetros) y `trace.py` (`CalculationTrace`).
- `app/services/deepseek.py` — narrativas automáticas.
- `app/main.py` — API FastAPI.
- `run_pipeline.py` — orquestador reproducible; `scripts/export_static.py` — exporta los JSON del
  demo estático.

## Frontend (`frontend/src/app/`)

- `core/` — `api.service.ts` (conmuta live/estático), `models.ts`, `static-compute.ts`.
- `shared/` — `trace-panel.ts` (¿Cómo se calcula?), `charts.ts` (SVG), `format.ts`.
- `pages/` — los 6 módulos.

## Reproducibilidad y despliegue

- Todo el pipeline es idempotente (`python -m backend.run_pipeline`).
- `run.sh` levanta backend + frontend en local.
- GitHub Actions (`.github/workflows/deploy.yml`) compila el modo estático y publica en
  **GitHub Pages** en cada push a `main`.

## Stack tecnológico
Python 3.12 · FastAPI · pandas / pyarrow / numpy / scikit-learn · Angular 21 (standalone, signals,
zoneless) · gráficos SVG propios · DeepSeek (narrativas) · GitHub Pages / Actions.
