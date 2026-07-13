"""
methodology.py — Parametros y metodologia documentada (fuente unica de verdad).

TODO parametro que afecta un calculo vive aqui, nunca escondido en la logica.
Cada bloque METODOLOGIA describe, para un modulo: que responde, la fuente de
datos, la formula, los supuestos y las limitaciones. La API expone esto tal cual
para el panel de transparencia del tablero.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# Parametros del modelo (auditables)
# --------------------------------------------------------------------------- #
PARAMS = {
    # Banda de edad usada como "poblacion objetivo" para la demanda potencial.
    # Se puede cambiar a pob_15_30 o pob_15_60 desde el simulador (es un filtro
    # con respaldo de datos DANE, no cosmetico).
    "banda_objetivo_default": "pob_15_45",
    "bandas_disponibles": {
        "pob_15_30": "15 a 30 años (jóvenes)",
        "pob_15_45": "15 a 45 años (núcleo de asistencia)",
        "pob_15_60": "15 a 60 años (amplia)",
    },
    # Percentil por encima del cual un municipio se considera "polo de atraccion"
    # y se EXCLUYE del calculo de la tasa de referencia (winsorizacion). La tasa
    # es el promedio ponderado por poblacion del resto. NO es un "percentil 75".
    "winsor_polos_percentil": 0.90,
    # Año de referencia para el analisis de demanda (ultimo año COMPLETO).
    "anio_referencia_demanda": 2025,
    # Años que representan el choque COVID (intervencion en la serie temporal).
    "anios_covid": [2020, 2021],
    # Factor de recuperacion: 2022 en adelante se considera post-choque.
    "anio_normalizacion_post_covid": 2023,
    # Horizonte de proyeccion.
    "anio_proyeccion": 2027,
    # Tope de penetracion para no reportar "demanda insatisfecha" espuria en
    # municipios que son polo de atraccion (reciben publico de vecinos).
    "penetracion_saturacion": 1.0,
    # Distancia (km) por debajo de la cual un municipio SIN sala se considera
    # conurbado a un polo con cine (brecha aparente por cercania, no aislamiento).
    "umbral_conurbacion_km": 25.0,
}

METODOLOGIA = {
    "panorama_nacional": {
        "pregunta": "¿Cuál es la magnitud y evolución del consumo de cine en Colombia?",
        "fuente": "SIREC — 'Espectadores por día' (serie diaria nacional 2007–2026) "
                  "y 'Taquilla 2026' (detalle transaccional).",
        "formula": "Agregación directa: asistencia anual = Σ asistencia diaria del año.",
        "supuestos": ["La serie diaria nacional es el agregado oficial de admisiones "
                      "reportadas al SIREC por los exhibidores."],
        "limitaciones": ["2026 es un año parcial (corte a junio); no debe compararse "
                         "en total anual contra años completos."],
    },
    "demanda_potencial": {
        "pregunta": "¿Cuánta asistencia podría generar un municipio si el acceso no "
                    "fuera la restricción?",
        "fuente": "Población por edad: DANE — Proyecciones municipales post-COVID "
                  "2020–2035 (edades simples). Asistencia realizada: SIREC "
                  "'AdmisionesXmunicipio'. Territorio: DIVIPOLA (datos.gov.co).",
        "formula": "demanda_potencial(m) = poblacion_objetivo(m) × tasa_referencia\n"
                   "tasa_referencia = Σ admisiones / Σ poblacion_objetivo, sobre los "
                   "municipios CON oferta, excluyendo los 'polos de atracción' cuya "
                   "tasa per cápita supera el percentil 90 (para no inflar el benchmark "
                   "con satélites que captan público de toda una región).",
        "supuestos": [
            "La tasa per cápita observada donde SÍ hay cine (promedio ponderado por "
            "población, sin polos extremos) aproxima el consumo alcanzable si el "
            "acceso no fuera la restricción.",
            "La población objetivo (banda de edad) concentra la propensión a asistir.",
        ],
        "limitaciones": [
            "No modela explícitamente la fuga de público entre municipios vecinos "
            "(un habitante sin sala local puede asistir en otro municipio).",
            "La tasa de referencia es un benchmark nacional, no específico por región.",
        ],
    },
    "demanda_insatisfecha": {
        "pregunta": "¿Qué municipios tienen demanda potencial que hoy NO se atiende?",
        "fuente": "Combina demanda_potencial (arriba) con oferta de salas "
                  "(SIREC 'Salas registradas y activas').",
        "formula": (
            "Se clasifican los municipios en tres grupos, sin mezclar métricas:\n"
            "1) BRECHA ESTRUCTURAL — municipios con 0 salas activas: toda su "
            "demanda potencial residente está sin atender localmente.\n"
            "   insatisfecha(m) = demanda_potencial(m)\n"
            "2) SUBATENDIDO — municipios con salas pero penetración < 1:\n"
            "   penetracion(m) = admisiones_realizadas(m) / demanda_potencial(m)\n"
            "   insatisfecha(m) = max(0, demanda_potencial(m) − admisiones_realizadas(m))\n"
            "3) POLO DE ATRACCIÓN / SATURADO — penetración ≥ 1: insatisfecha = 0 "
            "(atrae público de otros municipios; no se le imputa déficit)."
        ),
        "supuestos": [
            "La demanda insatisfecha se mide sobre RESIDENTES del municipio.",
            "Penetración ≥ 1 indica que el municipio ya captura toda su demanda "
            "residente (y probablemente parte de la de sus vecinos).",
        ],
        "limitaciones": [
            "La brecha estructural sobreestima la necesidad local si los residentes "
            "ya se desplazan a un municipio vecino cercano. Para mitigarlo se calcula "
            "la distancia (haversine) al polo con cine más cercano y se marca la brecha "
            "como 'conurbación' (aparente, a ≤25 km de un polo) o 'aislamiento' (real), "
            "de modo que el fomento priorice municipios genuinamente aislados.",
        ],
    },
    "estacionalidad_proyeccion": {
        "pregunta": "¿Cómo se distribuye la asistencia dentro del año y cuánto se "
                    "proyecta para 2027?",
        "fuente": "SIREC — serie diaria nacional 2007–2026.",
        "formula": (
            "Descomposición clásica multiplicativa: serie_mensual = nivel × factor_estacional.\n"
            "La proyeccion NO es un punto sino un RANGO de escenarios:\n"
            "1) central = promedio del total anual de los años normalizados (≥2023), que ya "
            "no arrastran la recuperacion; es el nivel estable observado.\n"
            "2) conservador = regresion lineal solo con años ≥2023 (pendiente ≈ plana/neg).\n"
            "3) optimista = regresion lineal incluyendo 2022 (año de recuperacion).\n"
            "4) factor_estacional(mes) = promedio( asistencia_mes / media_mensual_año ).\n"
            "5) proyeccion_central(mes) = (central / 12) × factor_estacional(mes).\n"
            "Se reporta ademas un backtest walk-forward (ajustar 2022-2024, predecir 2025) y "
            "el R² del ajuste, para exponer la incertidumbre."
        ),
        "supuestos": [
            "El patrón estacional (vacaciones, estrenos) es estable entre años.",
            "2020–2021 se excluyen por el cierre de salas; 2022 se trata como año de "
            "recuperacion cuya pendiente ya se agoto (no proyectable como tendencia).",
        ],
        "limitaciones": [
            "Con solo 4 años completos post-COVID la tendencia lineal es inestable (R² bajo, "
            "≈0.22 al incluir 2022); por eso el resultado se comunica como rango, no como cifra "
            "puntual de crecimiento.",
            "El backtest a 1 año muestra ~13% de error, magnitud que debe tenerse en cuenta.",
            "No incorpora el calendario específico de estrenos de 2027.",
        ],
    },
    "captura_exhibidor": {
        "pregunta": "¿Cuántos espectadores captaría un exhibidor hipotético con N "
                    "salas en un municipio dado?",
        "fuente": "SIREC — 'AdmisionesXmunicipio' (año 2025, admisiones y salas activas por "
                  "municipio). El rendimiento por sala usa el año 2025 completo.",
        "formula": (
            "rendimiento_sala(municipio) = admisiones(municipio, 2025) / salas_activas(municipio, 2025)\n"
            "captura_bruta = N_salas × rendimiento_sala(municipio)\n"
            "Luego la captura bruta se DESCOMPONE (no se escala) según el margen del mercado:\n"
            "  demanda_nueva = min(captura_bruta, demanda_insatisfecha_local)\n"
            "  redistribución = captura_bruta − demanda_nueva\n"
            "En mercados saturados (sin margen) la captura es 100% redistribución: se comunica "
            "así para no presentar redistribución como crecimiento."
        ),
        "supuestos": [
            "Una sala nueva rinde en promedio como las salas existentes del municipio (año 2025).",
            "En municipios sin salas se usa el rendimiento mediano de municipios comparables.",
        ],
        "limitaciones": [
            "No modela canibalización fina entre complejos ni el efecto de marca.",
            "En municipios sin salas se usa el rendimiento de municipios comparables "
            "por tamaño de población objetivo.",
        ],
    },
}
