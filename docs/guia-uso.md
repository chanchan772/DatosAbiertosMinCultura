# Guía de uso

## Instalación

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1     # Windows PowerShell
pip install -e ".[dev]"
copy .env.example .env          # completar tokens
```

## Pipeline completo

```bash
cinepredict download --source all   # SIREC + DANE desde datos.gov.co
cinepredict clean                   # tabla analítica normalizada y validada
cinepredict train                   # entrena componentes A, B, C (registra en MLflow)
cinepredict report                  # figuras para la presentación
streamlit run app/streamlit_app.py  # tablero interactivo
```

O con `make`: `make data && make clean && make train && make app`.

## Requisitos previos de datos

- `data/reference/divipola.csv` — diccionario DIVIPOLA del DANE (municipio → código).
- IDs de dataset reales en `.env`: `SIREC_DATASET_ID`, `DANE_POBLACION_DATASET_ID`.

## Experimentos

```bash
mlflow ui          # consultar runs en http://localhost:5000
```
