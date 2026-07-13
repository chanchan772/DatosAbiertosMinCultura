import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../core/api.service';
import { Overview } from '../core/models';
import { BarChart, LineChart, DonutChart, Bar } from '../shared/charts';
import { fmt, fmtCompact, pct } from '../shared/format';

@Component({
  selector: 'page-panorama',
  standalone: true,
  imports: [CommonModule, BarChart, LineChart, DonutChart],
  template: `
  <header class="section-head">
    <span class="badge amber">Panorama nacional</span>
    <h2 style="margin-top:10px">El consumo de cine en Colombia</h2>
    <p>Magnitud, evolución histórica y concentración del acceso, a partir del detalle
    transaccional del SIREC. El detalle 2026 es un año parcial (corte {{ d()?.kpis?.corte }}).</p>
  </header>

  @if (!d()) {
    <div class="grid g4" style="margin-top:18px">
      @for (i of [1,2,3,4]; track i) { <div class="card"><div class="skeleton" style="height:52px"></div></div> }
    </div>
  } @else {
  <div class="stack" style="margin-top:18px">

    <div class="grid g4">
      <div class="card kpi"><div class="kpi-label">Admisiones 2026 (parc.)</div>
        <div class="kpi-value">{{ fmtCompact(d()!.kpis.admisiones_total) }}</div>
        <div class="small muted">{{ fmt(d()!.kpis.admisiones_total) }} espectadores</div></div>
      <div class="card kpi"><div class="kpi-label">Salas activas</div>
        <div class="kpi-value">{{ fmt(d()!.kpis.salas) }}</div>
        <div class="small muted">{{ d()!.kpis.complejos }} complejos · {{ d()!.kpis.exhibidores }} exhibidores</div></div>
      <div class="card kpi"><div class="kpi-label">Municipios con cine</div>
        <div class="kpi-value">{{ d()!.kpis.municipios }}</div>
        <div class="small muted">de 1.122 · {{ d()!.kpis.departamentos }} departamentos</div></div>
      <div class="card kpi"><div class="kpi-label">Títulos exhibidos</div>
        <div class="kpi-value">{{ d()!.kpis.titulos }}</div>
        <div class="small muted">catálogo + estrenos</div></div>
    </div>

    <div class="grid" style="grid-template-columns: 1.6fr 1fr">
      <div class="card">
        <div class="card-title">Asistencia nacional anual (2007–2026)</div>
        <div class="card-sub">Serie diaria agregada. El desplome 2020–2021 corresponde al cierre de salas por COVID-19.</div>
        <line-chart [data]="serie()" color="var(--plum-600)" style="margin-top:10px"></line-chart>
        <div class="row wrap small muted" style="margin-top:6px">
          <span><span class="dot" style="background:var(--coral)"></span> años COVID (intervención del modelo)</span>
        </div>
      </div>
      <div class="card">
        <div class="card-title">Concentración del acceso</div>
        <div class="card-sub">Señal central de inequidad territorial y empresarial.</div>
        <div class="conc">
          <div class="conc-row"><span>{{ topMuni() }}</span>
            <b>{{ pct(d()!.concentracion.top1_municipio_pct) }}</b>
            <small>de las admisiones ocurren en un solo municipio</small></div>
          <div class="conc-row"><span>Top 5 municipios</span>
            <b>{{ pct(d()!.concentracion.top5_municipios_pct) }}</b>
            <small>más de la mitad en 5 ciudades</small></div>
          <div class="conc-row"><span>Top 3 exhibidores</span>
            <b>{{ pct(d()!.concentracion.top3_exhibidores_pct) }}</b>
            <small>del mercado en 3 empresas</small></div>
        </div>
      </div>
    </div>

    <div class="grid g3">
      <div class="card">
        <div class="card-title">Origen de la producción</div>
        <div class="card-sub">Participación del cine colombiano vs. extranjero.</div>
        <donut-chart [data]="nacion()" centerLabel="admisiones" style="margin-top:12px"></donut-chart>
      </div>
      <div class="card">
        <div class="card-title">Admisiones por género</div>
        <bar-chart [data]="genero()" style="margin-top:12px"></bar-chart>
      </div>
      <div class="card">
        <div class="card-title">Estacionalidad semanal</div>
        <div class="card-sub">Admisiones por día de exhibición.</div>
        <bar-chart [data]="dia()" style="margin-top:12px"></bar-chart>
      </div>
    </div>

    <div class="grid g2">
      <div class="card">
        <div class="card-title">Top exhibidores <span class="badge gray">seudonimizados</span></div>
        <div class="card-sub">Identidades tokenizadas (HMAC-SHA256); los agregados no cambian.</div>
        <table class="data" style="margin-top:8px">
          <thead><tr><th>#</th><th>Exhibidor</th><th class="num">Admisiones 2026</th><th class="num">Cuota</th></tr></thead>
          <tbody>
          @for (e of d()!.top_exhibidores; track e.exhibidor) {
            <tr><td class="muted">{{ e.rank }}</td><td class="mono">{{ e.exhibidor }}</td>
              <td class="num">{{ fmt(e.admisiones) }}</td>
              <td class="num">{{ pct(100*e.admisiones/d()!.kpis.admisiones_total) }}</td></tr>
          }
          </tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-title">Top municipios por admisiones</div>
        <div class="card-sub">Concentración geográfica del consumo.</div>
        <table class="data" style="margin-top:8px">
          <thead><tr><th>#</th><th>Municipio</th><th>Departamento</th><th class="num">Admisiones</th></tr></thead>
          <tbody>
          @for (m of d()!.top_municipios; track m.municipio) {
            <tr><td class="muted">{{ m.rank }}</td><td>{{ titleCase(m.municipio) }}</td>
              <td class="muted small">{{ titleCase(m.departamento) }}</td>
              <td class="num">{{ fmt(m.admisiones) }}</td></tr>
          }
          </tbody>
        </table>
      </div>
    </div>

    <div class="card ai">
      <div class="row">
        <div class="card-title">Lectura ejecutiva automática <span class="badge violet">IA · DeepSeek</span></div>
        <span class="spacer"></span>
        <button class="btn primary" (click)="narrar()" [disabled]="loadingNarr()">
          {{ loadingNarr() ? 'Generando…' : 'Generar resumen' }}</button>
      </div>
      @if (narrativa()) {
        <p class="narr">{{ narrativa()!.narrativa }}</p>
        <div class="small muted">Fuente: {{ narrativa()!.fuente === 'deepseek' ? 'DeepSeek ' + narrativa()!.modelo : 'respaldo local' }}
        · redactado a partir de las cifras calculadas, sin inventar datos.</div>
      } @else {
        <p class="muted small" style="margin-top:8px">Genera una síntesis en lenguaje natural del panorama para tomadores de decisión.</p>
      }
    </div>

  </div>
  }
  `,
  styles: [`
    .kpi { display: flex; flex-direction: column; gap: 8px; }
    .conc { display: flex; flex-direction: column; gap: 14px; margin-top: 14px; }
    .conc-row { display: grid; grid-template-columns: 1fr auto; align-items: baseline; row-gap: 2px;
      padding-bottom: 12px; border-bottom: 1px solid var(--line); }
    .conc-row span { font-size: 13px; color: var(--ink-soft); }
    .conc-row b { font-family: var(--display); font-size: 26px; color: var(--coral-dark); }
    .conc-row small { grid-column: 1 / -1; color: var(--muted); font-size: 12px; }
    .ai { background: linear-gradient(180deg, #faf7ff, #fff); }
    .narr { font-size: 14.5px; line-height: 1.6; color: var(--ink); margin: 12px 0 6px; white-space: pre-line; }
  `],
})
export class Panorama {
  private api = inject(ApiService);
  d = signal<Overview | null>(null);
  narrativa = signal<any>(null);
  loadingNarr = signal(false);
  fmt = fmt; fmtCompact = fmtCompact; pct = pct;

