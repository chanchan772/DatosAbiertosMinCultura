// Utilidades de formato numérico en convención colombiana (miles con punto).

export function fmt(n: number | null | undefined, decimals = 0): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return n.toLocaleString('es-CO', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

export function fmtCompact(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  const a = Math.abs(n);
  if (a >= 1e6) return (n / 1e6).toLocaleString('es-CO', { maximumFractionDigits: 2 }) + ' M';
  if (a >= 1e3) return (n / 1e3).toLocaleString('es-CO', { maximumFractionDigits: 1 }) + ' k';
  return fmt(n);
}

export function pct(n: number | null | undefined, decimals = 1): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return n.toLocaleString('es-CO', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + '%';
}

// Colores por clase de municipio (consistente en todo el tablero).
export const CLASE_COLOR: Record<string, string> = {
  sin_oferta: 'var(--coral)',
  subatendido: 'var(--amber)',
  saturado: 'var(--teal)',
};
export const CLASE_LABEL: Record<string, string> = {
  sin_oferta: 'Sin oferta (brecha estructural)',
  subatendido: 'Con oferta, subatendido',
  saturado: 'Saturado / polo de atracción',
};
