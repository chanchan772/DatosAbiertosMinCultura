# Fuentes de datos

## Fuentes primarias (SIREC — DACMI, publicadas en datos.gov.co)

| Archivo | Contenido | Filas | Uso |
|---|---|---|---|
| `Taquilla 2026-Colarco.xlsx` | Detalle transaccional de admisiones por sala, título, fecha y exhibidor (ene–may 2026) | 281.451 | Panorama, rendimiento por sala |
| `Datos abiertos.xlsx` | Serie diaria nacional de asistencia 2007–2026 | 7.011 | Estacionalidad y proyección |
| `Salas de Cine Registradas y Activas.xlsx` | Complejos con nº de salas y capacidad; admisiones + salas activas por municipio 2024/25/26 | 271 / 105 | Oferta y demanda insatisfecha |
| `HISTORICO Estrenos Total.xlsx` | Catálogo de largometrajes exhibidos desde 2020, con alcance territorial | 2.586 | Contexto de contenido |
| `HISTORICO Estrenos Colombia.xlsx` | Estrenos de cine colombiano con admisiones y cobertura | 1.596 | Participación del cine nacional |

## Fuentes externas obligatorias (datos.gov.co)

| Dataset | ID | Uso |
|---|---|---|
| **DIVIPOLA — Códigos de municipios** | `gdxc-w37w` | Reconciliación territorial (código de 5 dígitos) y geolocalización del mapa |
| DIVIPOLA — Códigos de departamentos | `vcjz-niiq` | Normalización de departamentos |
| Población Antioquia por edad (validación) | `evm3-92yw` | Control de coherencia de las bandas de edad |

## Fuente externa DANE (upstream)

- **Proyecciones de población municipal por área, sexo y edad 2020–2035** (base CNPV 2018,
  actualización post-COVID). Archivo oficial del DANE. De aquí se derivan las bandas de edad
  15–30, 15–45 y 15–60 por municipio (código DIVIPOLA), para los años 2024–2027.

> **Nota de procedencia:** datos.gov.co no publica la proyección nacional municipal-por-edad; se
> usa el archivo primario del DANE (upstream del mismo dato) y se **valida contra datos.gov.co**
> (Antioquia por edad, `evm3-92yw`): p.ej. Medellín 15–30 según DANE 2024 ≈ 678.966 vs. censo en
> datos.gov.co ≈ 675.549.

## Reconciliación y calidad

- **100 %** de los pares (departamento, municipio) del SIREC se reconciliaron al código DIVIPOLA
  (95 exactos + 8 por alias documentado, dentro de cada departamento para evitar homónimos).
- **Anonimización:** exhibidores y complejos se pseudonimizan con seudónimos secuenciales
  (EXH-001…) irreversibles desde el token; se eliminan direcciones (PII). Preserva todos los
  agregados.
