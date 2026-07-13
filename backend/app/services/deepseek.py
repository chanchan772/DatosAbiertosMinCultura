"""
deepseek.py — Cliente de DeepSeek para narrativas automáticas.

Genera resúmenes en lenguaje natural (español) de las proyecciones por territorio,
ANCLADOS a las cifras ya calculadas por los modelos. El prompt instruye al modelo
a NO inventar datos: solo redacta e interpreta los números que se le entregan.
Si el servicio no está disponible, devuelve una narrativa de respaldo generada
localmente a partir de las mismas cifras (el tablero nunca queda sin texto).
"""
from __future__ import annotations

import json

import requests

from ..config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

SYSTEM_PROMPT = (
    "Eres analista de datos del Ministerio de las Culturas de Colombia. Redactas "
    "resúmenes ejecutivos claros y honestos para tomadores de decisión SIN perfil "
    "técnico. Reglas estrictas: (1) usa ÚNICAMENTE las cifras del JSON que se te "
    "entrega; NO inventes ni estimes datos nuevos. (2) Sé conciso (máx. 140 palabras). "
    "(3) Explica qué significan las cifras y una recomendación de política pública. "
    "(4) Si una cifra es una demanda insatisfecha, aclara que es una estimación de "
    "residentes potenciales, no una certeza. (5) No uses tecnicismos innecesarios."
)


def _fallback(contexto: dict) -> str:
    m = contexto.get("municipio", "el territorio")
    ins = contexto.get("demanda_insatisfecha")
    clase = contexto.get("etiqueta_clase") or contexto.get("clase", "")
    partes = [f"Resumen de {m}."]
    if ins is not None:
        partes.append(f"Se estima una demanda insatisfecha de ~{ins:,.0f} espectadores/año "
                      f"({clase}).")
    if contexto.get("demanda_potencial") and contexto.get("demanda_realizada") is not None:
        partes.append(f"Potencial {contexto['demanda_potencial']:,.0f} vs. realizada "
                      f"{contexto['demanda_realizada']:,.0f}.")
    partes.append("Cifra estimada sobre residentes; verificar acceso a municipios vecinos "
                  "antes de decidir inversión.")
    return " ".join(partes)


def generar_narrativa(contexto: dict, tipo: str = "territorio",
                      timeout: int = 40) -> dict:
    """Devuelve {'narrativa': str, 'fuente': 'deepseek'|'fallback', 'modelo': str}."""
    instruccion = {
        "territorio": "Redacta un resumen ejecutivo del estado de acceso al cine en este "
                      "municipio y una recomendación.",
        "nacional": "Redacta un resumen del panorama nacional de asistencia al cine y la "
                    "principal brecha identificada.",
        "simulacion": "Interpreta el resultado de la simulación de un exhibidor hipotético: "
                      "cuánto captaría y si es demanda nueva o redistribución.",
    }.get(tipo, "Redacta un resumen ejecutivo.")

    user_content = (
        f"{instruccion}\n\nDatos (JSON):\n"
        f"{json.dumps(contexto, ensure_ascii=False, default=str)}"
    )
    try:
        r = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                     "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.3,
                "max_tokens": 320,
                "stream": False,
            },
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        texto = data["choices"][0]["message"]["content"].strip()
        return {"narrativa": texto, "fuente": "deepseek",
                "modelo": data.get("model", DEEPSEEK_MODEL)}
    except Exception as e:
        return {"narrativa": _fallback(contexto), "fuente": "fallback",
                "modelo": None, "error": str(e)}


if __name__ == "__main__":
    ctx = {"municipio": "Riohacha", "clase": "subatendido",
           "demanda_potencial": 324112, "demanda_realizada": 155449,
           "demanda_insatisfecha": 168663}
    print(generar_narrativa(ctx, "territorio"))
