import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../core/api.service';
import { Forecast } from '../core/models';
import { BarChart, LineChart, Bar } from '../shared/charts';
import { TracePanel } from '../shared/trace-panel';
import { fmt, fmtCompact } from '../shared/format';

@Component({
  selector: 'page-proyeccion',
  standalone: true,
  imports: [CommonModule, BarChart, LineChart, TracePanel],
  template: `
  <header class="section-head">
    <span class="badge teal">Series de tiempo</span>
    <h2 style="margin-top:10px">Estacionalidad y proyección a 2027</h2>
    <p>Descomposición clásica de la serie diaria nacional: tendencia (ajustada sobre años
    completos post-COVID) × factor estacional por mes. Procedimiento aritmético y auditable.</p>
  </header>

  @if (f(); as r) {
  <div class="grid g4" style="margin-top:18px">
    <div class="card kpi"><div class="kpi-label">Proyección central {{ r.anio_proyeccion }}</div>
      <div class="kpi-value">{{ fmtCompact(r.tendencia_anual_proyectada) }}</div>
      <div class="small muted">nivel estable 2023–2025 · {{ fmt(r.tendencia_anual_proyectada) }}</div></div>
    <div class="card kpi"><div class="kpi-label">Rango de escenarios</div>
      <div class="kpi-value" style="font-size:22px">{{ fmtCompact(r.intervalo.bajo) }}–{{ fmtCompact(r.intervalo.alto) }}</div>
      <div class="small muted">conservador ↔ optimista</div></div>
    <div class="card kpi"><div class="kpi-label">Error de validación</div>
      <div class="kpi-value" [style.color]="(r.backtest?.error_pct||0) > 10 ? 'var(--coral-dark)':'var(--teal-dark)'">
        {{ r.backtest ? r.backtest.error_pct + '%' : '—' }}</div>
      <div class="small muted">backtest a 1 año (2025)</div></div>
    <div class="card kpi"><div class="kpi-label">Mes pico</div>
      <div class="kpi-value">{{ pico().mes_nombre }}</div>
      <div class="small muted">factor {{ pico().factor.toFixed(2) }}× el promedio</div></div>
  </div>

  <div class="card note-2022" style="margin-top:18px">
    <div class="row" style="align-items:flex-start; gap:14px">
      <div class="n-ic">⚠</div>
      <div style="flex:1">
        <div class="card-title">Por qué se reporta un rango y no una cifra única</div>
        <p class="small" style="margin:8px 0 12px; color:var(--ink-soft)">{{ r.nota_2022 }}</p>
        <div class="scen">
          <div class="sc sc-c"><span>Conservador (sin 2022)</span><b>{{ fmtCompact(r.escenarios.conservador_sin_2022) }}</b></div>
          <div class="sc sc-b"><span>Central (nivel estable)</span><b>{{ fmtCompact(r.escenarios.central_nivel_estable) }}</b></div>
          <div class="sc sc-o"><span>Optimista (con 2022)</span><b>{{ fmtCompact(r.escenarios.optimista_con_2022) }}</b></div>
        </div>
        <div class="small muted" style="margin-top:10px">
          Backtest: ajustando 2022–2024 y prediciendo 2025 el modelo lineal da
          {{ r.backtest ? fmt(r.backtest.predicho_2025) : '—' }} vs. {{ r.backtest ? fmt(r.backtest.real_2025) : '—' }} real
          ({{ r.backtest?.error_pct }}% de error). R² del ajuste con 2022 = {{ r.r2_ajuste_con_2022 }} (bajo).
        </div>
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:18px">
    <div class="card-title">Asistencia nacional histórica (2007–2026)</div>
    <div class="card-sub">Puntos rojos = 2020–2021 (COVID), excluidos del ajuste de tendencia.</div>
    <line-chart [data]="serie()" color="var(--plum-600)" style="margin-top:10px"></line-chart>
  </div>

  <div class="grid g2" style="margin-top:18px">
    <div class="card">
      <div class="card-title">Factores estacionales por mes</div>
      <div class="card-sub">1.0 = mes promedio. Pico en vacaciones escolares (jun–jul).</div>
      <bar-chart [data]="factores()" style="margin-top:12px"></bar-chart>
    </div>
    <div class="card">
      <div class="card-title">Proyección mensual {{ r.anio_proyeccion }}</div>
      <div class="card-sub">tendencia/12 × factor estacional de cada mes.</div>
      <line-chart [data]="proyMensual()" color="var(--teal)" style="margin-top:10px"></line-chart>
    </div>
  </div>

  <div class="card" style="margin-top:18px">
    <div class="card-title">Detalle de la proyección</div>
    <table class="data" style="margin-top:8px">
      <thead><tr><th>Mes</th><th class="num">Factor estacional</th><th class="num">Asistencia proyectada</th></tr></thead>
      <tbody>
      @for (p of r.proyeccion_mensual; track p.mes) {
        <tr><td>{{ p.mes_nombre }}</td><td class="num">{{ p.factor_estacional.toFixed(3) }}</td>
          <td class="num">{{ fmt(p.asistencia_proyectada) }}</td></tr>
      }
      </tbody>
      <tfoot><tr><td><b>Total {{ r.anio_proyeccion }}</b></td><td></td>
        <td class="num"><b>{{ fmt(totalProy()) }}</b></td></tr></tfoot>
    </table>
    <trace-panel [trace]="r.trace"></trace-panel>
  </div>
  } @else {
    <div class="card" style="margin-top:18px"><div class="skeleton" style="height:300px"></div></div>
  }
  `,
  styles: [`
    .kpi { display: flex; flex-direction: column; gap: 6px; }
    table.data tfoot td { border-top: 2px solid var(--line-strong); border-bottom: none; padding-top: 10px; }
    .note-2022 { background: linear-gradient(180deg, #fff9ef, #fff); border-color: rgba(232,163,61,.35); }
    .n-ic { width: 34px; height: 34px; border-radius: 10px; background: rgba(232,163,61,.16); color: #97671a;
      display: grid; place-items: center; font-size: 18px; flex: none; }
    .scen { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    @media (max-width: 720px) { .scen { grid-template-columns: 1fr; } }
    .sc { background: var(--bg); border-radius: 10px; padding: 10px 12px; border-left: 3px solid var(--muted); }
    .sc span { font-size: 12px; color: var(--muted); display: block; }
    .sc b { font-family: var(--display); font-size: 18px; }
    .sc-c { border-left-color: var(--coral); } .sc-b { border-left-color: var(--plum-600); } .sc-o { border-left-color: var(--teal); }
  `],
})
export class Proyeccion {
  private api = inject(ApiService);
  f = signal<Forecast | null>(null);
  fmt = fmt; fmtCompact = fmtCompact;

  constructor() { this.api.forecast(2027).subscribe((r) => this.f.set(r)); }

  serie = computed(() => (this.f()?.historico_anual || []).map((s) => ({ x: s.anio, y: s.asistencia, flag: s.es_covid })));
  factores = computed<Bar[]>(() => (this.f()?.factores_estacionales || []).map((x) => ({
    label: x.mes_nombre, value: x.factor,
    color: x.factor >= 1.2 ? 'var(--coral)' : x.factor >= 1 ? 'var(--amber)' : 'var(--plum-600)',
  })));
  proyMensual = computed(() => (this.f()?.proyeccion_mensual || []).map((p) => ({ x: p.mes_nombre, y: p.asistencia_proyectada })));
  pico = computed(() => {
    const fs = this.f()?.factores_estacionales || [{ mes_nombre: '—', factor: 1 } as any];
    return fs.reduce((a, b) => (b.factor > a.factor ? b : a));
  });
  totalProy = computed(() => (this.f()?.proyeccion_mensual || []).reduce((s, p) => s + p.asistencia_proyectada, 0));
}
