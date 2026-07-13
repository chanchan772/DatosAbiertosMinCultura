import { Component, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CalcTrace } from '../core/models';

/**
 * Panel "¿Cómo se calcula?" — renderiza una traza de cálculo auditable:
 * fuentes, supuestos, pasos (fórmula + entradas + resultado) y limitaciones.
 * Es el mecanismo central de transparencia del tablero.
 */
@Component({
  selector: 'trace-panel',
  standalone: true,
  imports: [CommonModule],
  template: `
  <div class="tp">
    <button class="tp-toggle" (click)="open.set(!open())">
      <span class="tp-ic">{{ open() ? '−' : '+' }}</span>
      <span>¿Cómo se calcula?</span>
      <span class="tp-hint">{{ trace()?.pasos?.length || 0 }} pasos · fuentes y supuestos</span>
    </button>

    @if (open() && trace(); as t) {
    <div class="tp-body">
      <p class="tp-desc">{{ t.descripcion }}</p>

      @if (t.fuentes?.length) {
      <div class="tp-block">
        <h5>Fuentes de datos</h5>
        <ul class="tp-list">
          @for (f of t.fuentes; track f.nombre) {
            <li><b>{{ f.nombre }}</b> — {{ f.origen }}<span *ngIf="f.detalle"> · {{ f.detalle }}</span></li>
          }
        </ul>
      </div>
      }

      <div class="tp-block">
        <h5>Pasos del cálculo</h5>
        <ol class="tp-steps">
          @for (p of t.pasos; track p.n) {
          <li>
            <div class="tp-step-h"><span class="tp-n">{{ p.n }}</span>{{ p.nombre }}</div>
            <code class="tp-formula">{{ p.formula }}</code>
            @if (objectKeys(p.entradas).length) {
            <div class="tp-io">
              @for (k of objectKeys(p.entradas); track k) {
                <span class="tp-kv"><em>{{ k }}</em>: {{ fmtVal(p.entradas[k]) }}</span>
              }
            </div>
            }
            @if (p.resultado !== null && p.resultado !== undefined) {
            <div class="tp-res">= <b>{{ fmtVal(p.resultado) }}</b> <span class="tp-unit">{{ p.unidad }}</span></div>
            }
            @if (p.nota) { <div class="tp-note">{{ p.nota }}</div> }
          </li>
          }
        </ol>
      </div>

      @if (t.supuestos?.length) {
      <div class="tp-block">
        <h5>Supuestos</h5>
        <ul class="tp-list"><li *ngFor="let s of t.supuestos">{{ s }}</li></ul>
      </div>
      }
      @if (t.limitaciones?.length) {
      <div class="tp-block tp-lim">
        <h5>Limitaciones declaradas</h5>
        <ul class="tp-list"><li *ngFor="let l of t.limitaciones">{{ l }}</li></ul>
      </div>
      }
    </div>
    }
  </div>
  `,
  styles: [`
    .tp { border: 1px dashed var(--line-strong); border-radius: 12px; background: #faf9fe; margin-top: 12px; }
    .tp-toggle { display: flex; align-items: center; gap: 10px; width: 100%; background: none; border: none;
      padding: 12px 16px; font-weight: 600; font-size: 13.5px; color: var(--plum-700); }
    .tp-ic { width: 20px; height: 20px; border-radius: 6px; background: var(--plum-700); color: #fff;
      display: grid; place-items: center; font-size: 15px; }
    .tp-hint { margin-left: auto; font-weight: 500; color: var(--muted); font-size: 12px; }
    .tp-body { padding: 4px 18px 18px; border-top: 1px solid var(--line); }
    .tp-desc { color: var(--ink-soft); font-size: 13px; margin: 12px 0; }
    .tp-block { margin: 14px 0; }
    .tp-block h5 { font-family: var(--display); font-size: 12px; text-transform: uppercase; letter-spacing: .05em;
      color: var(--muted); margin: 0 0 8px; }
    .tp-list { margin: 0; padding-left: 18px; font-size: 13px; color: var(--ink-soft); }
    .tp-list li { margin: 4px 0; }
    .tp-steps { list-style: none; margin: 0; padding: 0; counter-reset: none; }
    .tp-steps > li { padding: 10px 0; border-bottom: 1px solid var(--line); }
    .tp-step-h { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 13.5px; }
    .tp-n { width: 20px; height: 20px; border-radius: 6px; background: var(--amber); color: #3a2606;
      display: grid; place-items: center; font-size: 12px; font-weight: 700; }
    .tp-formula { display: block; background: #2a1140; color: #f3e9ff; padding: 8px 12px; border-radius: 8px;
      font-size: 12.5px; margin: 8px 0; white-space: pre-wrap; font-family: 'Space Grotesk', monospace; }
    .tp-io { display: flex; flex-wrap: wrap; gap: 6px; margin: 6px 0; }
    .tp-kv { background: var(--bg-alt); border-radius: 6px; padding: 2px 8px; font-size: 12px; color: var(--ink-soft); }
    .tp-kv em { color: var(--plum-600); font-style: normal; font-weight: 600; }
    .tp-res { font-size: 14px; color: var(--ink); }
    .tp-unit { color: var(--muted); font-size: 12px; }
    .tp-note { font-size: 12px; color: var(--muted); font-style: italic; margin-top: 4px; }
    .tp-lim h5 { color: var(--coral-dark); }
  `],
})
export class TracePanel {
  trace = input<CalcTrace | null | undefined>();
  open = signal(false);
  objectKeys(o: any): string[] { return o ? Object.keys(o) : []; }
  fmtVal(v: any): string {
    if (v === null || v === undefined) return '—';
    if (typeof v === 'number') return v.toLocaleString('es-CO', { maximumFractionDigits: 4 });
    if (Array.isArray(v)) return v.map((x) => this.fmtVal(x)).join(', ');
    if (typeof v === 'object') return Object.entries(v).map(([k, x]) => `${k}: ${this.fmtVal(x)}`).join('; ');
    return String(v);
  }
}
