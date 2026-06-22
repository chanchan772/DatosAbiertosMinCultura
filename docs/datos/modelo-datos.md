# Modelo de datos

## Unidad de análisis

`sala × municipio × período` (período mensual `YYYY-MM`).

## Tabla analítica (`data/processed/analytic.parquet`)

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `cod_divipola` | str(5) | Código DIVIPOLA del municipio (llave territorial) |
| `municipio` | str | Nombre del municipio |
| `departamento` | str | Nombre del departamento |
| `periodo` | str | Período mensual `YYYY-MM` |
| `exhibidor` | str | Nombre/identificador del exhibidor |
| `num_salas` | int | Número de salas activas en el período |
| `espectadores` | int | Total de espectadores registrados |

El esquema se valida con **Pandera** (`src/cinepredict/data/schemas.py`) y la
calidad con **Great Expectations** antes del modelado.

## Flujo de datos

```
data/raw/         (Parquet crudo descargado de Socrata)
   └─ clean ─▶ data/interim/   (normalización intermedia)
        └─ reconcile DIVIPOLA + validate ─▶ data/processed/analytic.parquet
```
