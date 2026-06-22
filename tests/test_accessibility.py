"""Pruebas de las variables de accesibilidad (Haversine)."""

import pandas as pd

from cinepredict.features.accessibility import _haversine_matrix, distancia_a_sala_cercana


def test_haversine_distancia_conocida():
    # Bogotá (4.61, -74.08) a Medellín (6.25, -75.56): distancia en línea recta ~245 km
    import numpy as np
    d = _haversine_matrix(np.array([4.61]), np.array([-74.08]),
                          np.array([6.25]), np.array([-75.56]))[0, 0]
    assert 230 < d < 260


def test_municipio_con_cine_tiene_distancia_cero():
    div = pd.DataFrame({
        "cod_divipola": ["05001", "05002", "11001"],
        "lat": [6.25, 5.78, 4.61], "lon": [-75.56, -75.42, -74.08],
    })
    res = distancia_a_sala_cercana(div, municipios_con_cine={"05001"})
    fila = res.set_index("cod_divipola")
    assert fila.loc["05001", "dist_km_sala_cercana"] == 0.0
    assert fila.loc["05001", "tiene_cine"] == 1
    assert fila.loc["05002", "dist_km_sala_cercana"] > 0
