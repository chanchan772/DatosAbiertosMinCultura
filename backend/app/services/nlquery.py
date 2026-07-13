"""
nlquery.py — Consultas en lenguaje natural sobre los datos (DeepSeek).

Estrategia (RAG curado): se arma un CONTEXTO compacto con los hechos clave ya
calculados por los modelos (panorama, demanda insatisfecha, proyección 2027,
metodología) y se entrega a DeepSeek con la instrucción de responder ÚNICAMENTE a
partir de ese contexto. Es transparente y seguro: el modelo no inventa cifras ni
ejecuta consultas arbitrarias, solo interpreta datos verificados.
"""
from __future__ import annotations

import json

import requests

from ..config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from ..models import overview, demand, forecast
from ..models.methodology import METODOLOGIA

SYSTEM = (
    "Eres el asistente analítico de CinePredict, un tablero del Ministerio de las Culturas de "
    "Colombia sobre asistencia y acceso al cine (fuentes SIREC y DANE). Respondes preguntas en "
    "lenguaje natural.\n"
    "REGLAS ESTRICTAS:\n"
    "1) Usa ÚNICAMENTE las cifras del JSON de contexto que se te entrega. NO inventes datos.\n"
    "2) Si la respuesta no está en el contexto, dilo claramente y sugiere qué módulo del tablero "
    "consultar.\n"
    "3) Cita las cifras concretas y, cuando aplique, aclara el año (taquilla 2026 es parcial; la "
    "demanda usa 2025).\n"
    "4) Los exhibidores están anonimizados (EXH-###); no inventes nombres reales.\n"
    "5) Responde en español, claro y conciso (máx. ~180 palabras), apto para tomadores de "
    "decisión. Cuando ayude, usa una lista corta."
)


def build_context(banda: str = "pob_15_45") -> dict:
    ov = overview.compute()
    dm = demand.compute(banda=banda)
    fc = forecast.compute()
    mes_pico = max(fc["factores_estacionales"], key=lambda x: x["factor"])
    return {
        "descripcion": "Consumo y acceso al cine en Colombia. Taquilla detallada 2026 (parcial, "
                       "corte mayo); serie diaria 2007-2026; demanda con año de referencia 2025; "
                       "población objetivo por banda de edad (DANE).",
        "panorama_nacional": {
            "admisiones_2026_parcial": ov["kpis"]["admisiones_total"],
            "salas_activas": ov["kpis"]["salas"], "complejos": ov["kpis"]["complejos"],
            "exhibidores": ov["kpis"]["exhibidores"],
            "municipios_con_cine": ov["kpis"]["municipios"], "total_municipios_pais": 1122,
            "concentracion": ov["concentracion"],
            "por_genero": ov["por_genero"], "por_nacion": ov["por_nacion"],
            "top_municipios": ov["top_municipios"], "top_exhibidores": ov["top_exhibidores"],
            "asistencia_anual": ov["serie_anual"],
        },
        "demanda_insatisfecha": {
            "banda_edad": banda, "tasa_referencia_per_capita": dm["parametros"]["tasa_referencia"],
            "totales": dm["totales"], "resumen_por_clase": dm["resumen_por_clase"],
            "top_municipios_insatisfecha": dm["top_insatisfecha"][:15],
        },
        "proyeccion_2027": {
            "central": fc["tendencia_anual_proyectada"], "escenarios": fc["escenarios"],
            "intervalo": fc["intervalo"], "backtest": fc["backtest"],
            "mes_pico": mes_pico, "factores_estacionales": fc["factores_estacionales"],
        },
        "metodologia": {k: {"pregunta": v["pregunta"], "formula": v["formula"]}
                        for k, v in METODOLOGIA.items()},
    }


