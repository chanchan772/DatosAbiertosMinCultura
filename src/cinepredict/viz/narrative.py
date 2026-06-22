"""Narrativas automáticas con la API de Claude.

Genera resúmenes en lenguaje natural de las proyecciones por territorio para
facilitar la apropiación por tomadores de decisión sin perfil técnico. Se invoca
desde el tablero Streamlit.
"""

from __future__ import annotations

from cinepredict.config import settings

PROMPT_SISTEMA = (
    "Eres un analista del Ministerio de las Culturas de Colombia. Resume "
    "proyecciones de asistencia a cine en lenguaje claro para tomadores de "
    "decisión, sin jerga técnica, destacando brechas territoriales y "
    "oportunidades de fomento a la exhibición regional (Ley 814 de 2003)."
)


def narrar_proyeccion(resumen_datos: str) -> str:
    """Devuelve una narrativa breve a partir de un resumen estructurado de datos."""
    if not settings.anthropic_api_key:
        return "(Configura ANTHROPIC_API_KEY en .env para habilitar narrativas automáticas.)"

    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=600,
        system=PROMPT_SISTEMA,
        messages=[{"role": "user", "content": resumen_datos}],
    )
    return "".join(block.text for block in msg.content if block.type == "text")
