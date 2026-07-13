// Llamadas a DeepSeek DIRECTAMENTE desde el navegador (modo estático / GitHub
// Pages). DeepSeek permite CORS, por lo que la demo pública puede interpretar y
// responder consultas sin backend. Los prompts replican los del backend.
import { environment as env } from '../../environments/environment';

const INTERPRET_SYSTEM =
  'Eres analista de datos del Ministerio de las Culturas de Colombia. Te entregan los datos de UN ' +
  'módulo del tablero CinePredict (asistencia y acceso al cine). Redacta una INTERPRETACIÓN ' +
  'DETALLADA, LARGA y ROBUSTA de esos datos, en español, pensada para CUALQUIER TIPO DE PÚBLICO ' +
  '(ciudadanía, gestores culturales, tomadores de decisión): sin tecnicismos, y cuando uses un ' +
  'término técnico, explícalo en palabras simples.\n' +
  'ESTRUCTURA (usa subtítulos en negrita con Markdown):\n' +
  '**En pocas palabras** — 2-3 frases que resuman lo esencial.\n' +
  '**Qué muestran los datos** — describe las cifras clave en lenguaje cotidiano, con ejemplos y ' +
  'comparaciones que ayuden a dimensionarlas.\n' +
  '**Hallazgos principales** — lista de 3 a 6 patrones importantes, cada uno con su cifra.\n' +
  '**Qué significa para el país** — implicaciones para el acceso a la cultura y la política ' +
  'pública de fomento (Ley 814 de 2003), de forma concreta.\n' +
  '**Matices y límites** — qué NO se puede concluir y por qué (honestidad analítica).\n' +
  'REGLAS: usa ÚNICAMENTE las cifras del JSON (no inventes ni estimes). Sé claro, pedagógico y ' +
  'concreto. Extensión objetivo: 350-600 palabras. Los exhibidores están anonimizados (EXH-###).';

const MODULO_DESC: Record<string, string> = {
  panorama: 'Panorama nacional: magnitud, evolución histórica y concentración del consumo.',
  brechas: 'Mapa de brechas: demanda potencial vs. atendida y municipios con demanda insatisfecha.',
  simulador: 'Simulación de un exhibidor hipotético en un municipio (captura, demanda nueva vs redistribución).',
  proyeccion: 'Estacionalidad y proyección de asistencia a 2027 (escenarios y validación).',
  catalogo: 'Catálogo de datos: fuentes, procedencia, anonimización y reconciliación territorial.',
  metodologia: 'Metodología: preguntas, fórmulas, supuestos y limitaciones de cada modelo.',
};

const QUERY_SYSTEM =
  'Eres el asistente analítico de CinePredict, un tablero del Ministerio de las Culturas de ' +
  'Colombia sobre asistencia y acceso al cine (fuentes SIREC y DANE). Respondes preguntas en ' +
  'lenguaje natural.\nREGLAS ESTRICTAS:\n' +
  '1) Usa ÚNICAMENTE las cifras del JSON de contexto que se te entrega. NO inventes datos.\n' +
  '2) Si la respuesta no está en el contexto, dilo claramente y sugiere qué módulo del tablero consultar.\n' +
  '3) Cita las cifras concretas y, cuando aplique, aclara el año (taquilla 2026 es parcial; la demanda usa 2025).\n' +
  '4) Los exhibidores están anonimizados (EXH-###); no inventes nombres reales.\n' +
  '5) Responde en español, claro y bien explicado para cualquier público. Usa listas cuando ayude.';

async function callDeepSeek(system: string, user: string, maxTokens: number, temperature: number): Promise<string> {
  const res = await fetch(`${env.deepseekUrl}/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${env.deepseekApiKey}` },
    body: JSON.stringify({
      model: env.deepseekModel,
      messages: [{ role: 'system', content: system }, { role: 'user', content: user }],
      temperature, max_tokens: maxTokens, stream: false,
    }),
  });
  if (!res.ok) throw new Error('DeepSeek HTTP ' + res.status);
  const data = await res.json();
  return (data.choices?.[0]?.message?.content || '').trim();
}

export async function interpretBrowser(modulo: string, datos: any): Promise<any> {
  const desc = MODULO_DESC[modulo] || modulo;
  const user = `Módulo: ${desc}\n\nDatos del módulo (JSON):\n${JSON.stringify(datos)}`;
  try {
    const txt = await callDeepSeek(INTERPRET_SYSTEM, user, 1300, 0.35);
    return { interpretacion: txt, fuente: 'deepseek', modelo: env.deepseekModel };
  } catch (e: any) {
    return { interpretacion: 'No fue posible generar la interpretación (¿sin conexión?). Intenta de nuevo.', fuente: 'error', modelo: null };
  }
}

export async function queryBrowser(pregunta: string, context: any): Promise<any> {
  const user = `Pregunta del usuario: ${pregunta}\n\nContexto de datos (JSON):\n${JSON.stringify(context)}`;
  try {
    const txt = await callDeepSeek(QUERY_SYSTEM, user, 700, 0.2);
    return { respuesta: txt, fuente: 'deepseek', modelo: env.deepseekModel };
  } catch (e: any) {
    return { respuesta: 'No fue posible consultar el modelo en este momento. Intenta de nuevo.', fuente: 'error', modelo: null };
  }
}