  constructor() { this.api.overview().subscribe((r) => this.d.set(r)); }

  serie = computed(() => (this.d()?.serie_anual || []).map((s) => ({ x: s.anio, y: s.asistencia, flag: [2020, 2021].includes(s.anio) })));
  nacion = computed<Bar[]>(() => (this.d()?.por_nacion || []).map((x) => ({
    label: x.categoria, value: x.admisiones,
    color: x.categoria === 'Colombiana' ? 'var(--amber)' : x.categoria === 'Extranjera' ? 'var(--plum-600)' : 'var(--muted)',
  })));
  genero = computed<Bar[]>(() => (this.d()?.por_genero || []).map((x) => ({ label: x.categoria, value: x.admisiones })));
  dia = computed<Bar[]>(() => (this.d()?.por_dia_semana || []).map((x) => ({ label: x.categoria, value: x.admisiones, color: 'var(--teal)' })));
  topMuni = computed(() => this.titleCase(this.d()?.top_municipios?.[0]?.municipio || 'Bogotá'));

  titleCase(s: string): string {
    return (s || '').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()).replace(/\bD\.c\./i, 'D.C.');
  }
  narrar() {
    const d = this.d(); if (!d) return;
    this.loadingNarr.set(true);
    const ctx = {
      admisiones_2026_parcial: d.kpis.admisiones_total, municipios_con_cine: d.kpis.municipios,
      total_municipios_pais: 1122, concentracion: d.concentracion,
      participacion_cine_colombiano_pct: d.por_nacion.find((x) => x.categoria === 'Colombiana')?.pct,
    };
    this.api.narrative('nacional', ctx).subscribe({
      next: (r) => { this.narrativa.set(r); this.loadingNarr.set(false); },
      error: () => this.loadingNarr.set(false),
    });
  }
}
