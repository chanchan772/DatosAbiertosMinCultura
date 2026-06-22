"""Pruebas de la normalización territorial (no requieren datos descargados)."""

from cinepredict.data.territorial import normalize_name


def test_normalize_quita_tildes_y_mayusculas():
    assert normalize_name("Medellín") == "medellin"
    assert normalize_name("BOGOTÁ, D.C.") == "bogota, d.c."


def test_normalize_colapsa_espacios():
    assert normalize_name("  San   Andrés  ") == "san andres"


def test_normalize_maneja_no_str():
    assert normalize_name(None) == ""
    assert normalize_name(123) == ""
