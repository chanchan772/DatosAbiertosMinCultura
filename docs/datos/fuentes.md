# Fuentes de datos

## Primarias

### SIREC — Sistema de Información y Registro Cinematográfico
Estadísticas de exhibición por sala, título, período y número de espectadores,
desagregadas a nivel de municipio y establecimiento. Administrado por la DACMI y
publicado en [datos.gov.co](https://www.datos.gov.co).

> El equipo administra el SIREC, lo que garantiza la interpretación correcta de
> códigos, criterios de reporte y el tratamiento de vacíos estructurales (en
> particular el quiebre 2020-2021 por COVID-19).

### DANE — Proyecciones de población
Proyecciones municipales y departamentales basadas en el Censo Nacional de
Población y Vivienda 2018, con composición etaria.

## Complementarias (en evaluación)

| Fuente | Uso |
|--------|-----|
| INVIAS / DNP | Conectividad vial (red primaria/secundaria) → accesibilidad |
| DNP — MDM / Ley 617 | Categorización y desempeño municipal (contexto) |
| MGN (DANE) | Cartografía oficial para cruces espaciales |
| OpenStreetMap (OSMnx) | Red vial detallada → matrices de tiempo de viaje |

## Llave territorial

Todas las fuentes se reconcilian contra el código **DIVIPOLA** (5 dígitos) del
DANE. El diccionario se **consume directamente por API** desde datos.gov.co
(recurso `gdxc-w37w`) y se materializa en `data/reference/divipola.csv`:

```bash
cinepredict download --source divipola
# equivalente directo a la API SODA:
curl "https://www.datos.gov.co/resource/gdxc-w37w.json?\$limit=2"
```

Este recurso aporta también las **coordenadas (lat/lon)** de cada municipio,
usadas como centroides para las variables de accesibilidad.

## Consumo por API (SODA / Socrata)

Todos los datasets tabulares de datos.gov.co exponen API REST:

| Propósito | Endpoint |
|-----------|----------|
| Datos | `https://www.datos.gov.co/resource/<ID>.json` |
| Metadatos / esquema | `https://www.datos.gov.co/api/views/<ID>.json` |
| Filtros / agregaciones | parámetros SoQL: `$select`, `$where`, `$limit`, `$offset` |

El catálogo completo de fuentes (IDs, estado y tipo de consumo) está en
[`conf/fuentes.yaml`](../../conf/fuentes.yaml).
