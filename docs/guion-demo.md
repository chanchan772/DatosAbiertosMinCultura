# 🎬 Guion / Storyboard de la demo — CinePredict

> **Evento:** Final presencial · GovCamps 2026 (primera semana de agosto)
> **Duración objetivo:** ~10 min (7 min demo + 3 min Q&A)
> **Audiencia:** jurado técnico + tomadores de decisión del sector cultural
> **Mensaje central:** *con datos abiertos hicimos visible —y predecible— la brecha de acceso al cine en Colombia, y lo dejamos como herramienta abierta para orientar el fomento regional.*

---

## 🎯 Antes de empezar (checklist de 2 minutos)

- [ ] Entorno levantado: `.venv\Scripts\python -m streamlit run app/streamlit_app.py`
- [ ] Navegador en `http://localhost:8501`, **zoom 110–125 %**, modo pantalla completa (F11).
- [ ] Pestañas abiertas: el tablero · el repo en GitHub · (opcional) Power BI con los CSV cargados.
- [ ] `.env` con `ANTHROPIC_API_KEY` para la narrativa en vivo (si no, hay texto de respaldo).
- [ ] Conexión probada con datos.gov.co. **Plan B si la API falla:** el aplicativo cae a la copia local con aviso — *eso es una fortaleza, no un fallo* (ver Escena 2).
- [ ] Tener a la mano la cifra real (cuando esté el SIREC real). En ensayo usar las del modelo.

---

## 🪧 Arco narrativo (one-liner por acto)

1. **Problema** — el cine en Colombia está concentrado; hay público sin oferta.
2. **Datos** — lo construimos sobre datos abiertos del Estado, consumidos por API.
3. **Modelo** — predecimos demanda, brecha y estacionalidad a 2027.
4. **Decisión** — el tablero responde las 3 preguntas del reto y habla en lenguaje de política.
5. **Cierre** — abierto, replicable, conectado a la Ley 814.

---

## 🎞️ Storyboard escena por escena

### Escena 0 · Gancho (0:00–0:45)
**Pantalla:** página **Inicio** del tablero (hero + KPIs).
**Acción:** dejar visibles las tarjetas (municipios con sala vs. sin sala).
**Guion:**
> "En Colombia, **solo ~1 de cada 10 municipios tiene una sala de cine**. El resto
> —cientos de municipios con público real— simplemente no aparece en el mapa de la
> oferta cultural. Somos el equipo que administra el **SIREC** en el Ministerio de
> las Culturas, y decidimos convertir ese vacío en algo medible y **predecible**."

*Transición:* "¿Y cómo lo hicimos? Con datos abiertos, sin trucos."

---

### Escena 1 · Datos abiertos en vivo (0:45–2:00)
**Pantalla:** página **Datos Abiertos** → pulsar **⚡ Consumir la API**.
**Acción:** mostrar el consumo paso a paso (endpoints → metadatos → datos → mapa).
**Guion:**
> "Nada está cargado a mano. En este momento el aplicativo está **llamando en vivo a
> la API del portal datos.gov.co**. Pedimos el esquema… llegan los datos… y aquí está:
> **los 1.122 municipios del DANE (DIVIPOLA)** ubicados en el mapa. Esta es la **llave
> territorial** que une todas nuestras fuentes y nos da las coordenadas para medir
> accesibilidad."

**Plan B (si la API responde 500):**
> "Fíjense: el portal del Estado tuvo una intermitencia y el aplicativo **no se cayó**:
> cambió automáticamente a la última copia descargada por API y nos avisó. Esa
> **resiliencia** es parte de hacer un producto serio para producción."

*Transición:* "A esto le sumamos la población por edad del DANE y nuestra fuente reina, el SIREC."

---

### Escena 2 · Demanda y brecha (2:00–4:00) — *el corazón*
**Pantalla:** página **Demanda y Brecha** (mapa de burbujas, toggle "solo sin salas").
**Acción:** señalar las burbujas grandes; abrir la tabla Top 15.
**Guion:**
> "El **Componente A** es un modelo de regresión que estima la **demanda potencial**
> de cada municipio según su población de 15 a 44 años —la que más va a cine— y qué tan
> lejos está la sala más cercana. La diferencia con la asistencia real es la **demanda
> insatisfecha**: estos territorios *tienen público pero no tienen cine*."
>
> "Cada burbuja es un municipio sin sala; su tamaño es el público desatendido proyectado
> a 2027. Este ranking es, literalmente, una **lista priorizada de dónde conviene fomentar
> la exhibición**."

