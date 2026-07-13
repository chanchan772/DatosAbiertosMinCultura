import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { fmtCompact } from './format';

export interface Bar { label: string; value: number; color?: string; sub?: string }
export interface Pt { x: string | number; y: number; flag?: boolean }

/* ------------------------------------------------------------------ BarChart
   Barras horizontales con etiqueta y valor. Ideal para rankings/distribuciones. */
@Component({
  selector: 'bar-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
  <div class="bc">
    @for (b of rows(); track b.label) {
    <div class="bc-row">
      <div class="bc-label" [title]="b.label">{{ b.label }}</div>
      <div class="bc-track">
        <div class="bc-fill" [style.width.%]="b.pctW" [style.background]="b.color || defColor()"></div>
      </div>
      <div class="bc-val">{{ b.disp }}</div>
    </div>
    }
  </div>
  `,
  styles: [`
    .bc { display: flex; flex-direction: column; gap: 9px; }
    .bc-row { display: grid; grid-template-columns: minmax(90px, 34%) 1fr auto; align-items: center; gap: 12px; }
    .bc-label { font-size: 13px; color: var(--ink-soft); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .bc-track { background: var(--bg-alt); border-radius: 6px; height: 22px; overflow: hidden; }
    .bc-fill { height: 100%; border-radius: 6px; transition: width .5s cubic-bezier(.2,.8,.2,1); min-width: 2px; }
    .bc-val { font-size: 12.5px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums; }
  `],
})
export class BarChart {
  data = input<Bar[]>([]);
  percent = input(false);
  defColor = input('var(--plum-600)');
  rows = computed(() => {
    const d = this.data(); const max = Math.max(1, ...d.map((x) => x.value));
    return d.map((b) => ({
      ...b, pctW: (b.value / max) * 100,
      disp: this.percent() ? b.value.toLocaleString('es-CO', { maximumFractionDigits: 1 }) + '%' : fmtCompact(b.value),
    }));
  });
}

/* ------------------------------------------------------------------ LineChart
   Área+línea con marcadores. Puntos con flag=true se resaltan (p.ej. COVID). */
@Component({
  selector: 'line-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
  <svg [attr.viewBox]="'0 0 ' + W + ' ' + H" class="lc" preserveAspectRatio="none">
    <defs>
      <linearGradient id="lcg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" [attr.stop-color]="color()" stop-opacity="0.28"/>
        <stop offset="100%" [attr.stop-color]="color()" stop-opacity="0"/>
      </linearGradient>
    </defs>
    @for (g of gridY(); track g.y) {
      <line [attr.x1]="padL" [attr.x2]="W-padR" [attr.y1]="g.y" [attr.y2]="g.y" stroke="var(--line)" stroke-width="1"/>
      <text [attr.x]="padL-6" [attr.y]="g.y+3" text-anchor="end" class="lc-ax">{{ g.lab }}</text>
    }
    <path [attr.d]="areaPath()" fill="url(#lcg)"/>
    <path [attr.d]="linePath()" fill="none" [attr.stroke]="color()" stroke-width="2.5" stroke-linejoin="round"/>
    @for (p of pts(); track p.cx) {
      <circle [attr.cx]="p.cx" [attr.cy]="p.cy" [attr.r]="p.flag ? 4.5 : 2.6"
        [attr.fill]="p.flag ? 'var(--coral)' : color()"/>
    }
    @for (p of pts(); track p.cx) {
      <text *ngIf="p.showLab" [attr.x]="p.cx" [attr.y]="H-6" text-anchor="middle" class="lc-ax">{{ p.xl }}</text>
    }
  </svg>
  `,
  styles: [`
    .lc { width: 100%; height: 240px; display: block; }
    .lc-ax { font-size: 10px; fill: var(--muted); font-family: var(--sans); }
  `],
})
export class LineChart {
  data = input<Pt[]>([]);
  color = input('var(--plum-600)');
  W = 640; H = 240; padL = 44; padR = 12; padT = 14; padB = 24;

  private geo = computed(() => {
    const d = this.data();
    const ys = d.map((p) => p.y); const max = Math.max(1, ...ys); const min = Math.min(0, ...ys);
    const iw = this.W - this.padL - this.padR; const ih = this.H - this.padT - this.padB;
    const n = Math.max(1, d.length - 1);
    const step = Math.max(1, Math.ceil(d.length / 10));
    const pts = d.map((p, i) => ({
      ...p, cx: this.padL + (i / n) * iw,
      cy: this.padT + ih - ((p.y - min) / (max - min || 1)) * ih,
      xl: String(p.x), showLab: i % step === 0 || i === d.length - 1,
    }));
    return { pts, max, min, ih };
  });
  pts = computed(() => this.geo().pts);
  linePath = computed(() => this.pts().map((p, i) => (i ? 'L' : 'M') + p.cx.toFixed(1) + ' ' + p.cy.toFixed(1)).join(' '));
  areaPath = computed(() => {
    const p = this.pts(); if (!p.length) return '';
    const base = this.H - this.padB;
    return 'M' + p[0].cx + ' ' + base + ' ' + p.map((q) => 'L' + q.cx.toFixed(1) + ' ' + q.cy.toFixed(1)).join(' ')
      + ' L' + p[p.length - 1].cx + ' ' + base + ' Z';
  });
  gridY = computed(() => {
    const { max, min } = this.geo(); const ih = this.H - this.padT - this.padB; const rows = 4;
    return Array.from({ length: rows + 1 }, (_, i) => {
      const v = min + (i / rows) * (max - min);
      return { y: this.padT + ih - (i / rows) * ih, lab: fmtCompact(v) };
    });
  });
}

/* ------------------------------------------------------------------ Donut */
@Component({
  selector: 'donut-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
  <div class="dn">
    <svg viewBox="0 0 120 120" class="dn-svg">
      @for (a of arcs(); track a.label) {
        <circle cx="60" cy="60" r="46" fill="none" [attr.stroke]="a.color" stroke-width="16"
          [attr.stroke-dasharray]="a.dash" [attr.stroke-dashoffset]="a.offset" transform="rotate(-90 60 60)"/>
      }
      <text x="60" y="56" text-anchor="middle" class="dn-c1">{{ total() }}</text>
      <text x="60" y="72" text-anchor="middle" class="dn-c2">{{ centerLabel() }}</text>
    </svg>
    <div class="dn-leg">
      @for (a of arcs(); track a.label) {
      <div class="dn-li"><span class="dot" [style.background]="a.color"></span>
        <span class="dn-lt">{{ a.label }}</span><span class="dn-lv">{{ a.pctDisp }}</span></div>
      }
    </div>
  </div>
  `,
  styles: [`
    .dn { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }
    .dn-svg { width: 130px; height: 130px; flex: none; }
    .dn-c1 { font-family: var(--display); font-size: 15px; font-weight: 700; fill: var(--ink); }
    .dn-c2 { font-size: 7px; fill: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
    .dn-leg { display: flex; flex-direction: column; gap: 7px; flex: 1; min-width: 160px; }
    .dn-li { display: flex; align-items: center; gap: 8px; font-size: 13px; }
    .dn-lt { color: var(--ink-soft); flex: 1; }
    .dn-lv { font-weight: 600; font-variant-numeric: tabular-nums; }
  `],
})
export class DonutChart {
  data = input<Bar[]>([]);
  centerLabel = input('');
  private C = 2 * Math.PI * 46;
  arcs = computed(() => {
    const d = this.data(); const tot = d.reduce((s, x) => s + x.value, 0) || 1;
    let acc = 0;
    return d.map((b) => {
      const frac = b.value / tot; const len = frac * this.C;
      const arc = { label: b.label, color: b.color || 'var(--plum-600)',
        dash: `${len} ${this.C - len}`, offset: -acc,
        pctDisp: (frac * 100).toLocaleString('es-CO', { maximumFractionDigits: 1 }) + '%' };
      acc += len; return arc;
    });
  });
  total = computed(() => fmtCompact(this.data().reduce((s, x) => s + x.value, 0)));
}
