"""Pruebas de la variable de intervención COVID (sin dependencias de datos)."""

import pandas as pd

from cinepredict.models.seasonality import add_covid_intervention


def test_covid_marca_periodo_correcto():
    df = pd.DataFrame({"ds": pd.to_datetime(["2019-06-01", "2020-06-01", "2022-06-01"])})
    out = add_covid_intervention(df)
    assert out.loc[0, "covid"] == 0  # antes
    assert out.loc[1, "covid"] == 1  # durante
    assert out.loc[2, "covid"] == 0  # después
