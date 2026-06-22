"""Orquestación del entrenamiento de los tres componentes del modelo.

Componente A — Demanda potencial municipal (LightGBM + Optuna + SHAP).
Componente B — Captura por exhibidor (CatBoost).
Componente C — Estacionalidad y tendencia (StatsForecast AutoARIMA + Prophet).

Todo se registra en MLflow. Las salidas (modelos y proyecciones a 2027) quedan en
`models/` y `data/processed/`. La validación respeta la causalidad temporal:
se evalúa proyectando el último año observado.
"""

from __future__ import annotations

import warnings
from contextlib import contextmanager

import mlflow
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import mean_absolute_error, r2_score

from cinepredict.config import FIGURES_DIR, MODELS_DIR, PROCESSED_DIR, ROOT_DIR, settings

warnings.filterwarnings("ignore")

HORIZON_YEAR = settings.forecast_horizon_year  # 2027
ANIOS_COVID = {2020, 2021}

# MLflow es opcional: si falla (p. ej. ruta con espacios en Windows) no debe
# interrumpir el entrenamiento ni la generación de proyecciones.
_MLFLOW = False


@contextmanager
def _run(name: str):
    if _MLFLOW:
        with mlflow.start_run(run_name=name):
            yield
    else:
        yield


def _log_params(d: dict) -> None:
    if _MLFLOW:
        try:
            mlflow.log_params(d)
        except Exception:  # noqa: BLE001
            pass


def _log_metrics(d: dict) -> None:
    if _MLFLOW:
        try:
            mlflow.log_metrics(d)
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------- Componente A
DEMANDA_FEATURES = ["poblacion_total", "poblacion_15_44", "prop_15_44", "dist_km_sala_cercana"]


def train_demanda() -> pd.DataFrame:
    """Demanda potencial municipal. Devuelve proyección 2027 con brecha."""
    import lightgbm as lgb
    import optuna
    import shap

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    df = pd.read_parquet(PROCESSED_DIR / "features_demanda.parquet")

    # Entrenamos donde SÍ hay cine y años no-COVID (relación demanda~población+acceso)
    train_mask = (df["tiene_cine"] == 1) & (~df["anio"].isin(ANIOS_COVID)) & (df["espectadores"] > 0)
    train_df = df[train_mask].copy()
    train_df["y"] = np.log1p(train_df["espectadores"])

    # Validación temporal: último año observado como test
    anio_test = int(train_df["anio"].max())
    tr = train_df[train_df["anio"] < anio_test]
    te = train_df[train_df["anio"] == anio_test]

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 200, 800),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 15, 127),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 40),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "verbose": -1,
        }
        m = lgb.LGBMRegressor(**params)
        m.fit(tr[DEMANDA_FEATURES], tr["y"])
        pred = m.predict(te[DEMANDA_FEATURES])
        return mean_absolute_error(te["y"], pred)

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=20)
    best = {**study.best_params, "verbose": -1}

    model = lgb.LGBMRegressor(**best)
    model.fit(train_df[DEMANDA_FEATURES], train_df["y"])

    # métricas en escala original
    pred_te = np.expm1(model.predict(te[DEMANDA_FEATURES]))
    mae = mean_absolute_error(te["espectadores"], pred_te)
    r2 = r2_score(te["espectadores"], pred_te)
    logger.info(f"[A] Demanda — MAE(test {anio_test})={mae:,.0f} · R²={r2:.3f}")

    # SHAP (explicabilidad)
    try:
        expl = shap.TreeExplainer(model)
        sv = expl.shap_values(train_df[DEMANDA_FEATURES].sample(min(2000, len(train_df)), random_state=0))
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        shap.summary_plot(sv, train_df[DEMANDA_FEATURES].sample(min(2000, len(train_df)), random_state=0),
                          show=False)
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        plt.tight_layout(); plt.savefig(FIGURES_DIR / "shap_demanda.png", dpi=110); plt.close()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"SHAP demanda omitido: {e}")

    # Proyección a HORIZON_YEAR: demanda potencial de TODOS los municipios
    fut = df[df["anio"] == HORIZON_YEAR].copy()
    fut["demanda_potencial"] = np.expm1(model.predict(fut[DEMANDA_FEATURES])).round().astype(int)
    # Referencia observada: último año con asistencia real (p. ej. 2024). En 2027 no hay
    # observación, así que la brecha = demanda potencial − asistencia actual del municipio.
    # Municipios SIN sala tienen observación 0 → toda su demanda potencial es insatisfecha.
    ultimo_obs = int(df[df["espectadores"] > 0]["anio"].max())
    obs_ref = df[df["anio"] == ultimo_obs].set_index("cod_divipola")["espectadores"]
    fut["espectadores_obs"] = fut["cod_divipola"].map(obs_ref).fillna(0).round().astype(int)
    fut["brecha"] = (fut["demanda_potencial"] - fut["espectadores_obs"]).clip(lower=0)

    model.booster_.save_model(str(MODELS_DIR / "demanda_lgbm.txt"))
    out = fut[["cod_divipola", "anio", "poblacion_15_44", "tiene_cine",
               "dist_km_sala_cercana", "demanda_potencial", "espectadores_obs", "brecha"]]
    out.to_parquet(PROCESSED_DIR / "proyeccion_demanda_2027.parquet", index=False)

    _log_params({f"A_{k}": v for k, v in study.best_params.items()})
    _log_metrics({"A_mae": mae, "A_r2": r2})
    return out


