import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../core/api.service';
import { DemandResult, MunicipioGeo, MunicipioDetail } from '../core/models';
import { TracePanel } from '../shared/trace-panel';
import { AiInterpret } from '../shared/ai-interpret';
import { fmt, fmtCompact, pct, CLASE_COLOR, CLASE_LABEL } from '../shared/format';

@Component({
  selector: 'page-brechas',
  standalone: true,
  imports: [CommonModule, TracePanel, AiInterpret],
  template: `
  <header class="section-head">
    <span class="badge coral">Demanda insatisfecha</span>
    <h2 style="margin-top:10px">Mapa de brechas de acceso al cine</h2>
    <p>¿Qué municipios tienen demanda potencial que hoy no se atiende? Se clasifica cada
    territorio en tres grupos con fórmulas distintas y explícitas —nunca se mezclan métricas.</p>
  </header>

  <div class="card tight filters">
    <div>
      <label class="field">Población objetivo (banda de edad · fuente DANE)</label>
      <select [value]="banda()" (change)="onBanda($any($event.target).value)">
        <option value="pob_15_30">15–30 años (jóvenes)</option>
        <option value="pob_15_45">15–45 años (núcleo de asistencia)</option>
        <option value="pob_15_60">15–60 años (amplia)</option>
      </select>
    </div>
    <div class="filt-note">
      La banda de edad es un <b>filtro con respaldo de datos</b>: define la población que
      concentra la propensión a asistir al cine. Cambia la demanda potencial de cada municipio
      (proyecciones DANE por edad simple).
    </div>
  </div>

  @if (dm(); as r) {
  <div class="grid g3" style="margin-top:18px">
    @for (c of r.resumen_por_clase; track c.clase) {
    <div class="card clase" [style.borderTopColor]="color(c.clase)">
      <div class="row"><span class="dot" [style.background]="color(c.clase)"></span>
        <span class="clase-t">{{ c.etiqueta }}</span></div>
      <div class="kpi-value" style="margin:8px 0 2px">{{ fmt(c.municipios) }}</div>
      <div class="small muted">municipios</div>
      <div class="clase-ins">Demanda insatisfecha: <b>{{ fmtCompact(c.demanda_insatisfecha) }}</b></div>
    </div>
    }
  </div>

  <div class="grid" style="grid-template-columns: 1.15fr 1fr; margin-top:18px; align-items:start">
    <div class="card">
      <div class="card-title">Mapa municipal de brechas</div>
      <div class="card-sub">Tamaño = demanda insatisfecha · color = clase. Clic en un municipio para el detalle.</div>
      <svg viewBox="0 0 460 640" class="map" (click)="clearSel()">
        @for (p of points(); track p.cod_mpio) {
          <circle [attr.cx]="p.cx" [attr.cy]="p.cy" [attr.r]="p.r"
            [attr.fill]="p.color" [attr.fill-opacity]="p.op"
            [attr.stroke]="sel()?.cod_mpio === p.cod_mpio ? 'var(--ink)' : 'none'"
            stroke-width="1.5" class="mdot"
            (click)="select(p.cod_mpio); $event.stopPropagation()">
            <title>{{ titleCase(p.municipio) }} — {{ fmtCompact(p.demanda_insatisfecha) }} insatisf.</title>
          </circle>
        }
      </svg>
      <div class="row wrap small" style="margin-top:8px">
        @for (k of clases; track k) {
          <span class="row" style="gap:6px"><span class="dot" [style.background]="color(k)"></span>{{ label(k) }}</span>
        }
      </div>
    </div>

    <div class="stack">
      @if (sel(); as s) {
      <div class="card sel">
        <div class="row"><span class="badge" [class.coral]="s.clase==='sin_oferta'" [class.amber]="s.clase==='subatendido'"
          [class.teal]="s.clase==='saturado'">{{ s.etiqueta_clase }}</span>
          <span class="spacer"></span><button class="btn" (click)="clearSel()">✕</button></div>
        <h3 style="margin:10px 0 2px">{{ titleCase(s.municipio) }}</h3>
        <div class="small muted">{{ titleCase(s.departamento) }} · DIVIPOLA {{ s.cod_mpio }}</div>
        @if (s.clase === 'sin_oferta' && s.brecha_tipo) {
          <div class="brecha-tag" [class.aparente]="s.brecha_tipo==='conurbacion'">
            {{ s.brecha_tipo === 'conurbacion'
              ? '◐ Brecha aparente por conurbación — polo con cine a ' + (s.dist_polo_km|number:'1.0-0') + ' km'
              : '● Brecha real por aislamiento — polo más cercano a ' + (s.dist_polo_km|number:'1.0-0') + ' km' }}
          </div>
        }
        <div class="grid g2" style="margin-top:14px; gap:12px">
          <div class="mini"><div class="kpi-label">Demanda potencial</div><div class="mini-v">{{ fmtCompact(s.demanda_potencial) }}</div></div>
          <div class="mini"><div class="kpi-label">Realizada</div><div class="mini-v">{{ fmtCompact(s.admisiones_realizadas ?? s.admisiones) }}</div></div>
          <div class="mini"><div class="kpi-label">Insatisfecha</div><div class="mini-v" style="color:var(--coral-dark)">{{ fmtCompact(s.demanda_insatisfecha) }}</div></div>
          <div class="mini"><div class="kpi-label">Salas activas</div><div class="mini-v">{{ s.salas_activas }}</div></div>
        </div>
        <trace-panel [trace]="s.trace"></trace-panel>
        <div class="row" style="margin-top:12px">
          <button class="btn primary" (click)="narrar(s)" [disabled]="loadingNarr()">
            {{ loadingNarr() ? 'Generando…' : 'Lectura ejecutiva (IA)' }}</button>
        </div>
        @if (narrativa()) { <p class="narr">{{ narrativa()!.narrativa }}</p>
          <div class="small muted">{{ narrativa()!.fuente === 'deepseek' ? 'DeepSeek ' + narrativa()!.modelo : 'respaldo local' }}</div> }
      </div>
      } @else {
      <div class="card">
        <div class="card-title">Municipios con mayor demanda insatisfecha</div>
        <table class="data" style="margin-top:8px">
          <thead><tr><th>Municipio</th><th>Clase</th><th class="num">Insatisf.</th></tr></thead>
          <tbody>
          @for (m of r.top_insatisfecha.slice(0,14); track m.cod_mpio) {
            <tr (click)="select(m.cod_mpio)" style="cursor:pointer">
              <td>{{ titleCase(m.municipio) }}<div class="small muted">{{ titleCase(m.departamento) }}</div></td>
              <td><span class="dot" [style.background]="color(m.clase)"></span></td>
              <td class="num">{{ fmtCompact(m.demanda_insatisfecha) }}</td></tr>
          }
          </tbody>
        </table>
      </div>
      }

      <div class="card">
        <div class="card-title">Totales nacionales</div>
        <div class="tot">
          <div><span>Demanda potencial residente</span><b>{{ fmtCompact(r.totales.demanda_potencial) }}</b></div>
          <div><span>Residente atendida localmente</span><b>{{ fmtCompact(r.totales.demanda_residente_atendida) }}</b></div>
          <div><span>Insatisfecha</span><b style="color:var(--coral-dark)">{{ fmtCompact(r.totales.demanda_insatisfecha) }}</b></div>
          <div><span>Cobertura residente</span><b>{{ pct(r.totales.cobertura_pct) }}</b></div>
        </div>
        <div class="small muted" style="margin-top:6px">Cobertura = (potencial − insatisfecha) / potencial.
        Las admisiones totales ({{ fmtCompact(r.totales.admisiones_totales) }}) incluyen desplazamiento entre municipios
        y no son comparables contra el potencial residente.</div>
        <trace-panel [trace]="r.trace"></trace-panel>
      </div>
    </div>
  </div>

  <div style="margin-top:18px">
    <ai-interpret [modulo]="'brechas'" [datos]="interpretData()"
      subtitulo="Interpretación de las brechas de acceso y la demanda insatisfecha."></ai-interpret>
  </div>
  } @else {
    <div class="card" style="margin-top:18px"><div class="skeleton" style="height:360px"></div></div>
  }
  `,
  styles: [`
    .filters { display: grid; grid-template-columns: 320px 1fr; gap: 18px; align-items: center; margin-top: 16px; }
    .filt-note { font-size: 12.5px; color: var(--ink-soft); background: #faf7ff; border-radius: 10px; padding: 10px 14px; }
    .clase { border-top: 3px solid; }
    .clase-t { font-weight: 600; font-size: 13.5px; }
    .clase-ins { margin-top: 12px; font-size: 13px; color: var(--ink-soft); border-top: 1px solid var(--line); padding-top: 10px; }
    .map { width: 100%; height: 620px; background: radial-gradient(circle at 40% 30%, #faf9fe, #f1eff8); border-radius: 12px; }
    .mdot { cursor: pointer; transition: fill-opacity .15s; }
    .mdot:hover { fill-opacity: 1 !important; }
    .mini { background: var(--bg); border-radius: 10px; padding: 10px 12px; }
    .mini-v { font-family: var(--display); font-weight: 700; font-size: 20px; margin-top: 4px; }
    .brecha-tag { margin-top: 10px; font-size: 12px; font-weight: 600; padding: 8px 12px; border-radius: 10px;
      background: rgba(229,72,77,.1); color: var(--coral-dark); }
    .brecha-tag.aparente { background: rgba(232,163,61,.14); color: #8a5a12; }
    .tot { display: flex; flex-direction: column; gap: 10px; margin: 12px 0; }
    .tot > div { display: flex; justify-content: space-between; font-size: 13.5px; color: var(--ink-soft);
      border-bottom: 1px solid var(--line); padding-bottom: 8px; }
    .tot b { font-family: var(--display); font-size: 15px; color: var(--ink); }
    .narr { font-size: 14px; line-height: 1.6; margin: 12px 0 4px; white-space: pre-line; }
  `],
})
export class Brechas {
  private api = inject(ApiService);
  banda = signal('pob_15_45');
  dm = signal<DemandResult | null>(null);
  mapData = signal<MunicipioGeo[]>([]);
  sel = signal<MunicipioDetail | null>(null);
  narrativa = signal<any>(null);
  loadingNarr = signal(false);
  clases = ['sin_oferta', 'subatendido', 'saturado'];
  fmt = fmt; fmtCompact = fmtCompact; pct = pct;
  color = (c: string) => CLASE_COLOR[c] || 'var(--muted)';
  label = (c: string) => CLASE_LABEL[c] || c;

