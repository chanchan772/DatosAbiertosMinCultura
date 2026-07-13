// Cómputo en el navegador para el despliegue estático (GitHub Pages), replicando
// la lógica del backend (demand.municipio_detail, exhibitor.simulate, narrativa
// de respaldo) a partir de los JSON precomputados. Mantiene paridad con el API.

import { MunicipioGeo, MunicipioDetail, SimResult, CalcTrace, TraceStep, Narrative } from './models';
import { CLASE_LABEL } from '../shared/format';

interface GeoPlus extends MunicipioGeo { rend_base: number; origen_rend: string }

function fmt(n: number): string {
  return (n ?? 0).toLocaleString('es-CO', { maximumFractionDigits: 0 });
}
function step(pasos: TraceStep[], nombre: string, formula: string, entradas: any,
             resultado: any, unidad = '', nota = ''): void {
  pasos.push({ n: pasos.length + 1, nombre, formula, entradas, resultado, unidad, nota });
}

export function buildMunicipioDetail(
  m: GeoPlus, tasaRef: number, metodoTasa: string, banda: string, anio: number, umbral: number,
): MunicipioDetail {
  const pob = m.poblacion_objetivo || 0;
  const potencial = m.demanda_potencial;
  const real = m.admisiones;
  const salas = m.salas_activas;
  const pen = m.penetracion;
  const clase = m.clase;
  const insat = m.demanda_insatisfecha;
  const etiqueta = CLASE_LABEL[clase] || clase;

  const pasos: TraceStep[] = [];
  step(pasos, '1. Población objetivo', `poblacion_${banda}(${anio})`, {}, pob, 'habitantes');
  step(pasos, '2. Tasa de referencia (nacional)', metodoTasa, {}, tasaRef, 'adm/hab');
  step(pasos, '3. Demanda potencial', 'potencial = poblacion_objetivo × tasa_ref',
    { poblacion_objetivo: Math.round(pob), tasa_ref: tasaRef }, Math.round(potencial), 'espectadores/año');
  step(pasos, '4. Admisiones realizadas (SIREC)', 'dato observado', {}, Math.round(real), 'espectadores/año');
  step(pasos, '5. Salas activas (SIREC)', 'dato observado', {}, salas, 'salas');
  if (pen != null) {
    step(pasos, '6. Penetración', 'penetracion = realizadas / potencial',
      { realizadas: Math.round(real), potencial: Math.round(potencial) }, Math.round(pen * 1000) / 1000, 'ratio');
  }
  step(pasos, '7. Clasificación', 'según salas y penetración', {}, etiqueta);
  const f: Record<string, string> = {
    sin_oferta: 'insatisfecha = potencial (no hay oferta local)',
    subatendido: 'insatisfecha = max(0, potencial − realizadas)',
    saturado: 'insatisfecha = 0 (satura / atrae vecinos)',
  };
  step(pasos, '8. Demanda insatisfecha', f[clase], { potencial: Math.round(potencial), realizadas: Math.round(real) },
    Math.round(insat), 'espectadores/año');
  if (clase === 'sin_oferta' && m.dist_polo_km != null) {
    step(pasos, '9. Tipo de brecha (distancia al polo)',
      `si dist_polo ≤ ${umbral} km → conurbación (aparente); si no → aislamiento (real)`,
      { dist_polo_km: m.dist_polo_km }, m.brecha_tipo, '',
      'Distingue municipios genuinamente aislados de suburbios con un multiplex a minutos.');
  }
  const trace: CalcTrace = {
    titulo: `Cálculo de demanda insatisfecha — ${m.municipio} (${m.departamento})`,
    descripcion: '',
    fuentes: [{ nombre: 'Población objetivo (DANE)', origen: `banda ${banda}, año ${anio}`, detalle: `${fmt(pob)} habitantes` }],
    supuestos: [], pasos, limitaciones: [],
  };
  return { ...m, etiqueta_clase: etiqueta, admisiones_realizadas: real, trace };
}

const SIM_SUP = [
  'Una sala nueva rinde en promedio como las salas existentes del municipio (año 2025).',
  'En municipios sin salas se usa el rendimiento mediano de municipios comparables.',
];
const SIM_LIM = [
  'No modela canibalización fina entre complejos ni el efecto de marca.',
  'En municipios sin salas se usa el rendimiento de municipios comparables por tamaño de población objetivo.',
];

