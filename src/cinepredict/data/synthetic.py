"""Generador de datos SINTÉTICOS de exhibición cinematográfica (proxy de SIREC).

Mientras el SIREC real (que administra el equipo) se incorpora, este módulo
produce un dataset realista con la misma estructura esperada, para construir y
probar el pipeline completo de extremo a extremo.

Realismo incorporado:
  - **Concentración territorial**: solo los municipios con suficiente población
    15–44 tienen salas; el número de salas crece con la población (Bogotá/Medellín/
    Cali concentran la oferta), reproduciendo la brecha de acceso del Reto 8.
  - **Cadenas de exhibidores** (Cine Colombia, Cinemark, Royal Films, Procinal,
    Cinemateca/independiente) repartidas según el tamaño del mercado.
  - **Estacionalidad** mensual (vacaciones de enero, mitad de año y diciembre).
  - **Quiebre COVID** 2020-03 a 2020-12 (cierre casi total) y recuperación parcial
    en 2021 — se modelará luego como variable de intervención.
  - **Demanda ligada a la demografía**: admisiones ∝ población 15–44 del DANE.

Salida: `data/raw/sirec.parquet` con columnas
  municipio, departamento, exhibidor, sala, periodo (YYYY-MM), titulo, espectadores
(sin código DIVIPOLA: se reconcilia después contra el DANE, ejercitando esa etapa).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

from cinepredict.config import PROCESSED_DIR, RAW_DIR, REFERENCE_DIR

CADENAS = ["Cine Colombia", "Cinemark", "Royal Films", "Procinal", "Cinemateca/Independiente"]

TITULOS = [
    "Estreno Nacional", "Blockbuster Internacional", "Animación Familiar",
    "Cine Colombiano", "Drama de Autor", "Acción y Aventura", "Comedia",
]

# Estacionalidad mensual relativa (1.0 = promedio). Picos: ene, jun-jul, dic.
SEASONALITY = {1: 1.35, 2: 0.85, 3: 0.80, 4: 0.95, 5: 0.90, 6: 1.25,
               7: 1.30, 8: 0.95, 9: 0.80, 10: 0.90, 11: 1.00, 12: 1.45}


def _covid_factor(anio: int, mes: int) -> float:
    """Multiplicador por la pandemia (cierre de salas 2020 y recuperación 2021)."""
    if anio == 2020 and 3 <= mes <= 12:
        return 0.03 if mes <= 8 else 0.12
    if anio == 2021:
        return 0.45 + 0.04 * (mes - 1)  # de ~45% a ~90% durante el año
    return 1.0


def generate_sirec(
    start: str = "2016-01",
    end: str = "2024-12",
    seed: int = 42,
    annual_admissions_per_capita: float = 1.8,
) -> "pd.DataFrame":
    """Genera el dataset sintético y lo guarda en data/raw/sirec.parquet."""
    rng = np.random.default_rng(seed)

    divipola = pd.read_csv(REFERENCE_DIR / "divipola.csv", dtype={"cod_divipola": str})
    dane = pd.read_parquet(PROCESSED_DIR / "dane_poblacion.parquet")

    # Población 15–44 por municipio y año (para escalar la demanda)
    pob = dane.set_index(["cod_divipola", "anio"])["poblacion_15_44"].to_dict()

    # Población de referencia (2019) para decidir oferta de salas
    pob2019 = (dane[dane.anio == 2019].set_index("cod_divipola")["poblacion_15_44"]).to_dict()
    base = divipola.merge(
        dane[dane.anio == 2019][["cod_divipola", "poblacion_15_44"]], on="cod_divipola", how="left"
    ).dropna(subset=["poblacion_15_44"])

    # Oferta de salas ∝ población; umbral mínimo => concentración territorial
    def n_salas(p):
        if p < 25_000:
            return 0
        return int(np.clip(round(p / 40_000), 1, 120))

    base["num_salas"] = base["poblacion_15_44"].apply(n_salas)
    con_cine = base[base["num_salas"] > 0].copy()
    logger.info(f"Municipios con salas: {len(con_cine)} de {len(base)} "
                f"({100*len(con_cine)/len(base):.1f}%) — concentración territorial.")

    # Asignar cadenas y salas por municipio
    registros: list[dict] = []
    meses = pd.period_range(start=start, end=end, freq="M")

    for _, m in con_cine.iterrows():
        cod = m["cod_divipola"]
        municipio, departamento = m["municipio"], m["departamento"]
        salas_tot = int(m["num_salas"])
        # nº de cadenas presentes según tamaño del mercado
        n_cadenas = int(np.clip(1 + salas_tot // 8, 1, len(CADENAS)))
        cadenas = list(rng.choice(CADENAS, size=n_cadenas, replace=False))
        # repartir salas entre cadenas
        repart = rng.multinomial(salas_tot, np.ones(n_cadenas) / n_cadenas)
        repart = np.clip(repart, 1, None)

        # propensión local al cine (heterogeneidad municipal)
        propension = float(np.clip(rng.normal(annual_admissions_per_capita, 0.4), 0.6, 3.2))

        salas_def = []  # (exhibidor, sala_id, cuota)
        for cad, ns in zip(cadenas, repart):
            for k in range(int(ns)):
                salas_def.append((cad, f"{cad[:3].upper()}-{cod}-{k+1}"))

        for periodo in meses:
            anio, mes = periodo.year, periodo.month
            pobp = pob.get((cod, anio), m["poblacion_15_44"])
            # admisiones municipales del mes
            adm_muni = (pobp * propension / 12.0
                        * SEASONALITY[mes] * _covid_factor(anio, mes))
            if adm_muni <= 0:
                continue
            # repartir entre salas con ruido
            pesos = rng.dirichlet(np.ones(len(salas_def)) * 4)
            for (cad, sala_id), w in zip(salas_def, pesos):
                adm_sala = adm_muni * w * rng.normal(1.0, 0.10)
                if adm_sala < 1:
                    continue
                # repartir entre 2-4 títulos
                n_tit = rng.integers(2, 5)
                titulos = rng.choice(TITULOS, size=n_tit, replace=False)
                cuotas = rng.dirichlet(np.ones(n_tit) * 2)
                for tit, c in zip(titulos, cuotas):
                    esp = int(max(0, round(adm_sala * c)))
                    if esp <= 0:
                        continue
                    registros.append({
                        "municipio": municipio,
                        "departamento": departamento,
                        "exhibidor": cad,
                        "sala": sala_id,
                        "periodo": str(periodo),
                        "titulo": str(tit),
                        "espectadores": esp,
                    })

    df = pd.DataFrame.from_records(registros)
    out = RAW_DIR / "sirec.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.success(
        f"SIREC sintético: {len(df):,} filas · {df['sala'].nunique():,} salas · "
        f"{df['municipio'].nunique()} municipios · {df['periodo'].nunique()} meses -> {out}"
    )
    return df


if __name__ == "__main__":
    generate_sirec()