  interpretData = computed(() => {
    const r = this.dm(); if (!r) return {};
    return {
      banda: this.banda(), parametros: r.parametros, totales: r.totales,
      resumen_por_clase: r.resumen_por_clase,
      top_municipios_insatisfecha: r.top_insatisfecha?.slice(0, 15),
    };
  });

  // límites geográficos de Colombia continental para la proyección
  private LAT = [-4.3, 13.5]; private LON = [-79.2, -66.8]; private W = 460; private H = 640;

  constructor() { this.load(); }
  load() {
    this.api.demand(2025, this.banda()).subscribe((r) => this.dm.set(r));
    this.api.demandMap(2025, this.banda()).subscribe((r) => this.mapData.set(r.municipios));
  }
  onBanda(v: string) { this.banda.set(v); this.sel.set(null); this.narrativa.set(null); this.load(); }

  points = computed(() => {
    const data = this.mapData();
    const maxI = Math.max(1, ...data.map((m) => m.demanda_insatisfecha));
    return data.filter((m) => m.lat != null && m.lon != null).map((m) => {
      const cx = ((m.lon! - this.LON[0]) / (this.LON[1] - this.LON[0])) * this.W;
      const cy = ((this.LAT[1] - m.lat!) / (this.LAT[1] - this.LAT[0])) * this.H;
      const r = m.demanda_insatisfecha > 0 ? 2.5 + Math.sqrt(m.demanda_insatisfecha / maxI) * 15 : 2;
      return { ...m, cx: +cx.toFixed(1), cy: +cy.toFixed(1), r: +r.toFixed(1),
        color: this.color(m.clase), op: m.demanda_insatisfecha > 0 ? 0.72 : 0.5 };
    }).sort((a, b) => b.r - a.r);
  });

  select(cod: string) {
    this.narrativa.set(null);
    this.api.municipio(cod, 2025, this.banda()).subscribe((d) => this.sel.set(d));
  }
  clearSel() { this.sel.set(null); this.narrativa.set(null); }

  narrar(s: MunicipioDetail) {
    this.loadingNarr.set(true);
    const ctx = { municipio: this.titleCase(s.municipio), departamento: this.titleCase(s.departamento),
      clase: s.clase, etiqueta_clase: s.etiqueta_clase, demanda_potencial: s.demanda_potencial,
      demanda_realizada: s.admisiones_realizadas ?? s.admisiones, demanda_insatisfecha: s.demanda_insatisfecha,
      salas_activas: s.salas_activas };
    this.api.narrative('territorio', ctx).subscribe({
      next: (r) => { this.narrativa.set(r); this.loadingNarr.set(false); },
      error: () => this.loadingNarr.set(false),
    });
  }
  titleCase(s: string): string {
    return (s || '').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()).replace(/\bD\.c\./i, 'D.C.');
  }
}