export function buildSimulate(m: GeoPlus, nSalas: number, tasaRef: number, banda: string, anio: number): SimResult {
  const pob = m.poblacion_objetivo || 0;
  const potencial = m.demanda_potencial;
  const real = m.admisiones;
  const salas = m.salas_activas;
  const rend = m.rend_base;
  const insatCtx = m.demanda_insatisfecha;                 // = max(0, potencial − realizada)
  const capturaBruta = nSalas * rend;
  const headroom = potencial > 0 ? insatCtx / potencial : 0;
  const demandaNueva = Math.min(capturaBruta, insatCtx);
  const redistribucion = Math.max(0, capturaBruta - insatCtx);
  const cuota = potencial > 0 ? capturaBruta / potencial : null;

  const pasos: TraceStep[] = [];
  if (salas > 0) {
    step(pasos, '1. Rendimiento por sala (municipio)', 'rendimiento_sala = admisiones_municipio / salas_activas',
      { admisiones_municipio: Math.round(real), salas_activas: salas }, Math.round(rend), 'espectadores/sala/año');
  } else {
    step(pasos, '1. Rendimiento por sala (comparables)',
      'rendimiento_sala = mediana( adm/sala ) de municipios de tamaño similar',
      { poblacion_objetivo: Math.round(pob) }, Math.round(rend), 'espectadores/sala/año',
      'El municipio no tiene salas activas; se usa un grupo comparable por población.');
  }
  step(pasos, '2. Captura bruta estimada', 'captura_bruta = N_salas × rendimiento_sala',
    { N_salas: nSalas, rendimiento_sala: Math.round(rend) }, Math.round(capturaBruta), 'espectadores/año');
  step(pasos, '3. Descomposición demanda nueva vs redistribución',
    'demanda_nueva = min(captura_bruta, demanda_insatisfecha) ; redistribución = captura_bruta − demanda_nueva',
    { captura_bruta: Math.round(capturaBruta), demanda_insatisfecha_local: Math.round(insatCtx) },
    { demanda_nueva: Math.round(demandaNueva), redistribucion: Math.round(redistribucion) }, 'espectadores/año',
    'Transparencia: parte de la captura puede provenir de competidores, no ser demanda nueva.');
  step(pasos, '4. Cuota de mercado estimada', 'cuota = captura_bruta / demanda_potencial_municipio',
    { captura_bruta: Math.round(capturaBruta), demanda_potencial: Math.round(potencial) },
    cuota != null ? Math.round(cuota * 1000) / 1000 : null, 'ratio');

  const trace: CalcTrace = {
    titulo: `Simulación de exhibidor — ${m.municipio} (${m.departamento})`,
    descripcion: `${nSalas} sala(s) hipotética(s), año de referencia ${anio}, banda ${banda}.`,
    fuentes: [
      { nombre: 'Admisiones y salas (SIREC)', origen: 'AdmisionesXmunicipio (Salas registradas y activas)', detalle: `Año ${anio} completo` },
      { nombre: 'Población objetivo (DANE)', origen: `banda ${banda}`, detalle: `${fmt(pob)} hab.` },
    ],
    supuestos: SIM_SUP, pasos, limitaciones: SIM_LIM,
  };
  return {
    cod_mpio: m.cod_mpio, municipio: m.municipio, departamento: m.departamento, n_salas: nSalas,
    rendimiento_sala: Math.round(rend), origen_rendimiento: m.origen_rend,
    captura_estimada: Math.round(capturaBruta), demanda_nueva: Math.round(demandaNueva),
    redistribucion: Math.round(redistribucion), cuota_mercado: cuota != null ? Math.round(cuota * 10000) / 10000 : null,
    contexto: {
      poblacion_objetivo: pob, demanda_potencial: Math.round(potencial), demanda_realizada: Math.round(real),
      demanda_insatisfecha: Math.round(insatCtx), salas_actuales: salas, headroom_pct: Math.round(headroom * 1000) / 10,
    },
    lat: m.lat, lon: m.lon, trace,
  };
}

// Narrativa de respaldo (cuando no hay backend con DeepSeek): resumen determinista.
export function fallbackNarrative(tipo: string, ctx: any): Narrative {
  let t = '';
  if (tipo === 'territorio') {
    const ins = ctx.demanda_insatisfecha;
    t = `Resumen de ${ctx.municipio}. Clasificado como “${ctx.etiqueta_clase || ctx.clase}”. `;
    if (ins != null) t += `Demanda potencial ${fmt(ctx.demanda_potencial)} vs. realizada ${fmt(ctx.demanda_realizada)}; ` +
      `demanda insatisfecha estimada ≈ ${fmt(ins)} espectadores/año. `;
    t += 'Cifra estimada sobre residentes; conviene verificar el acceso a municipios vecinos antes de decidir inversión.';
  } else if (tipo === 'simulacion') {
    t = `Con ${ctx.n_salas} sala(s), la captura estimada es ≈ ${fmt(ctx.captura_estimada)} espectadores/año, ` +
      `de los cuales ${fmt(ctx.demanda_nueva)} serían demanda nueva y ${fmt(ctx.redistribucion)} redistribución de mercado. ` +
      (ctx.demanda_nueva === 0 ? 'El mercado está saturado: la captura provendría de competidores, no de demanda nueva.' : '');
  } else {
    t = `Panorama nacional: el consumo de cine se concentra fuertemente (top-3 exhibidores ≈ ` +
      `${ctx.concentracion?.top3_exhibidores_pct}% del mercado). La principal brecha son los municipios sin oferta.`;
  }
  return { narrativa: t, fuente: 'fallback', modelo: null };
}