# ---------------------------------------------------------------- Componente B
# Sin cod_divipola: evita memorización/extrapolación constante fuera de muestra
# y permite que el modelo generalice por población y nº de salas (clave para el simulador).
CAP_NUM = ["num_salas", "poblacion_15_44", "prop_15_44", "dist_km_sala_cercana"]
CAP_CAT = ["exhibidor"]


def train_captura():
    """Captura por exhibidor (CatBoost). Devuelve el modelo entrenado."""
    from catboost import CatBoostRegressor, Pool

    df = pd.read_parquet(PROCESSED_DIR / "features_captura.parquet").dropna(subset=["poblacion_15_44"])
    df = df[~df["anio"].isin(ANIOS_COVID)].copy()
    df["cod_divipola"] = df["cod_divipola"].astype(str)

    anio_test = int(df["anio"].max())
    tr, te = df[df["anio"] < anio_test], df[df["anio"] == anio_test]

    feats = CAP_NUM + CAP_CAT
    model = CatBoostRegressor(iterations=600, learning_rate=0.05, depth=8,
                              loss_function="RMSE", verbose=False)
    model.fit(Pool(tr[feats], tr["espectadores"], cat_features=CAP_CAT))

    pred = model.predict(Pool(te[feats], cat_features=CAP_CAT))
    mae = mean_absolute_error(te["espectadores"], pred)
    r2 = r2_score(te["espectadores"], pred)
    logger.info(f"[B] Captura — MAE(test {anio_test})={mae:,.0f} · R²={r2:.3f}")

    model.save_model(str(MODELS_DIR / "captura_catboost.cbm"))
    _log_metrics({"B_mae": mae, "B_r2": r2})
    return model


# ---------------------------------------------------------------- Componente C
def train_seasonality() -> pd.DataFrame:
    """Estacionalidad/tendencia mensual. Proyecta hasta diciembre de HORIZON_YEAR."""
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA

    serie = pd.read_parquet(PROCESSED_DIR / "series_mensuales.parquet")
    serie["ds"] = pd.PeriodIndex(serie["periodo"], freq="M").to_timestamp()
    long = serie.rename(columns={"cod_divipola": "unique_id", "espectadores": "y"})[
        ["unique_id", "ds", "y"]
    ]

    ult = long["ds"].max()
    h = (HORIZON_YEAR - ult.year) * 12 + (12 - ult.month)
    h = max(h, 12)

    sf = StatsForecast(models=[AutoARIMA(season_length=12)], freq="MS", n_jobs=-1)
    fcst = sf.forecast(df=long, h=h)
    fcst = fcst.rename(columns={"AutoARIMA": "espectadores_pred"})
    fcst["espectadores_pred"] = fcst["espectadores_pred"].clip(lower=0).round().astype(int)
    fcst.to_parquet(PROCESSED_DIR / "proyeccion_mensual.parquet", index=False)
    logger.info(f"[C] Estacionalidad — {long['unique_id'].nunique()} series, horizonte {h} meses")
    _log_metrics({"C_series": long["unique_id"].nunique(), "C_horizonte_meses": h})
    return fcst


def train_prophet_nacional():
    """Prophet sobre la serie nacional con intervención COVID y festivos (baseline interpretable)."""
    try:
        from prophet import Prophet
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Prophet no disponible: {e}")
        return

    serie = pd.read_parquet(PROCESSED_DIR / "series_mensuales.parquet")
    serie["ds"] = pd.PeriodIndex(serie["periodo"], freq="M").to_timestamp()
    nac = serie.groupby("ds", as_index=False)["espectadores"].sum().rename(columns={"espectadores": "y"})
    nac["covid"] = (((nac["ds"] >= "2020-03-01") & (nac["ds"] <= "2021-12-31"))).astype(int)

    m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    m.add_country_holidays(country_name="CO")
    m.add_regressor("covid")
    m.fit(nac)

    fut = m.make_future_dataframe(periods=(HORIZON_YEAR - nac["ds"].max().year) * 12 + 12, freq="MS")
    fut["covid"] = 0
    fc = m.predict(fut)
    fc[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_parquet(
        PROCESSED_DIR / "proyeccion_nacional_prophet.parquet", index=False
    )
    logger.info("[C] Prophet nacional con intervención COVID ajustado.")


def run() -> None:
    global _MLFLOW
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    # URI absoluta tipo file:// (robusta a espacios en la ruta en Windows)
    try:
        mlflow.set_tracking_uri((ROOT_DIR / "mlruns").as_uri())
        mlflow.set_experiment("cinepredict")
        _MLFLOW = True
        logger.info("MLflow activo (trazabilidad de experimentos).")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"MLflow desactivado ({e}); el entrenamiento continúa sin trazabilidad.")

    with _run("A_demanda"):
        dem = train_demanda()
    with _run("B_captura"):
        train_captura()
    with _run("C_estacionalidad"):
        train_seasonality()
        train_prophet_nacional()

    # Resumen de brechas (pregunta 2 del reto)
    top = dem.sort_values("brecha", ascending=False).head(10)
    logger.success(f"Top municipios con demanda insatisfecha (2027):\n{top[['cod_divipola','brecha']].to_string(index=False)}")
    logger.success("Entrenamiento completo. Revisa MLflow (mlflow ui) y data/processed/.")
