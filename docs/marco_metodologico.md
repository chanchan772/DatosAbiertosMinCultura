# Marco metodológico

El proyecto prioriza **modelos interpretables y auditables** sobre cajas negras: cada cifra del
tablero expone su fórmula, sus entradas y su resultado paso a paso (panel "¿Cómo se calcula?").
Todos los parámetros que afectan resultados viven en un único archivo
(`backend/app/models/methodology.py`).

## Tipo de análisis

**Mixto — descriptivo + predictivo:**
- **Descriptivo:** panorama nacional, concentración territorial y empresarial, distribuciones.
- **Predictivo (regresión):** demanda potencial municipal, captura por exhibidor, y proyección de
  series de tiempo a 2027.

## 1. Demanda potencial e insatisfecha

```
demanda_potencial(m) = poblacion_objetivo(m) × tasa_referencia
```

- `poblacion_objetivo(m)`: población del municipio en la banda de edad de mayor propensión a
  asistir (15–30, 15–45 o 15–60 años, proyecciones DANE).
- `tasa_referencia`: promedio **ponderado por población** de admisiones/habitante en los
  municipios **con oferta**, **excluyendo los polos de atracción** (tasa por encima del percentil
  90) para no inflar el potencial con satélites que captan público regional.

Cada municipio se clasifica en tres grupos con **fórmula distinta** (no se mezclan métricas):

| Grupo | Condición | Demanda insatisfecha |
|---|---|---|
| Sin oferta | 0 salas | = demanda potencial |
| Subatendido | salas y penetración < 1 | = max(0, potencial − realizada) |
| Saturado / polo | penetración ≥ 1 | = 0 (atrae público de vecinos) |

La **cobertura** se calcula sobre residentes: `(potencial − insatisfecha) / potencial`. Para el
fomento, la brecha estructural distingue **aislamiento real** de **conurbación aparente** midiendo
la **distancia haversine** al polo con cine más cercano (umbral 25 km).

## 2. Captura por exhibidor (simulador)

```
rendimiento_sala(m) = admisiones(m) / salas_activas(m)
captura_bruta       = N_salas × rendimiento_sala(m)
demanda_nueva       = min(captura_bruta, demanda_insatisfecha_local)
redistribución      = captura_bruta − demanda_nueva
```

En municipios sin salas se usa el rendimiento mediano de municipios comparables por población. La
descomposición evita presentar como “crecimiento” lo que en mercados saturados es redistribución.

## 3. Estacionalidad y proyección 2027

Descomposición clásica multiplicativa `serie = nivel × factor_estacional` sobre la serie diaria
nacional 2007–2026. Con solo 4 años completos post-COVID, la proyección se reporta como **rango de
escenarios** (conservador / central / optimista), acompañada de un **backtest** walk-forward
(ajustar 2022–2024, predecir 2025 → ~13 % de error) y el **R²** del ajuste, en vez de una cifra
puntual de crecimiento. El choque 2020–2021 se trata como intervención (excluido de la tendencia).

## Aseguramiento de calidad

El proyecto fue auditado por un **panel de 3 revisores independientes** (metodología, dominio y
datos), y se aplicaron sus correcciones obligatorias (proyección como rango, cobertura coherente,
anonimización irreversible, distancia al polo, unificación de la tasa de referencia).
