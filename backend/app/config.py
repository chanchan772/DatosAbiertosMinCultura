"""
config.py — Configuracion central del backend CinePredict.

Rutas del proyecto, parametros de anonimizacion y credenciales de servicios
externos (DeepSeek, datos.gov.co). Las credenciales se leen de variables de
entorno con un fallback explicito para desarrollo local.

Transparencia: todos los parametros que afectan calculos (tasas per-capita,
bandas de edad, umbrales de brecha) viven en este archivo o en
`methodology.py`, NUNCA ocultos dentro de la logica, para que el jurado pueda
auditarlos en un solo lugar.
"""
from __future__ import annotations

import os
from pathlib import Path

# Carga liviana de un .env local (NO versionado) sin dependencias externas.
# Permite mantener secretos (llave DeepSeek) fuera del codigo entregado.
def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# --------------------------------------------------------------------------- #
# Rutas
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[2]           # .../Concurso Datos Abiertos
DATOS_RAW = ROOT / "Datos"                            # Excel crudos (entrada)
DATA = ROOT / "backend" / "data"
DATA_INTERIM = DATA / "interim"                       # productos intermedios/perfiles
DATA_PROCESSED = DATA / "processed"                   # tablas limpias y anonimizadas (parquet)
DATA_EXTERNAL = DATA / "external"                     # DIVIPOLA, poblacion DANE (cache datos.gov.co)
DATA_PRIVATE = DATA / "private"                       # mapeo de pseudonimizacion (NO se publica)

for _p in (DATA_INTERIM, DATA_PROCESSED, DATA_EXTERNAL, DATA_PRIVATE):
    _p.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Anonimizacion / pseudonimizacion
# --------------------------------------------------------------------------- #
# Tecnica: SEUDONIMOS SECUENCIALES sin relacion con el nombre real (EXH-001,
# CPX-001, ...), asignados por orden alfabetico estable. A diferencia de un hash
# del nombre, el token NO permite reidentificar por fuerza bruta aunque el
# universo de entidades sea pequeno: la unica correspondencia token->real vive en
# DATA_PRIVATE (no versionado, ver .gitignore) y no forma parte del entregable.
# Preserva todas las relaciones analiticas (agrupar por token == por entidad
# real), por lo que NO afecta ningun resultado numerico.
REVEAL_REAL_NAMES = os.environ.get("CINEPREDICT_REVEAL", "0") == "1"

# --------------------------------------------------------------------------- #
# Servicios externos
# --------------------------------------------------------------------------- #
# datos.gov.co (Socrata)
DATOS_GOV_BASE = "https://www.datos.gov.co"
DIVIPOLA_MUNICIPIOS_ID = "gdxc-w37w"   # DIVIPOLA - Codigos municipios (DANE/DNP)
DIVIPOLA_DEPARTAMENTOS_ID = "vcjz-niiq"

# DeepSeek (narrativas automaticas). La llave se puede sobreescribir por variable
# de entorno o por backend/.env; el fallback es la llave del equipo, incluida a
# proposito para que el jurado/los testers puedan ejecutar el tablero sin
# configuracion adicional. Si no hubiera llave, /api/narrative degrada a una
# narrativa de respaldo generada localmente.
DEEPSEEK_API_KEY = os.environ.get(
    "DEEPSEEK_API_KEY", "sk-31382fc441eb4fe28414478ac6fd793f"
)
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# --------------------------------------------------------------------------- #
# Ventana temporal de los datos (documentada para el tablero)
# --------------------------------------------------------------------------- #
TAQUILLA_ANIO = 2026            # el detalle transaccional cubre solo 2026 (parcial)
TAQUILLA_CORTE = "2026-05-24"   # ultima fecha de exhibicion observada
SERIE_INICIO = "2007-01-01"     # serie diaria nacional de espectadores
SERIE_FIN = "2026-06-28"
HORIZONTE_PROYECCION = 2027     # ano objetivo de proyeccion del reto
