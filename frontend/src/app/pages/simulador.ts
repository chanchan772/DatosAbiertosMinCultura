import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../core/api.service';
import { MunicipioItem, SimResult } from '../core/models';
import { TracePanel } from '../shared/trace-panel';
import { fmt, fmtCompact, pct } from '../shared/format';

@Component({
  selector: 'page-simulador',
  standalone: true,
  imports: [CommonModule, FormsModule, TracePanel],
  template: `
  <header class="section-head">
    <span class="badge violet">Simulador</span>
    <h2 style="margin-top:10px">Exhibidor hipotético: ¿cuántos espectadores captaría?</h2>
    <p>Estima la captura de un exhibidor con N salas en un municipio. El resultado se
    descompone en <b>demanda nueva</b> vs. <b>redistribución</b> (mercado que se le quita a
    competidores) para no dar una cifra engañosa.</p>
  </header>

  <div class="grid" style="grid-template-columns: 340px 1fr; margin-top:18px; align-items:start">
    <div class="card">
      <div class="card-title">Parámetros</div>
      <div class="stack" style="margin-top:14px">
        <div>
          <label class="field">Buscar municipio</label>
          <input type="text" [ngModel]="q()" (ngModelChange)="q.set($event)" placeholder="Ej. Riohacha, Yopal…">
        </div>
        <div>
          <label class="field">Municipio ({{ filtered().length }} coinciden)</label>
          <select [ngModel]="cod()" (ngModelChange)="cod.set($event)" size="6" class="mlist">
            @for (m of filtered().slice(0,120); track m.cod_mpio) {
              <option [value]="m.cod_mpio">{{ titleCase(m.municipio) }} — {{ titleCase(m.departamento) }}
                ({{ m.salas_activas }} salas)</option>
            }
          </select>
        </div>
        <div class="row">
          <div style="flex:1"><label class="field">N.º de salas</label>
            <input type="number" min="1" max="30" [ngModel]="nSalas()" (ngModelChange)="nSalas.set(+$event)"></div>
          <div style="flex:1.4"><label class="field">Banda de edad</label>
            <select [ngModel]="banda()" (ngModelChange)="banda.set($event)">
              <option value="pob_15_30">15–30 años</option>
              <option value="pob_15_45">15–45 años</option>
              <option value="pob_15_60">15–60 años</option>
            </select></div>
        </div>
        <button class="btn primary" (click)="run()" [disabled]="!cod() || loading()">
          {{ loading() ? 'Calculando…' : 'Simular captura' }}</button>
        <div class="filt-note">La banda define la población objetivo (fuente DANE) usada para
        el potencial de mercado y la cuota estimada.</div>
      </div>
    </div>

    <div class="stack">
      @if (res(); as s) {
      <div class="card">
        <div class="row"><h3>{{ titleCase(s.municipio) }}</h3>
          <span class="badge gray">{{ titleCase(s.departamento) }}</span><span class="spacer"></span>
          <span class="badge violet">{{ s.n_salas }} sala(s)</span></div>

        <div class="grid g3" style="margin-top:16px">
          <div class="hero"><div class="kpi-label">Captura estimada</div>
            <div class="hero-v">{{ fmt(s.captura_estimada) }}</div><div class="small muted">espectadores/año</div></div>
          <div class="hero"><div class="kpi-label">Rendimiento por sala</div>
            <div class="hero-v">{{ fmtCompact(s.rendimiento_sala) }}</div><div class="small muted">{{ s.origen_rendimiento }}</div></div>
          <div class="hero"><div class="kpi-label">Cuota de mercado</div>
            <div class="hero-v">{{ s.cuota_mercado != null ? pct(s.cuota_mercado*100) : '—' }}</div>
            <div class="small muted">del potencial local</div></div>
        </div>

        <div class="split" style="margin-top:18px">
          <div class="split-h"><span>Composición de la captura</span></div>
          <div class="split-bar">
            <div class="seg new" [style.flex]="s.demanda_nueva || 0"
              [title]="'Demanda nueva: ' + fmt(s.demanda_nueva)"></div>
            <div class="seg redi" [style.flex]="s.redistribucion || 0"
              [title]="'Redistribución: ' + fmt(s.redistribucion)"></div>
          </div>
          <div class="row wrap small" style="margin-top:8px; gap:16px">
            <span><span class="dot" style="background:var(--teal)"></span> Demanda nueva: <b>{{ fmt(s.demanda_nueva) }}</b></span>
            <span><span class="dot" style="background:var(--amber)"></span> Redistribución: <b>{{ fmt(s.redistribucion) }}</b></span>
          </div>
          @if (s.redistribucion > 0 && s.demanda_nueva === 0) {
            <div class="warn">⚠ En este municipio el mercado ya está saturado: la captura provendría
            de competidores existentes, no de demanda nueva.</div>
          }
        </div>

        <div class="grid g4" style="margin-top:18px">
          <div class="mini"><div class="kpi-label">Potencial local</div><div class="mini-v">{{ fmtCompact(s.contexto.demanda_potencial) }}</div></div>
          <div class="mini"><div class="kpi-label">Realizada</div><div class="mini-v">{{ fmtCompact(s.contexto.demanda_realizada) }}</div></div>
          <div class="mini"><div class="kpi-label">Insatisfecha</div><div class="mini-v">{{ fmtCompact(s.contexto.demanda_insatisfecha) }}</div></div>
          <div class="mini"><div class="kpi-label">Salas actuales</div><div class="mini-v">{{ s.contexto.salas_actuales }}</div></div>
        </div>

        <trace-panel [trace]="s.trace"></trace-panel>

        <div class="row" style="margin-top:12px">
          <button class="btn primary" (click)="narrar(s)" [disabled]="loadingNarr()">
            {{ loadingNarr() ? 'Generando…' : 'Interpretar resultado (IA)' }}</button>
        </div>
        @if (narrativa()) { <p class="narr">{{ narrativa()!.narrativa }}</p>
          <div class="small muted">{{ narrativa()!.fuente === 'deepseek' ? 'DeepSeek ' + narrativa()!.modelo : 'respaldo local' }}</div> }
      </div>
      } @else {
      <div class="card empty">
        <div class="empty-ic">⧉</div>
        <p>Selecciona un municipio y el número de salas para estimar la captura de un exhibidor hipotético.</p>
        <p class="small muted">Sugerencia: prueba un municipio sin oferta (brecha estructural) y otro
        saturado como Bogotá para ver la diferencia entre demanda nueva y redistribución.</p>
      </div>
      }
    </div>
  </div>
  `,
  styles: [`
    .mlist { height: auto; padding: 4px; }
    .filt-note { font-size: 12px; color: var(--ink-soft); background: #faf7ff; border-radius: 10px; padding: 10px 12px; }
    .hero { background: var(--bg); border-radius: 12px; padding: 14px; }
    .hero-v { font-family: var(--display); font-weight: 700; font-size: 26px; margin: 6px 0 2px; }
    .split-bar { display: flex; height: 26px; border-radius: 8px; overflow: hidden; background: var(--bg-alt); }
    .seg { min-width: 2px; transition: flex .4s; } .seg.new { background: var(--teal); } .seg.redi { background: var(--amber); }
    .split-h { font-size: 12.5px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; margin-bottom: 8px; font-weight: 600; }
    .warn { margin-top: 10px; background: rgba(232,163,61,.12); color: #8a5a12; border-radius: 10px; padding: 10px 12px; font-size: 12.5px; }
    .mini { background: var(--bg); border-radius: 10px; padding: 10px 12px; }
    .mini-v { font-family: var(--display); font-weight: 700; font-size: 18px; margin-top: 4px; }
    .empty { text-align: center; padding: 50px 30px; color: var(--ink-soft); }
    .empty-ic { font-size: 40px; color: var(--line-strong); margin-bottom: 10px; }
    .narr { font-size: 14px; line-height: 1.6; margin: 12px 0 4px; white-space: pre-line; }
  `],
})
export class Simulador {
  private api = inject(ApiService);
  municipios = signal<MunicipioItem[]>([]);
  q = signal('');
  cod = signal('');
  nSalas = signal(3);
  banda = signal('pob_15_45');
  res = signal<SimResult | null>(null);
  loading = signal(false);
  narrativa = signal<any>(null);
  loadingNarr = signal(false);
  fmt = fmt; fmtCompact = fmtCompact; pct = pct;

