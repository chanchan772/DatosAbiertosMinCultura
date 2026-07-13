// Interfaces de datos de la API CinePredict.

export interface TraceStep {
  n: number;
  nombre: string;
  formula: string;
  entradas: Record<string, any>;
  resultado: any;
  unidad: string;
  nota: string;
}
export interface CalcTrace {
  titulo: string;
  descripcion: string;
  fuentes: { nombre: string; origen: string; detalle: string }[];
  supuestos: string[];
  pasos: TraceStep[];
  limitaciones: string[];
}

export interface Overview {
  kpis: {
    anio: number; corte: string; admisiones_total: number; exhibidores: number;
    complejos: number; salas: number; municipios: number; departamentos: number; titulos: number;
  };
  concentracion: { top1_municipio_pct: number; top5_municipios_pct: number; top3_exhibidores_pct: number };
  top_exhibidores: { rank: number; exhibidor: string; admisiones: number }[];
  top_municipios: { rank: number; municipio: string; departamento: string; admisiones: number }[];
  admisiones_mensual: { mes: number; admisiones: number }[];
  serie_anual: { anio: number; asistencia: number }[];
  por_genero: Dist[]; por_clasificacion: Dist[]; por_nacion: Dist[];
  por_dia_semana: Dist[]; por_catalogo_estreno: Dist[];
}
export interface Dist { categoria: string; admisiones: number; pct: number }

export interface DemandResult {
  parametros: { anio_ref: number; banda: string; percentil: number; tasa_referencia: number };
  diagnostico_tasa: any;
  resumen_por_clase: {
    clase: string; etiqueta: string; municipios: number; poblacion_objetivo: number;
    admisiones_realizadas: number; demanda_potencial: number; demanda_insatisfecha: number;
  }[];
  totales: { demanda_potencial: number; demanda_residente_atendida: number; admisiones_totales: number; demanda_insatisfecha: number; cobertura_pct: number };
  top_insatisfecha: MunicipioGeo[];
  trace: CalcTrace;
}

export interface MunicipioGeo {
  cod_mpio: string; municipio: string; departamento: string; clase: string;
  poblacion_objetivo: number; salas_activas: number; admisiones: number;
  demanda_potencial: number; penetracion: number | null; demanda_insatisfecha: number;
  dist_polo_km: number | null; brecha_tipo: string | null;
  lat: number | null; lon: number | null;
}

export interface MunicipioDetail extends MunicipioGeo {
  etiqueta_clase: string; admisiones_realizadas?: number; trace: CalcTrace;
}

export interface Forecast {
  anio_proyeccion: number; tendencia_anual_proyectada: number; anios_base_tendencia: number[];
  pendiente_anual: number;
  escenarios: { central_nivel_estable: number; conservador_sin_2022: number; optimista_con_2022: number };
  intervalo: { bajo: number; alto: number };
  backtest: { predicho_2025: number; real_2025: number; error_pct: number } | null;
  r2_ajuste_con_2022: number; nota_2022: string;
  factores_estacionales: { mes: number; mes_nombre: string; factor: number }[];
  proyeccion_mensual: { mes: number; mes_nombre: string; factor_estacional: number; asistencia_proyectada: number }[];
  historico_anual: { anio: number; asistencia: number; es_covid: boolean; completo: boolean }[];
  trace: CalcTrace;
}

export interface SimResult {
  cod_mpio: string; municipio: string; departamento: string; n_salas: number;
  rendimiento_sala: number; origen_rendimiento: string; captura_estimada: number;
  demanda_nueva: number; redistribucion: number; cuota_mercado: number | null;
  contexto: {
    poblacion_objetivo: number; demanda_potencial: number; demanda_realizada: number;
    demanda_insatisfecha: number; salas_actuales: number; headroom_pct: number;
  };
  lat: number | null; lon: number | null; trace: CalcTrace;
}

export interface MunicipioItem {
  cod_mpio: string; municipio: string; departamento: string;
  salas_activas: number; poblacion_objetivo: number;
}

export interface Catalog {
  fuentes: any[];
  anonimizacion: any;
  reconciliacion_territorial: any;
  procedencia_externa: any;
}

export interface Narrative { narrativa: string; fuente: string; modelo: string | null; error?: string }
