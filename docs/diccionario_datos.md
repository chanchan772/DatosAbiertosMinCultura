# Diccionario de datos

Variables de las tablas procesadas (anonimizadas) que alimentan los modelos.

## `fact_taquilla` — detalle transaccional 2026

| Campo | Tipo | Descripción |
|---|---|---|
| `fecha_exhibicion` | fecha | Día de exhibición |
| `exhibidor_tok` | texto | Exhibidor **pseudonimizado** (EXH-001…) |
| `complejo_tok` | texto | Complejo **pseudonimizado** (CPX-001…) |
| `id_complejo`, `id_sala` | entero | Identificadores de complejo y sala |
| `titulo` | texto | Título de la película |
| `admisiones` | entero | Nº de espectadores del registro |
| `departamento`, `municipio` | texto | Territorio (reconciliado a DIVIPOLA) |
| `genero` | texto | Ficción / Animación / Documental |
| `clasificacion` | texto | Clasificación (Todos, +7, +12, +15, +18) |
| `nacion` | texto | Colombiana / Extranjera / Sin asignar |
| `catalogo_estreno` | texto | Catálogo o Estreno |
| `dia_semana` | texto | Día de la semana (incl. Festivo) |

## `serie_diaria_nacional` — asistencia diaria 2007–2026

| Campo | Tipo | Descripción |
|---|---|---|
| `fecha` | fecha | Día |
| `anio`, `mes`, `dia_semana` | entero | Derivados de la fecha |
| `asistencia` | entero | Asistencia nacional del día |

## `admisiones_municipio_anual` — oferta y demanda por municipio

| Campo | Tipo | Descripción |
|---|---|---|
| `departamento`, `municipio` | texto | Territorio |
| `anio` | entero | 2024, 2025 o 2026 |
| `salas_activas` | entero | Salas activas en el período |
| `admisiones` | decimal | Admisiones del año (convertidas de miles a unidades) |

## `poblacion_municipal` — población por edad (DANE)

| Campo | Tipo | Descripción |
|---|---|---|
| `cod_mpio` | texto | Código DIVIPOLA de 5 dígitos |
| `anio` | entero | 2024–2027 |
| `pob_15_30`, `pob_15_45`, `pob_15_60` | decimal | Población en la banda de edad (suma de edades simples) |
| `poblacion_total` | decimal | Población total municipal |

## `divipola_municipios` — territorio (datos.gov.co)

| Campo | Tipo | Descripción |
|---|---|---|
| `cod_dpto`, `cod_mpio` | texto | Códigos DANE (2 y 5 dígitos) |
| `departamento`, `municipio` | texto | Nombres oficiales |
| `lat`, `lon` | decimal | Geolocalización (para el mapa y la distancia al polo) |

## Variables derivadas por los modelos

| Variable | Definición |
|---|---|
| `tasa_referencia` | Admisiones per cápita de referencia (ponderada, sin polos) |
| `demanda_potencial` | `poblacion_objetivo × tasa_referencia` |
| `penetracion` | `admisiones / demanda_potencial` |
| `clase` | sin_oferta / subatendido / saturado |
| `demanda_insatisfecha` | Según la clase (ver marco metodológico) |
| `dist_polo_km` | Distancia haversine al polo con cine más cercano |
| `brecha_tipo` | aislamiento / conurbacion (para municipios sin oferta) |
| `rend_base` | Rendimiento por sala usado por el simulador |
