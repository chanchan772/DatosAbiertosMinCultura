import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../core/api.service';
import { Catalog } from '../core/models';
import { fmt } from '../shared/format';

@Component({
  selector: 'page-datos',
  standalone: true,
  imports: [CommonModule],
  template: `
  <header class="section-head">
    <span class="badge gray">Fuentes y procedencia</span>
    <h2 style="margin-top:10px">Catálogo de datos</h2>
    <p>Qué contiene cada fuente, cuántos registros, qué campos usa y de dónde proviene.
    Cinco bases del SIREC más las fuentes obligatorias de datos.gov.co (DIVIPOLA) y del DANE.</p>
  </header>

  @if (c(); as cat) {
  <div class="grid g3" style="margin-top:18px">
    <div class="card stat"><div class="kpi-label">Fuentes integradas</div>
      <div class="kpi-value">{{ cat.fuentes.length }}</div>
      <div class="small muted">5 SIREC · 2 externas (datos.gov.co / DANE)</div></div>
    <div class="card stat"><div class="kpi-label">Reconciliación DIVIPOLA</div>
      <div class="kpi-value">{{ cat.reconciliacion_territorial.cobertura_pct }}%</div>
      <div class="small muted">{{ cat.reconciliacion_territorial.emparejados }}/{{ cat.reconciliacion_territorial.pares }} pares municipio</div></div>
    <div class="card stat"><div class="kpi-label">Entidades anonimizadas</div>
      <div class="kpi-value">{{ totalAnon() }}</div>
      <div class="small muted">exhibidores + complejos (seudónimos)</div></div>
  </div>

  <div class="grid g2" style="margin-top:18px">
    @for (f of cat.fuentes; track f.id) {
    <div class="card fuente">
      <div class="row">
        <span class="badge" [class.amber]="f.grupo==='primaria'" [class.violet]="f.grupo==='externa'">{{ f.fuente }}</span>
        <span class="spacer"></span>
        @if (f.filas) { <span class="small muted mono">{{ fmt(f.filas) }} filas</span> }
      </div>
      <h3 style="margin:10px 0 2px; font-size:16px">{{ f.titulo }}</h3>
      <div class="small muted mono">{{ f.archivo }}</div>
      <p class="desc">{{ f.descripcion }}</p>
      <div class="fields">
        <div class="fl-h">Campos clave</div>
        <div class="row wrap">
          @for (k of f.campos_clave; track k) { <span class="chip">{{ k }}</span> }
        </div>
      </div>
      <div class="usos">
        <div class="fl-h">Se usa en</div>
        <div class="row wrap">
          @for (u of f.usos; track u) { <span class="badge teal">{{ u }}</span> }
        </div>
      </div>
      @if (f.notas) { <div class="nota">ⓘ {{ f.notas }}</div> }
      @if (f.procedencia) { <div class="small muted" style="margin-top:8px">Procedencia: <a [href]="f.procedencia" target="_blank" class="link">{{ f.procedencia }}</a></div> }
    </div>
    }
  </div>

  <div class="grid g2" style="margin-top:18px">
    <div class="card">
      <div class="card-title">Anonimización de datos sensibles</div>
      <div class="card-sub">Requisito del reto: anonimizar antes de procesar, sin afectar resultados.</div>
      <div class="stack" style="margin-top:12px">
        <div class="kv"><span>Técnica</span><b>{{ cat.anonimizacion.tecnica }}</b></div>
        <div class="kv"><span>Campos seudonimizados</span><b>Exhibidor, Complejo</b></div>
        <div class="kv"><span>Campos eliminados</span><b>Dirección física (PII)</b></div>
        <div class="kv"><span>Preserva resultados</span><b class="ok">Sí — agregados idénticos</b></div>
      </div>
      <p class="small muted" style="margin-top:12px">La tokenización determinista (HMAC-SHA256 salteado)
      hace que cada entidad real produzca siempre el mismo token, por lo que toda suma o conteo
      da exactamente el mismo número que con el nombre real.</p>
    </div>
    <div class="card">
      <div class="card-title">Reconciliación territorial (DIVIPOLA)</div>
      <div class="card-sub">Unión de nombres SIREC al código oficial DANE de 5 dígitos.</div>
      <div class="stack" style="margin-top:12px">
        <div class="kv"><span>Cobertura</span><b class="ok">{{ cat.reconciliacion_territorial.cobertura_pct }}%</b></div>
        @for (m of metodos(); track m.k) {
          <div class="kv"><span>Método: {{ m.k }}</span><b>{{ m.v }}</b></div>
        }
      </div>
      <p class="small muted" style="margin-top:12px">El emparejamiento se hace por normalización de texto
      (sin acentos) y coincidencia dentro de cada departamento, evitando confundir municipios homónimos.</p>
    </div>
  </div>
  } @else {
    <div class="card" style="margin-top:18px"><div class="skeleton" style="height:300px"></div></div>
  }
  `,
  styles: [`
    .stat { display: flex; flex-direction: column; gap: 6px; }
    .fuente .desc { font-size: 13.5px; color: var(--ink-soft); line-height: 1.55; margin: 12px 0; }
    .fl-h { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 600; margin-bottom: 6px; }
    .fields, .usos { margin: 12px 0; }
    .chip { background: var(--bg-alt); border-radius: 6px; padding: 3px 9px; font-size: 11.5px; color: var(--ink-soft); }
    .nota { margin-top: 12px; background: rgba(232,163,61,.1); border-radius: 10px; padding: 9px 12px; font-size: 12.5px; color: #8a5a12; }
    .link { color: var(--plum-600); word-break: break-all; }
    .kv { display: flex; justify-content: space-between; gap: 12px; font-size: 13px; color: var(--ink-soft);
      border-bottom: 1px solid var(--line); padding-bottom: 9px; }
    .kv b { color: var(--ink); text-align: right; }
    .ok { color: var(--teal-dark) !important; }
  `],
})
export class Datos {
  private api = inject(ApiService);
  c = signal<Catalog | null>(null);
  fmt = fmt;
  constructor() { this.api.catalog().subscribe((r) => this.c.set(r)); }
  totalAnon = computed(() => {
    const e = this.c()?.anonimizacion?.entidades_por_tipo || {};
    return Object.values(e).reduce((s: number, v: any) => s + (v as number), 0);
  });
  metodos = computed(() => {
    const m = this.c()?.reconciliacion_territorial?.por_metodo || {};
    return Object.entries(m).map(([k, v]) => ({ k, v: v as number }));
  });
}
