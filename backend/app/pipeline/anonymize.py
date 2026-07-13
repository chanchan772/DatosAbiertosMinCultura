"""
anonymize.py — Pseudonimizacion por SEUDONIMOS SECUENCIALES.

Requisito del reto: anonimizar los datos de los Excel ANTES de procesarlos, sin
afectar el resultado analitico.

Tecnica: a cada entidad sensible (exhibidor, complejo) se le asigna un seudonimo
secuencial estable sin relacion con su nombre real (EXH-001, EXH-002, ... en
orden alfabetico). Propiedades:

  - IRREVERSIBLE desde el token: el seudonimo no deriva del nombre (no es un hash
    del texto), de modo que NO se puede reidentificar por fuerza bruta aunque el
    universo sea pequeno (a diferencia de un HMAC del nombre). La unica
    correspondencia token->real vive en data/private/ y no se publica.
  - Determinista: el orden alfabetico fija el mismo token en cada corrida, por lo
    que TODA agregacion da exactamente el mismo numero que con el nombre real.
    No afecta ningun resultado.

Uso: registrar todos los valores (register_series) de todas las tablas, llamar a
finalize() y luego tokenize_series() por columna.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..config import DATA_PRIVATE


class Pseudonymizer:
    def __init__(self) -> None:
        self._values: dict[str, set[str]] = {}
        self.token_map: dict[str, dict[str, str]] = {}   # prefix -> {real: token}
        self.mapping: dict[str, dict[str, str]] = {}      # prefix -> {token: real}

    def register_series(self, s: pd.Series, prefix: str) -> None:
        vals = self._values.setdefault(prefix, set())
        for v in s.dropna().astype(str):
            v = v.strip()
            if v:
                vals.add(v)

    def finalize(self) -> None:
        for prefix, vals in self._values.items():
            tm, inv = {}, {}
            for i, real in enumerate(sorted(vals), 1):
                tok = f"{prefix}-{i:03d}"
                tm[real] = tok
                inv[tok] = real
            self.token_map[prefix] = tm
            self.mapping[prefix] = inv

    def tokenize_series(self, s: pd.Series, prefix: str) -> pd.Series:
        tm = self.token_map.get(prefix, {})
        return s.astype(str).str.strip().map(lambda v: tm.get(v, f"{prefix}-NA"))

    def save_mapping(self, name: str = "anon_mapping.json") -> Path:
        path = DATA_PRIVATE / name
        path.write_text(json.dumps(self.mapping, ensure_ascii=False, indent=2), encoding="utf-8")
        (DATA_PRIVATE / "anon_summary.json").write_text(
            json.dumps({p: len(m) for p, m in self.mapping.items()}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # aviso de privacidad junto al mapeo
        (DATA_PRIVATE / "LEEME_PRIVADO.txt").write_text(
            "Este directorio contiene la correspondencia seudonimo->nombre real.\n"
            "NO debe versionarse ni distribuirse (ver .gitignore).\n", encoding="utf-8")
        return path
