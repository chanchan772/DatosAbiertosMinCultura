#!/usr/bin/env bash
# =============================================================================
# CinePredict — arranque de toda la aplicacion (backend FastAPI + frontend Angular)
# Uso:
#   ./run.sh              backend :8000 + frontend (ng serve) :4200
#   ./run.sh --pipeline   regenera el pipeline de datos antes de arrancar
#   ./run.sh --build      sirve el frontend compilado (produccion)
#   ./run.sh --backend    solo backend
# =============================================================================
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PIPELINE=0; BUILD=0; ONLY_BACKEND=0
for a in "$@"; do
  case "$a" in
    --pipeline) PIPELINE=1 ;;
    --build)    BUILD=1 ;;
    --backend)  ONLY_BACKEND=1 ;;
    *) echo "Opcion desconocida: $a" ;;
  esac
done

PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || { echo "ERROR: no se encontro python"; exit 1; }

echo "==> CinePredict"
echo "    raiz: $ROOT"

# --- dependencias backend ---------------------------------------------------
if ! "$PY" -c "import fastapi, pandas, pyarrow, uvicorn" >/dev/null 2>&1; then
  echo "==> Instalando dependencias de Python..."
  "$PY" -m pip install -q -r backend/requirements.txt
fi

# --- datos ------------------------------------------------------------------
if [ "$PIPELINE" = "1" ] || [ ! -f "backend/data/processed/fact_taquilla.parquet" ]; then
  echo "==> Generando pipeline de datos (ingesta + fuentes + reconciliacion)..."
  "$PY" -m backend.run_pipeline
else
  echo "==> Datos procesados presentes (usa --pipeline para regenerar)."
fi

# --- backend ----------------------------------------------------------------
echo "==> Iniciando backend en http://127.0.0.1:8000 ..."
"$PY" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --log-level warning &
BACK_PID=$!

cleanup() {
  echo ""; echo "==> Deteniendo servicios..."
  kill "$BACK_PID" >/dev/null 2>&1
  [ -n "${FRONT_PID:-}" ] && kill "$FRONT_PID" >/dev/null 2>&1
  exit 0
}
trap cleanup INT TERM

# espera a que el backend responda
for i in $(seq 1 30); do
  if curl -s -o /dev/null "http://127.0.0.1:8000/api/health" 2>/dev/null; then
    echo "    backend OK"; break; fi
  sleep 1
done

if [ "$ONLY_BACKEND" = "1" ]; then
  echo "==> Backend listo. API: http://127.0.0.1:8000/docs  (Ctrl+C para salir)"
  wait "$BACK_PID"; exit 0
fi

# --- frontend ---------------------------------------------------------------
command -v node >/dev/null 2>&1 || { echo "ERROR: no se encontro node"; cleanup; }
cd frontend
if [ ! -d node_modules ]; then
  echo "==> Instalando dependencias del frontend (npm install)..."
  npm install
fi

if [ "$BUILD" = "1" ]; then
  echo "==> Compilando frontend (produccion)..."
  npx ng build
  echo "==> Sirviendo frontend compilado en http://127.0.0.1:4200 ..."
  npx serve -s dist/frontend/browser -l 4200 &
  FRONT_PID=$!
else
  echo "==> Iniciando frontend (ng serve) en http://127.0.0.1:4200 ..."
  npx ng serve --host 127.0.0.1 --port 4200 &
  FRONT_PID=$!
fi

echo ""
echo "=================================================================="
echo "  CinePredict en marcha:"
echo "    Frontend : http://127.0.0.1:4200"
echo "    Backend  : http://127.0.0.1:8000  (docs en /docs)"
echo "  Ctrl+C para detener ambos."
echo "=================================================================="
wait "$FRONT_PID"
cleanup
