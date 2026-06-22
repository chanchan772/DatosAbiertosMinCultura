"""Narrativas territoriales — IA por API con respaldo sin costo.

Diseño "a prueba de créditos":
  1. Si hay un proveedor de IA configurado (Anthropic, o cualquiera compatible con
     OpenAI como Groq/Gemini/OpenRouter/Ollama), genera la narrativa con el LLM.
  2. Si NO hay clave, cae a un **resumen determinístico por plantilla** (sin costo),
     claramente etiquetado, para que la página nunca quede vacía.

Variables de entorno relevantes (ver .env.example):
  ANTHROPIC_API_KEY / ANTHROPIC_MODEL            → Claude
  LLM_BASE_URL / LLM_API_KEY / LLM_MODEL         → cualquier API compatible OpenAI
                                                   (Groq, Gemini, OpenRouter, Ollama…)
"""

from __future__ import annotations

import os

from cinepredict.config import settings

PROMPT_SISTEMA = (
    "Eres analista del Ministerio de las Culturas de Colombia. Resume proyecciones "
    "de asistencia a cine en lenguaje claro para tomadores de decisión, sin jerga "
    "técnica, destacando brechas territoriales y oportunidades de fomento a la "
    "exhibición regional (Ley 814 de 2003). Máximo 130 palabras."
)


def _prompt_usuario(ctx: dict) -> str:
    top = ", ".join(f"{m} ({int(b):,})" for m, b in ctx.get("top", []))
    return (
        f"Departamento: {ctx['departamento']}. Municipios con salas de cine: "
        f"{ctx['con_cine']}. Municipios sin salas: {ctx['sin_cine']}. Demanda "
        f"insatisfecha proyectada a 2027: {ctx['brecha_total']:,} espectadores. "
        f"Municipios con mayor demanda insatisfecha: {top}."
    )


def _via_anthropic(ctx: dict) -> str | None:
    if not settings.anthropic_api_key:
        return None
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=settings.anthropic_model, max_tokens=400,
        system=PROMPT_SISTEMA, messages=[{"role": "user", "content": _prompt_usuario(ctx)}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


def _via_openai_compatible(ctx: dict) -> str | None:
    """Cualquier proveedor compatible con OpenAI (Groq, Gemini, OpenRouter, Ollama)."""
    base_url = os.getenv("LLM_BASE_URL")
    api_key = os.getenv("LLM_API_KEY", "ollama")  # Ollama no exige clave real
    model = os.getenv("LLM_MODEL")
    if not base_url or not model:
        return None
    try:
        from openai import OpenAI
    except Exception:  # noqa: BLE001
        return None
    client = OpenAI(base_url=base_url, api_key=api_key)
    resp = client.chat.completions.create(
        model=model, max_tokens=400,
        messages=[{"role": "system", "content": PROMPT_SISTEMA},
                  {"role": "user", "content": _prompt_usuario(ctx)}],
    )
    return resp.choices[0].message.content


def _por_plantilla(ctx: dict) -> str:
    """Resumen determinístico sin LLM (costo cero, siempre disponible)."""
    dep = ctx["departamento"]
    con, sin = ctx["con_cine"], ctx["sin_cine"]
    brecha = ctx["brecha_total"]
    top = ctx.get("top", [])
    total = con + sin
    cobertura = (con / total * 100) if total else 0
    lider = top[0][0] if top else "varios municipios"
    nombres = ", ".join(m for m, _ in top[:3]) if top else "—"
    return (
        f"En **{dep}**, {con} de {total} municipios ({cobertura:.0f}%) cuentan hoy con "
        f"salas de cine, mientras que **{sin} municipios no tienen oferta**. El modelo "
        f"proyecta para 2027 una **demanda insatisfecha de {brecha:,} espectadores** "
        f"concentrada en territorios sin sala, encabezados por **{lider}**. "
        f"Municipios prioritarios para fomentar la exhibición ({nombres}) concentran el "
        f"mayor público desatendido. Estos resultados orientan la focalización de los "
        f"instrumentos de fomento a la exhibición regional previstos en la Ley 814 de 2003, "
        f"acercando la oferta cultural a la población que hoy no accede al cine."
    )


def narrar_territorio(ctx: dict) -> tuple[str, str]:
    """Devuelve (texto, fuente). fuente ∈ {'Claude', 'LLM externo', 'plantilla'}."""
    try:
        t = _via_anthropic(ctx)
        if t:
            return t, "Claude (Anthropic)"
    except Exception:  # noqa: BLE001
        pass
    try:
        t = _via_openai_compatible(ctx)
        if t:
            return t, "LLM externo (API compatible)"
    except Exception:  # noqa: BLE001
        pass
    return _por_plantilla(ctx), "plantilla (sin costo)"


# --- Compatibilidad con la versión anterior (recibe texto) ---
def narrar_proyeccion(resumen_datos: str) -> str:
    if not settings.anthropic_api_key:
        return "(Configura una clave de IA o usa la narrativa por plantilla.)"
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=settings.anthropic_model, max_tokens=400,
        system=PROMPT_SISTEMA, messages=[{"role": "user", "content": resumen_datos}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")
