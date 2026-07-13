"""
trace.py — Traza de calculo auditable ("¿Como se calcula?").

Cada modelo construye una CalculationTrace registrando: fuentes de datos usadas,
supuestos, y CADA paso aritmetico con su formula simbolica, los valores de
entrada y el resultado. El tablero renderiza esta traza para que los jurados
puedan reconstruir a mano cualquier cifra. Es el mecanismo central de
transparencia del proyecto.
"""
from __future__ import annotations

from typing import Any


class CalculationTrace:
    def __init__(self, titulo: str, descripcion: str = "") -> None:
        self.titulo = titulo
        self.descripcion = descripcion
        self.fuentes: list[dict] = []
        self.supuestos: list[str] = []
        self.pasos: list[dict] = []
        self.limitaciones: list[str] = []

    def fuente(self, nombre: str, origen: str, detalle: str = "") -> "CalculationTrace":
        """Registra una fuente de datos (con su procedencia exacta)."""
        self.fuentes.append({"nombre": nombre, "origen": origen, "detalle": detalle})
        return self

    def supuesto(self, texto: str) -> "CalculationTrace":
        self.supuestos.append(texto)
        return self

    def limitacion(self, texto: str) -> "CalculationTrace":
        self.limitaciones.append(texto)
        return self

    def paso(
        self,
        nombre: str,
        formula: str,
        entradas: dict[str, Any] | None = None,
        resultado: Any = None,
        unidad: str = "",
        nota: str = "",
    ) -> Any:
        """Registra un paso de calculo y DEVUELVE el resultado (para encadenar).

        formula: expresion legible, p.ej. "potencial = poblacion_15_45 x tasa_ref"
        entradas: {nombre_variable: valor} con los numeros concretos usados.
        """
        self.pasos.append({
            "n": len(self.pasos) + 1,
            "nombre": nombre,
            "formula": formula,
            "entradas": _round_dict(entradas or {}),
            "resultado": _round_val(resultado),
            "unidad": unidad,
            "nota": nota,
        })
        return resultado

    def to_dict(self) -> dict:
        return {
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "fuentes": self.fuentes,
            "supuestos": self.supuestos,
            "pasos": self.pasos,
            "limitaciones": self.limitaciones,
        }


def _round_val(v: Any) -> Any:
    if isinstance(v, float):
        return round(v, 4)
    return v


def _round_dict(d: dict) -> dict:
    return {k: _round_val(v) for k, v in d.items()}