def answer(pregunta: str, context: dict | None = None, banda: str = "pob_15_45",
           timeout: int = 45) -> dict:
    ctx = context if context is not None else build_context(banda)
    user = (f"Pregunta del usuario: {pregunta}\n\n"
            f"Contexto de datos (JSON):\n{json.dumps(ctx, ensure_ascii=False, default=str)}")
    try:
        r = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": DEEPSEEK_MODEL,
                  "messages": [{"role": "system", "content": SYSTEM},
                               {"role": "user", "content": user}],
                  "temperature": 0.2, "max_tokens": 600, "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        return {"respuesta": data["choices"][0]["message"]["content"].strip(),
                "fuente": "deepseek", "modelo": data.get("model", DEEPSEEK_MODEL)}
    except Exception as e:
        return {"respuesta": "No fue posible consultar el modelo en este momento. "
                             "Intenta de nuevo o revisa los módulos del tablero.",
                "fuente": "error", "modelo": None, "error": str(e)}


INTERPRET_SYSTEM = (
    "Eres analista de datos del Ministerio de las Culturas de Colombia. Te entregan los datos de "
    "UN módulo del tablero CinePredict (asistencia y acceso al cine). Redacta una INTERPRETACIÓN "
    "DETALLADA, LARGA y ROBUSTA de esos datos, en español, pensada para CUALQUIER TIPO DE PÚBLICO "
    "(ciudadanía, gestores culturales, tomadores de decisión): sin tecnicismos, y cuando uses un "
    "término técnico, explícalo en palabras simples.\n"
    "ESTRUCTURA (usa subtítulos en negrita con Markdown):\n"
    "**En pocas palabras** — 2-3 frases que resuman lo esencial.\n"
    "**Qué muestran los datos** — describe las cifras clave en lenguaje cotidiano, con ejemplos y "
    "comparaciones que ayuden a dimensionarlas.\n"
    "**Hallazgos principales** — lista de 3 a 6 patrones importantes, cada uno con su cifra.\n"
    "**Qué significa para el país** — implicaciones para el acceso a la cultura y para la política "
    "pública de fomento (Ley 814 de 2003), de forma concreta.\n"
    "**Matices y límites** — qué NO se puede concluir y por qué (honestidad analítica).\n"
    "REGLAS: usa ÚNICAMENTE las cifras del JSON (no inventes ni estimes). Sé claro, pedagógico y "
    "concreto. Extensión objetivo: 350-600 palabras. Los exhibidores están anonimizados (EXH-###)."
)

MODULO_DESC = {
    "panorama": "Panorama nacional: magnitud, evolución histórica y concentración del consumo.",
    "brechas": "Mapa de brechas: demanda potencial vs. atendida y municipios con demanda insatisfecha.",
    "simulador": "Simulación de un exhibidor hipotético en un municipio (captura, demanda nueva vs redistribución).",
    "proyeccion": "Estacionalidad y proyección de asistencia a 2027 (escenarios y validación).",
    "catalogo": "Catálogo de datos: fuentes, procedencia, anonimización y reconciliación territorial.",
    "metodologia": "Metodología: preguntas, fórmulas, supuestos y limitaciones de cada modelo.",
}


def interpret_module(modulo: str, datos: dict, timeout: int = 60) -> dict:
    """Interpretación larga y accesible de los datos de un módulo."""
    desc = MODULO_DESC.get(modulo, modulo)
    user = (f"Módulo: {desc}\n\nDatos del módulo (JSON):\n"
            f"{json.dumps(datos, ensure_ascii=False, default=str)}")
    try:
        r = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": DEEPSEEK_MODEL,
                  "messages": [{"role": "system", "content": INTERPRET_SYSTEM},
                               {"role": "user", "content": user}],
                  "temperature": 0.35, "max_tokens": 1300, "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        return {"interpretacion": data["choices"][0]["message"]["content"].strip(),
                "fuente": "deepseek", "modelo": data.get("model", DEEPSEEK_MODEL)}
    except Exception as e:
        return {"interpretacion": "No fue posible generar la interpretación en este momento.",
                "fuente": "error", "modelo": None, "error": str(e)}


if __name__ == "__main__":
    print(answer("¿Cuáles son los 3 municipios con mayor demanda insatisfecha y por qué?"))

