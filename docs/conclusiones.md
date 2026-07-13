# Conclusiones

## Resultados clave

1. **El acceso al cine en Colombia es altamente inequitativo.** El 31,7 % de las admisiones se
   concentra en Bogotá, los 5 municipios mayores suman >53 %, y 3 exhibidores controlan ~72 % del
   mercado.

2. **Brecha estructural masiva.** De 1.122 municipios, **~1.025 no tienen salas de cine activas**,
   con una demanda potencial residente sin atender de **~25,7 millones** de espectadores/año. Al
   separar por distancia al polo más cercano, **833 municipios están genuinamente aislados** y
   **191 son conurbación aparente** (tienen un multiplex a ≤25 km): esta distinción es clave para
   focalizar el fomento.

3. **Cobertura residente ≈ 54 %.** La demanda potencial residente nacional (~71 M) frente a lo
   atendido localmente deja una demanda insatisfecha de ~32,8 M, concentrada en ciudades
   intermedias subatendidas (Soledad, Valledupar, Cartagena, Buenaventura…) y en la periferia sin
   oferta.

4. **El sector se estabilizó, no crece.** Tras el desplome COVID (2019: 73,6 M → 2020: 12,8 M),
   la asistencia se recuperó a un **nivel estable de ~50 M/año en 2023–2025**. La proyección 2027
   se reporta como rango **44,6 M – 55,2 M** (central ~51 M), con un error de validación (backtest)
   de ~13 %: presentar un único valor de crecimiento sería engañoso.

5. **El cine colombiano tiene apenas 1,45 % de las admisiones.** La demanda insatisfecha
   territorial es también una oportunidad de exhibición para la producción nacional.

## Interpretación

El problema no es principalmente de **volumen agregado** sino de **distribución territorial**. Los
instrumentos de la **Ley 814 de 2003** pueden focalizarse con evidencia: priorizar municipios
aislados con demanda potencial alta antes que suburbios ya cubiertos por polos cercanos.

## Impacto potencial

- **Focalización del fomento** a la exhibición regional con criterios cuantitativos y auditables.
- **Transparencia institucional:** cada cifra es reconstruible paso a paso, apta para revisión por
  pares y para la apropiación por tomadores de decisión sin perfil técnico (narrativas asistidas
  por IA).
- **Reproducibilidad:** pipeline y modelo abiertos, extensibles a nuevos cortes del SIREC.

## Limitaciones y trabajo futuro

- Incorporar **matrices de accesibilidad vial** (INVIAS / OpenStreetMap) para modelar la fuga de
  público con mayor precisión que la distancia en línea recta.
- Enriquecer el modelo de demanda con variables socioeconómicas (MDM/DNP) y de contenido.
- Añadir intervalos de predicción formales y validación cruzada temporal más extensa cuando haya
  más años completos post-COVID.
