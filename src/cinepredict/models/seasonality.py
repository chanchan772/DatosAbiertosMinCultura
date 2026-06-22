"""Componente C — Estacionalidad y tendencia (series de tiempo).

Modela la dinámica mensual de asistencia por territorio para desagregar las
proyecciones anuales mes a mes, capturando vacaciones, estrenos y festivos
colombianos. El quiebre 2020-2021 (COVID-19) se incorpora como variable de
intervención (regresor exógeno binario).

Se usa StatsForecast (SARIMAX/AutoARIMA) para cientos de series municipales en
paralelo, con Prophet como baseline interpretable.
"""

from __future__ import annotations

import pandas as pd

from cinepredict.config import settings


def add_covid_intervention(df: pd.DataFrame, date_col: str = "ds") -> pd.DataFrame:
    """Añade el regresor binario `covid` para el periodo de cierre de salas."""
    df = df.copy()
    start = pd.Period(settings.covid_break_start, freq="M").to_timestamp()
    end = pd.Period(settings.covid_break_end, freq="M").to_timestamp(how="end")
    fechas = pd.to_datetime(df[date_col])
    df["covid"] = ((fechas >= start) & (fechas <= end)).astype(int)
    return df


def to_long_format(analytic: pd.DataFrame) -> pd.DataFrame:
    """Convierte la tabla analítica al formato largo de Nixtla (unique_id, ds, y)."""
    df = analytic.copy()
    df["ds"] = pd.PeriodIndex(df["periodo"], freq="M").to_timestamp()
    long = (
        df.groupby(["cod_divipola", "ds"], as_index=False)["espectadores"]
        .sum()
        .rename(columns={"cod_divipola": "unique_id", "espectadores": "y"})
    )
    return add_covid_intervention(long)


def fit_forecast(long_df: pd.DataFrame, horizon_months: int = 24):
    """Ajusta SARIMAX por serie y proyecta `horizon_months` hacia adelante."""
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA

    sf = StatsForecast(models=[AutoARIMA(season_length=12)], freq="MS", n_jobs=-1)
    sf.fit(long_df[["unique_id", "ds", "y"]])
    return sf.predict(h=horizon_months)
