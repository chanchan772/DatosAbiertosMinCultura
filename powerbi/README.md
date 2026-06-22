# Vista espejo en Power BI — CinePredict

Capa de visualización **institucional** que replica el tablero de CinePredict en
Power BI, alineada con el ecosistema tecnológico del Ministerio de las Culturas.
Consume las mismas proyecciones del modelo, exportadas como CSV.

## 1. Generar los datos

```bash
cinepredict export-powerbi
```

Esto crea en `powerbi/datos/` cuatro tablas (CSV UTF-8 con BOM, tildes correctas):

| Tabla | Tipo | Grano | Campos clave |
|-------|------|-------|--------------|
| `dim_municipio.csv` | Dimensión | municipio | `cod_divipola`, municipio, departamento, **lat**, **lon**, tiene_sala |
| `fact_demanda.csv` | Hecho | municipio | demanda_potencial, espectadores_obs, **brecha**, poblacion_15_44, dist_km_sala_cercana |
| `fact_mensual.csv` | Hecho | municipio × mes | fecha, espectadores, **tipo** (Histórico / Proyección) |
| `fact_captura.csv` | Hecho | municipio × exhibidor × año | exhibidor, num_salas, espectadores |

## 2. Importar en Power BI Desktop

1. **Inicio → Obtener datos → Texto/CSV** e importa los 4 archivos de `powerbi/datos/`.
2. En cada tabla, confirma que el origen use codificación **65001: Unicode (UTF-8)**.
3. Marca `cod_divipola` como **texto** (no número: conserva los ceros a la izquierda).

## 3. Modelo de datos (esquema estrella)

```
                 ┌────────────────────┐
   fact_demanda ─┤                    ├─ fact_mensual
                 │   dim_municipio    │
   fact_captura ─┤  (cod_divipola)    │
                 └────────────────────┘
```

Crea relaciones **1 → muchos** desde `dim_municipio[cod_divipola]` hacia el
`cod_divipola` de cada tabla de hechos (dirección de filtro única, sencilla).

> Para el mapa, marca en `dim_municipio` la categoría de datos: `lat` → *Latitud*,
> `lon` → *Longitud* (Herramientas de columna → Categoría de datos).

## 4. Medidas DAX sugeridas

Ver [`medidas.dax`](medidas.dax). Principales:

```DAX
Demanda potencial = SUM(fact_demanda[demanda_potencial])
Brecha total      = SUM(fact_demanda[brecha])
Municipios sin sala = CALCULATE(DISTINCTCOUNT(dim_municipio[cod_divipola]),
                                dim_municipio[tiene_sala] = "Sin sala")
Espectadores (mes) = SUM(fact_mensual[espectadores])
```

## 5. Páginas/visuales sugeridos (espejo del tablero)

| Página | Visual | Campos |
|--------|--------|--------|
| **Resumen** | Tarjetas KPI | Demanda potencial, Brecha total, Municipios sin sala |
| **Brecha territorial** | Mapa de burbujas | `lat`/`lon`, tamaño = `[Brecha total]`, filtro `tiene_sala = "Sin sala"` |
| **Ranking** | Tabla/matriz | departamento → municipio, `[Brecha total]` (desc) |
| **Estacionalidad** | Gráfico de líneas | eje `fecha`, valor `[Espectadores (mes)]`, leyenda `tipo` |
| **Exhibidores** | Columnas | exhibidor, `SUM(espectadores)`; segmentador por municipio |

Añade segmentadores (slicers) por **departamento** y **municipio** para la
consulta institucional, replicando la navegación del tablero Streamlit.

## 6. Actualización

Cuando se incorpore el **SIREC real** y se reentrene (`cinepredict train`),
vuelve a ejecutar `cinepredict export-powerbi` y pulsa **Actualizar** en Power BI:
el tablero se refresca con las nuevas proyecciones.
