import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../core/api.service';

@Component({
  selector: 'page-metodologia',
  standalone: true,
  imports: [CommonModule],
  template: `
  <header class="section-head">
    <span class="badge violet">Transparencia</span>
    <h2 style="margin-top:10px">Metodología y parámetros</h2>
    <p>Toda la lógica de cálculo, sus fuentes, supuestos y limitaciones en un solo lugar
    auditable. Los parámetros que afectan resultados están expuestos, no ocultos en el código.</p>
  </header>

  @if (m(); as data) {
  <div class="card" style="margin-top:18px">
    <div class="card-title">Parámetros del modelo</div>
    <div class="card-sub">Editables en un único archivo (methodology.py); cambian de forma trazable los resultados.</div>
    <div class="grid g3" style="margin-top:14px">
      @for (p of params(); track p.k) {
        <div class="param"><div class="param-k">{{ p.k }}</div><div class="param-v">{{ p.v }}</div></div>
      }
    </div>
  </div>

  <div class="stack" style="margin-top:18px">
    @for (mod of modules(); track mod.key) {
    <div class="card mod">
      <div class="mod-h">
        <span class="mod-badge">{{ mod.idx }}</span>
        <div><h3>{{ mod.titulo }}</h3><div class="small muted">{{ mod.v.pregunta }}</div></div>
      </div>
      <div class="mod-grid">
        <div><div class="fl-h">Fuente</div><p>{{ mod.v.fuente }}</p></div>
        <div><div class="fl-h">Fórmula</div><pre class="formula">{{ mod.v.formula }}</pre></div>
      </div>
      <div class="mod-grid">
        <div><div class="fl-h">Supuestos</div>
          <ul><li *ngFor="let s of mod.v.supuestos">{{ s }}</li></ul></div>
        <div><div class="fl-h lim">Limitaciones</div>
          <ul><li *ngFor="let l of mod.v.limitaciones">{{ l }}</li></ul></div>
      </div>
    </div>
    }
  </div>
  } @else {
    <div class="card" style="margin-top:18px"><div class="skeleton" style="height:280px"></div></div>
  }
  `,
  styles: [`
    .param { background: var(--bg); border-radius: 10px; padding: 12px 14px; }
    .param-k { font-size: 12px; color: var(--muted); font-family: var(--sans); }
    .param-v { font-family: var(--display); font-weight: 600; font-size: 16px; margin-top: 4px; word-break: break-word; }
    .mod-h { display: flex; gap: 12px; align-items: center; margin-bottom: 14px; }
    .mod-badge { width: 34px; height: 34px; border-radius: 10px; background: var(--plum-700); color: #fff;
      display: grid; place-items: center; font-family: var(--display); font-weight: 700; flex: none; }
    .mod-grid { display: grid; grid-template-columns: 1fr 1.3fr; gap: 20px; margin: 14px 0; }
    @media (max-width: 820px) { .mod-grid { grid-template-columns: 1fr; } }
    .fl-h { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 600; margin-bottom: 6px; }
    .fl-h.lim { color: var(--coral-dark); }
    .mod p { font-size: 13.5px; color: var(--ink-soft); margin: 0; line-height: 1.55; }
    .formula { background: #2a1140; color: #f3e9ff; padding: 12px 14px; border-radius: 10px; font-size: 12.5px;
      white-space: pre-wrap; font-family: 'Space Grotesk', monospace; margin: 0; line-height: 1.5; }
    .mod ul { margin: 0; padding-left: 18px; font-size: 13px; color: var(--ink-soft); }
    .mod ul li { margin: 5px 0; }
  `],
})
export class Metodologia {
  private api = inject(ApiService);
  m = signal<any>(null);
  private titulos: Record<string, string> = {
    panorama_nacional: 'Panorama nacional', demanda_potencial: 'Demanda potencial',
    demanda_insatisfecha: 'Demanda insatisfecha', estacionalidad_proyeccion: 'Estacionalidad y proyección',
    captura_exhibidor: 'Captura por exhibidor',
  };
  constructor() { this.api.methodology().subscribe((r) => this.m.set(r)); }
  params = computed(() => Object.entries(this.m()?.parametros || {}).map(([k, v]) => ({
    k, v: typeof v === 'object' ? JSON.stringify(v) : String(v),
  })));
  modules = computed(() => {
    const met = this.m()?.metodologia || {};
    return Object.entries(met).map(([key, v]: any, i) => ({
      key, v, idx: i + 1, titulo: this.titulos[key] || key,
    }));
  });
}
