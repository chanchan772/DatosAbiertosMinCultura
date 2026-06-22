# Arquitectura del modelo

Arquitectura **híbrida** en tres componentes complementarios. La separación
permite responder de forma directa a las tres preguntas del reto.

```
        ┌─────────────────────────────┐
        │  A. Demanda potencial        │  Regresión (LightGBM)
        │     municipal                │  ← demografía + accesibilidad
        └─────────────┬───────────────┘
                      │ demanda potencial − asistencia = brecha
        ┌─────────────▼───────────────┐
        │  B. Captura por exhibidor    │  CatBoost
        │     (nº salas × territorio)  │  ← proyección exhibidor hipotético
        └─────────────┬───────────────┘
                      │ totales anuales
        ┌─────────────▼───────────────┐
        │  C. Estacionalidad y         │  SARIMAX / Prophet / TFT
        │     tendencia (mensual)      │  ← desagregación mes a mes
        └─────────────────────────────┘
```

## Componente A — Demanda potencial municipal
Estima los espectadores potenciales de un municipio según variables demográficas
(DANE) y de accesibilidad (OSM/INVIAS), con independencia de la oferta. La brecha
frente a la asistencia observada localiza la **demanda insatisfecha**.

## Componente B — Captura por exhibidor
Modela los espectadores capturados según el número de salas y las características
del territorio. Responde la **proyección para un exhibidor hipotético**. Usa
CatBoost por el manejo nativo de categóricas de alta cardinalidad.

## Componente C — Estacionalidad y tendencia
Series de tiempo mensuales por territorio. Incorpora festivos colombianos y el
**quiebre COVID 2020-2021 como variable de intervención**. StatsForecast permite
ajustar cientos de series municipales en paralelo; NeuralForecast (TFT) se evalúa
como modelo avanzado.

## Reproducibilidad y explicabilidad
- **Optuna** para optimización de hiperparámetros.
- **MLflow** para trazabilidad de experimentos.
- **SHAP** para explicabilidad: predicciones auditables y comunicables al sector.
- Validación cruzada con **respeto a la causalidad temporal** (sktime).
