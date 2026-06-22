# Datos de referencia

Esta carpeta **sí se versiona** (a diferencia de `raw/`, `interim/`, etc.):
contiene diccionarios pequeños y estables necesarios para reproducir el pipeline.

## Archivos esperados

- `divipola.csv` — diccionario DIVIPOLA del DANE con columnas:
  `cod_divipola` (5 dígitos), `municipio`, `departamento`.
  Fuente: Marco Geoestadístico Nacional / DANE.

> Los datasets grandes (SIREC, proyecciones DANE, cartografía) NO van aquí; se
> descargan de forma reproducible con `cinepredict download` y quedan en
> `data/raw/` (ignorado por git).
