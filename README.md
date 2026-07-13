<p align="center">
  <img src="Recursos/portada.png" alt="CinePredict" width="820">
</p>

# CinePredict — Modelo predictivo de espectadores de cine en Colombia

> **Concurso Datos al Ecosistema 2026 · Reto 8 — Cultura y Turismo**
> Grupo de Producción y Gestión de la Información · DACMI · Ministerio de las Culturas, las Artes y los Saberes.

---

## Problema abordado

Colombia tiene una **distribución profundamente inequitativa del acceso al cine**: la
infraestructura de salas se concentra en pocas ciudades, generando brechas de consumo cultural que
los datos permiten identificar pero que no habían sido modeladas de forma sistemática y abierta.
CinePredict cuantifica esas brechas y proyecta la demanda a nivel nacional, regional y por
exhibidor. Ver [docs/planteamiento_problema.md](docs/planteamiento_problema.md).

## Justificación (valor público)

Identificar y cuantificar las brechas de acceso permite **focalizar los instrumentos de fomento a
la exhibición regional** de la **Ley 814 de 2003**, priorizando municipios genuinamente aislados en
lugar de suburbios ya cubiertos por polos cercanos. Todo el producto es transparente, reproducible
y de código abierto, apto para revisión por pares y para tomadores de decisión sin perfil técnico.

## Cantidad de datasets utilizados

**7 fuentes**: 5 bases del SIREC + 2 externas obligatorias/DANE. Detalle en
[docs/fuentes_datos.md](docs/fuentes_datos.md).

## Datasets utilizados (datos.gov.co — obligatorio)

- **DIVIPOLA — Códigos de municipios** (`gdxc-w37w`): 1.122 municipios + geolocalización.
- DIVIPOLA — Códigos de departamentos (`vcjz-niiq`).
- Población Antioquia por edad (`evm3-92yw`) — validación cruzada de las bandas de edad.
- Bases del SIREC publicadas por la DACMI (taquilla, serie diaria, salas, estrenos) — en `Datos/`.

## Datasets externos

- **DANE — Proyecciones de población municipal por edad 2020–2035** (base CNPV 2018,
  actualización post-COVID). Fuente primaria de las bandas de edad 15–30 / 15–45 / 15–60.
  *(datos.gov.co no publica la versión nacional-por-edad; se valida contra datos.gov.co.)*

## Variables seleccionadas

Población por banda de edad, admisiones, salas activas, capacidad, municipio/departamento
(DIVIPOLA), género, clasificación, nacionalidad, día de la semana, y variables derivadas
(demanda potencial, penetración, clase, distancia al polo). Diccionario completo en
[docs/diccionario_datos.md](docs/diccionario_datos.md).

## Tipo de análisis

**Mixto — descriptivo + predictivo (regresión).** Descriptivo: panorama y concentración.
Predictivo: demanda potencial municipal, captura por exhibidor y proyección de series de tiempo.

## Modelo utilizado

- **Regresión** (per cápita ponderada) para la demanda potencial e insatisfecha, con clasificación
  territorial en tres grupos.
- **Regresión lineal + descomposición estacional clásica** para la proyección 2027 (reportada como
  rango de escenarios con backtest).
- **Modelo de rendimiento por sala** para el simulador de exhibidor.

Metodología y fórmulas en [docs/marco_metodologico.md](docs/marco_metodologico.md).

## Resultados clave

- **~1.025 municipios sin cine** → **25,7 M** de demanda potencial residente sin atender.
- **833 municipios de aislamiento real** vs **191 de conurbación aparente** (distancia al polo).
- Cobertura residente **≈ 54 %** · demanda insatisfecha nacional **≈ 32,8 M**.
- Proyección 2027 como **rango 44,6 M – 55,2 M** (central ~51 M; backtest ~13 % de error).
- Concentración: Bogotá 31,7 % de admisiones; top-3 exhibidores ~72 %; cine colombiano 1,45 %.

## Interpretación

El problema es de **distribución territorial**, no de volumen agregado. La evidencia permite
focalizar el fomento hacia municipios aislados con alta demanda potencial. Ver
[docs/conclusiones.md](docs/conclusiones.md).

## Impacto potencial

Focalización del fomento (Ley 814) con criterios cuantitativos y auditables; transparencia
institucional (cada cifra reconstruible paso a paso); y reproducibilidad del pipeline y el modelo.

---

## Solución en producción (Demo en Vivo)

Para ver y probar la solución funcionando en tiempo real:

- **Aplicación web / Demo en vivo:** **[Abrir el tablero](https://chanchan772.github.io/DatosAbiertosMinCultura/)**
  → `https://chanchan772.github.io/DatosAbiertosMinCultura/`
  *(SPA estática desplegada con GitHub Pages/Actions; se publica automáticamente en cada push.)*
- **Documentación de la API (local):** al ejecutar el backend, Swagger queda en
  `http://127.0.0.1:8000/docs`.

## Enlaces de acceso

- [Descargar presentación (.PPTX)](Recursos/Presentacion.pptx) — para abrir y editar en PowerPoint.
- [Ver presentación en línea (.PDF)](Recursos/presentacion.pdf) — visor de GitHub.
- [Descarga directa (.PDF)](Recursos/presentacion.pdf?raw=true) — fuerza la descarga.

## Documentación técnica (`docs/`)

Para profundizar en los detalles teóricos, metodológicos y de diseño:

- [Planteamiento del problema](docs/planteamiento_problema.md)
- [Marco metodológico](docs/marco_metodologico.md)
- [Fuentes de datos](docs/fuentes_datos.md)
- [Diccionario de datos](docs/diccionario_datos.md)
- [Arquitectura](docs/architecture.md)
- [Conclusiones](docs/conclusiones.md)

---

## Ejecución local (backend + frontend en vivo, con narrativas DeepSeek)

```bash
./run.sh                 # backend :8000 + frontend :4200
./run.sh --pipeline      # regenera el pipeline de datos primero
./run.sh --backend       # solo backend
```

Manual:
```bash
pip install -r backend/requirements.txt
python -m backend.run_pipeline          # opcional (idempotente)
uvicorn backend.app.main:app --port 8000
cd frontend && npm install && ng serve --port 4200
```

> El repositorio incluye los datos anonimizados precomputados y los datasets crudos (`Datos/`),
> de modo que la aplicación corre tras `git clone`. La llave de DeepSeek viene incluida para que
> los evaluadores puedan probar las narrativas sin configuración adicional.

## Licencia
Código abierto, para auditoría, réplica y extensión por terceros — en línea con los principios de
gobierno abierto y datos abiertos del Estado colombiano.
