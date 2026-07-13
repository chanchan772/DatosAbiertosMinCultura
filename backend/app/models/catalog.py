"""
catalog.py — Catálogo de datos y procedencia (sección de transparencia de fuentes).

Construye la descripción estructurada de CADA fuente usada: los 5 Excel del SIREC
más las fuentes externas obligatorias (DIVIPOLA de datos.gov.co y proyecciones
DANE), indicando qué contiene, cuántas filas, campos clave, en qué módulo se usa
y su procedencia exacta. Combina descripciones curadas con estadísticas leídas de
los manifiestos generados por el pipeline.
"""
from __future__ import annotations

import json

from ..config import DATA_INTERIM, DATA_EXTERNAL, DATA_PRIVATE

# Descripción curada de cada fuente (conocimiento del equipo administrador SIREC).
FUENTES = [
    {
        "id": "taquilla_2026",
        "archivo": "Taquilla 2026-Colarco.xlsx",
        "titulo": "Taquilla 2026 — detalle transaccional de admisiones",
        "fuente": "SIREC (DACMI)",
        "grupo": "primaria",
        "descripcion": "Registro transaccional de admisiones por sala, título, fecha y "
                       "exhibidor durante 2026 (corte 24-may). Es la mayor fuente de "
                       "granularidad: permite construir la unidad sala × municipio × período.",
        "campos_clave": ["Fecha Exhibición", "ID EXHIBIDOR/COMPLEJO/SALA", "TITULO",
                         "Admisiones", "Departamento", "Municipio", "Género",
                         "Clasificación", "Nacionalidad", "Catálogo/Estreno"],
        "usos": ["Panorama nacional", "Rendimiento por sala (simulador)",
                 "Concentración territorial y empresarial"],
        "notas": "Año parcial (ene–may 2026). No comparar su total contra años completos.",
    },
    {
        "id": "espectadores_dia",
        "archivo": "Datos abiertos.xlsx",
        "titulo": "Espectadores por día — serie diaria nacional",
        "fuente": "SIREC (DACMI)",
        "grupo": "primaria",
        "descripcion": "Serie temporal diaria de asistencia nacional 2007–2026 (≈7.011 días). "
                       "Muestra con claridad el quiebre COVID (2020–2021) y la recuperación.",
        "campos_clave": ["FECHA", "ASISTENCIA", "SEMANA CALENDARIO"],
        "usos": ["Estacionalidad y tendencia", "Proyección 2027"],
        "notas": "Base del modelo de series de tiempo; 2020–2021 se tratan como intervención.",
    },
    {
        "id": "salas_activas",
        "archivo": "Salas de Cine Registradas y Activas.xlsx",
        "titulo": "Salas registradas y activas + admisiones por municipio",
        "fuente": "SIREC (DACMI)",
        "grupo": "primaria",
        "descripcion": "Oferta de exhibición: complejos con número de salas y capacidad "
                       "(hoja Base Datos), y admisiones + salas activas por municipio para "
                       "2024/2025/2026 (hoja AdmisionesXmunicipio).",
        "campos_clave": ["Complejo", "Municipio", "No Salas", "Capacidad",
                         "# Salas activas", "Admisiones (Miles) por año"],
        "usos": ["Demanda insatisfecha (oferta)", "Rendimiento por sala", "Mapa de brechas"],
        "notas": "Admisiones por municipio vienen en miles; se convierten a unidades.",
    },
    {
        "id": "estrenos_total",
        "archivo": "HISTORICO Estrenos Total.xlsx",
        "titulo": "Histórico de estrenos — total (largometrajes 2020+)",
        "fuente": "SIREC (DACMI)",
        "grupo": "primaria",
        "descripcion": "Catálogo de largometrajes exhibidos desde 2020 con alcance "
                       "territorial (municipios, exhibidores, complejos, pantallas, semanas).",
        "campos_clave": ["Título", "Año", "Género", "Clasificación", "Nacionalidad",
                         "Admisiones", "# Municipios/Exhibidores/Pantallas"],
        "usos": ["Contexto de oferta de contenido", "Análisis de alcance por película"],
        "notas": "Enriquecimiento; no es la unidad de análisis central.",
    },
    {
        "id": "estrenos_colombia",
        "archivo": "HISTORICO Estrenos Colombia.xlsx",
        "titulo": "Histórico de estrenos — cine colombiano",
        "fuente": "SIREC (DACMI)",
        "grupo": "primaria",
        "descripcion": "Estrenos de producción colombiana con admisiones y cobertura, "
                       "clave para dimensionar la participación del cine nacional.",
        "campos_clave": ["Título", "Año Estreno", "Género", "Admisiones", "Nacionalidad"],
        "usos": ["Participación del cine colombiano", "Contexto de fomento (Ley 814)"],
        "notas": "Solo 1,45% de las admisiones 2026 corresponden a cine colombiano.",
    },
    {
        "id": "divipola",
        "archivo": "datos.gov.co · gdxc-w37w",
        "titulo": "DIVIPOLA — códigos de municipios (obligatoria datos.gov.co)",
        "fuente": "DANE / DNP vía datos.gov.co",
        "grupo": "externa",
        "descripcion": "División político-administrativa oficial: 1.122 municipios con "
                       "código de 5 dígitos y geolocalización. Base de la reconciliación "
                       "territorial y del mapa.",
        "campos_clave": ["cod_dpto", "cod_mpio", "nom_mpio", "lat", "lon"],
        "usos": ["Reconciliación territorial", "Mapa de brechas", "Universo de municipios"],
        "notas": "Fuente obligatoria del concurso, consumida vía API Socrata.",
    },
    {
        "id": "poblacion_dane",
        "archivo": "DANE · Proyecciones municipales por edad 2020–2035",
        "titulo": "Proyecciones de población municipal por edad (DANE, post-COVID)",
        "fuente": "DANE (dane.gov.co)",
        "grupo": "externa",
        "descripcion": "Proyecciones por edad simple y municipio (base CNPV 2018). Se derivan "
                       "las bandas 15–30, 15–45 y 15–60 como población objetivo de asistencia. "
                       "datos.gov.co no publica la versión nacional-por-edad; se usa la fuente "
                       "primaria DANE y se valida contra datos.gov.co (Antioquia, evm3-92yw).",
        "campos_clave": ["DPMP (código)", "AÑO", "ÁREA GEOGRÁFICA", "Total_0…Total_85+"],
        "usos": ["Demanda potencial", "Demanda insatisfecha", "Simulador"],
        "notas": "Validación cruzada: Medellín 15–30 (DANE 2024 ≈ 678.966) vs censo "
                 "datos.gov.co (≈ 675.549).",
    },
]


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def compute() -> dict:
    manifest = _read_json(DATA_INTERIM / "catalog_manifest.json")
    external = _read_json(DATA_EXTERNAL / "external_manifest.json")
    reconcile = _read_json(DATA_INTERIM / "reconcile_report.json")
    anon = _read_json(DATA_PRIVATE / "anon_summary.json")

    # adjunta estadísticas dinámicas por fuente donde aplique
    stats_map = {
        "taquilla_2026": manifest.get("tablas", {}).get("fact_taquilla", {}),
        "espectadores_dia": manifest.get("tablas", {}).get("serie_diaria_nacional", {}),
        "salas_activas": manifest.get("tablas", {}).get("admisiones_municipio_anual", {}),
        "estrenos_total": manifest.get("tablas", {}).get("dim_peliculas", {}),
        "estrenos_colombia": manifest.get("tablas", {}).get("dim_estrenos_colombia", {}),
        "divipola": external.get("divipola_municipios", {}),
        "poblacion_dane": external.get("poblacion_municipal_dane", {}),
    }
    fuentes = []
    for f in FUENTES:
        st = stats_map.get(f["id"], {})
        fuentes.append({**f, "filas": st.get("filas"), "procedencia": st.get("url")})

    return {
        "fuentes": fuentes,
        "anonimizacion": {
            "tecnica": manifest.get("anonimizacion", {}).get("tecnica"),
            "detalle": manifest.get("anonimizacion", {}),
            "entidades_por_tipo": anon,
        },
        "reconciliacion_territorial": {
            "pares": reconcile.get("pares_totales"),
            "emparejados": reconcile.get("emparejados"),
            "cobertura_pct": reconcile.get("cobertura_pct"),
            "por_metodo": reconcile.get("por_metodo"),
        },
        "procedencia_externa": external,
    }


if __name__ == "__main__":
    r = compute()
    for f in r["fuentes"]:
        print(f"- [{f['grupo']}] {f['titulo']}  (filas: {f['filas']})")
    print("\nAnonimización:", r["anonimizacion"]["entidades_por_tipo"])
    print("Reconciliación:", r["reconciliacion_territorial"]["cobertura_pct"], "%")