*Dato para enfatizar (reemplazar con cifra real):* "≈44 millones de asistencias potenciales hoy sin atender."

*Transición:* "Y si un exhibidor quisiera entrar a uno de estos municipios, ¿cuánto capturaría?"

---

### Escena 3 · Simulador de exhibidor (4:00–5:15)
**Pantalla:** página **Simulador de Exhibidor**.
**Acción:** elegir un municipio mediano sin sala, mover el slider de salas; mostrar la métrica y la curva de sensibilidad.
**Guion:**
> "El **Componente B** (CatBoost) responde la segunda pregunta del reto: *¿cuántos
> espectadores captaría un exhibidor hipotético?* Elijo el municipio, el número de salas…
> y el modelo proyecta la asistencia anual. Sirve para **dimensionar una inversión** o
> una política de incentivos **antes** de ejecutarla."

*Transición:* "Pero una cifra anual no basta para operar: hay que saber el cuándo."

---

### Escena 4 · Estacionalidad y COVID (5:15–6:15)
**Pantalla:** página **Estacionalidad** (serie nacional con la franja COVID).
**Acción:** señalar los picos (enero, mitad de año, diciembre) y la franja roja 2020–2021.
**Guion:**
> "El **Componente C** desagrega mes a mes con modelos de series de tiempo. Vean los picos
> de vacaciones y diciembre. Y aquí —la franja roja— el **cierre de salas por COVID**:
> en vez de dejar que distorsione la tendencia, lo modelamos como una **intervención**,
> aprovechando que conocemos los vacíos de la serie desde adentro del SIREC."

*Transición:* "Todo esto es potente… pero un secretario de cultura no lee modelos. Lee historias."

---

### Escena 5 · Narrativa con IA (6:15–7:00)
**Pantalla:** página **Narrativa IA** → elegir un departamento → **Generar narrativa**.
**Guion:**
> "Aquí entra la IA aplicada: con la **API de Claude** convertimos las proyecciones de
> cada territorio en un **resumen en lenguaje claro** para tomadores de decisión sin
> perfil técnico. Esto es lo que cierra la brecha entre el dato y la **política pública**."

*Transición:* "Y para que el Ministerio lo adopte en sus herramientas de siempre…"

---

### Escena 6 · Cierre: abierto y replicable (7:00–7:45)
**Pantalla:** GitHub del proyecto + (opcional) la vista espejo en **Power BI**.
**Guion:**
> "Todo es **código abierto** en GitHub: datos, modelo y documentación, reproducibles de
> punta a punta. Exportamos también una **vista espejo en Power BI** para apropiación
> institucional. CinePredict no es un tablero más: es un **instrumento técnico para
> orientar el fomento a la exhibición regional de la Ley 814 de 2003**, con potencial de
> escalar a todo el sector audiovisual."
>
> "Hicimos visible lo invisible: dónde está el público de cine que Colombia todavía no atiende."

---

## ❓ Preguntas probables del jurado (y respuestas)

| Pregunta | Respuesta corta |
|----------|-----------------|
| ¿Los datos son reales? | La arquitectura corre con datos abiertos reales (DIVIPOLA y proyecciones DANE). La exhibición usa una **base de prueba** mientras integramos el **SIREC real** que administramos; el pipeline ya está listo para recibirlo. |
| ¿Por qué 15–44 años? | Es la franja de mayor consumo de cine; la tomamos de la proyección por edad del DANE (Censo 2018). |
| ¿Cómo manejan el COVID? | Como **variable de intervención** (2020–2021), para que no contamine la tendencia proyectada. |
| ¿Es explicable / auditable? | Sí: usamos **SHAP** para explicar el modelo y todo el código es abierto y reproducible. |
| ¿Escalabilidad? | Mismo enfoque sirve para teatro, museos, bibliotecas: cambia la fuente, no la arquitectura. |
| ¿Sesgo de “más salas = más cine”? | Por eso separamos **demanda potencial** (independiente de la oferta) de **captura**; así medimos la brecha sin circularidad. |

---

## 🧰 Notas de producción

- **Ensayar el orden de clics**; tener cada página ya cargada una vez (cachea datos).
- Si la conexión es inestable, **pre-cargar** la página de Datos Abiertos antes de iniciar.
- Hablar de **decisiones**, no de librerías: el jurado mixto valora el *para qué*.
- Cerrar siempre con la frase de impacto (Escena 6).
- Reloj: si falta tiempo, **sacrificar la Escena 3 o 5**, nunca la 2 (la brecha es el corazón).