  constructor() {
    this.api.municipios().subscribe((m) => {
      this.municipios.set(m);
      const rioha = m.find((x) => x.municipio.toUpperCase().includes('RIOHACHA'));
      if (rioha) this.cod.set(rioha.cod_mpio);
    });
  }
  onSearch() { /* filtered() reacciona a q() */ }
  filtered = computed(() => {
    const term = this.q().trim().toLowerCase();
    const all = this.municipios();
    if (!term) return all;
    return all.filter((m) => (m.municipio + ' ' + m.departamento).toLowerCase().includes(term));
  });

  run() {
    if (!this.cod()) return;
    this.loading.set(true); this.narrativa.set(null);
    this.api.simulate(this.cod(), this.nSalas(), this.banda()).subscribe({
      next: (r) => { this.res.set(r); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }
  narrar(s: SimResult) {
    this.loadingNarr.set(true);
    const ctx = { municipio: this.titleCase(s.municipio), n_salas: s.n_salas,
      captura_estimada: s.captura_estimada, demanda_nueva: s.demanda_nueva,
      redistribucion: s.redistribucion, cuota_mercado: s.cuota_mercado, contexto: s.contexto };
    this.api.narrative('simulacion', ctx).subscribe({
      next: (r) => { this.narrativa.set(r); this.loadingNarr.set(false); },
      error: () => this.loadingNarr.set(false),
    });
  }
  titleCase(s: string): string {
    return (s || '').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()).replace(/\bD\.c\./i, 'D.C.');
  }
}
