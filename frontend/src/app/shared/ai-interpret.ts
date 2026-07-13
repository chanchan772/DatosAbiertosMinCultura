import { Component, computed, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../core/api.service';
import { Interpretation } from '../core/models';

// Markdown mínimo → HTML (negritas, listas, párrafos). Angular sanea el innerHTML.
export function mdToHtml(md: string): string {
  const esc = (md || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const lines = esc.split('\n');
  let html = '', inList = false;
  for (const raw of lines) {
    let line = raw.trim().replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    const bullet = /^[-*]\s+/.test(raw.trim()) || /^\d+\.\s+/.test(raw.trim());
    if (bullet) {
      if (!inList) { html += '<ul>'; inList = true; }
      html += '<li>' + line.replace(/^[-*]\s+/, '').replace(/^\d+\.\s+/, '') + '</li>';
    } else {
      if (inList) { html += '</ul>'; inList = false; }
      if (line) html += '<p>' + line + '</p>';
    }
  }
  if (inList) html += '</ul>';
  return html;
}

/**
 * Panel reutilizable "Interpretación del análisis (IA)": recibe el nombre del
 * módulo y los datos que muestra, y pide a DeepSeek una interpretación larga y
 * accesible para cualquier público.
 */
@Component({
  selector: 'ai-interpret',
  standalone: true,
  imports: [CommonModule],
  template: `
  <div class="ai card">
    <div class="row">
      <div>
        <div class="card-title">Interpretación del análisis <span class="badge violet">IA · DeepSeek</span></div>
        <div class="card-sub">{{ subtitulo() }}</div>
      </div>
      <span class="spacer"></span>
      <button class="btn primary" (click)="run()" [disabled]="loading()">
        {{ loading() ? 'Analizando…' : (result() ? '↻ Regenerar' : 'Interpretar con IA') }}
      </button>
    </div>
    @if (loading()) {
      <div class="ai-loading">
        <div class="skeleton" style="height:16px; width:40%"></div>
        <div class="skeleton" style="height:12px"></div>
        <div class="skeleton" style="height:12px; width:92%"></div>
        <div class="skeleton" style="height:12px; width:96%"></div>
      </div>
    } @else if (result()) {
      <div class="ai-body" [innerHTML]="html()"></div>
      <div class="small muted ai-src">
        {{ result()!.fuente === 'deepseek' ? 'Generado por DeepSeek ' + result()!.modelo : 'No disponible en este momento' }}
        · redactado a partir de las cifras del módulo, sin inventar datos.
      </div>
    } @else {
      <p class="muted small" style="margin-top:8px">Obtén una explicación detallada y en lenguaje
      sencillo de lo que muestran estos datos: hallazgos, qué significan para el país y sus límites.</p>
    }
  </div>
  `,
  styles: [`
    .ai { background: linear-gradient(180deg, #faf7ff, #fff); }
    .ai-loading { display: flex; flex-direction: column; gap: 8px; margin-top: 14px; }
    .ai-body { margin-top: 12px; font-size: 14.5px; line-height: 1.68; color: var(--ink); }
    .ai-body :is(p) { margin: 0 0 10px; }
    .ai-body :is(strong) { color: var(--plum-700); }
    .ai-body :is(ul) { margin: 6px 0 12px; padding-left: 20px; }
    .ai-body :is(li) { margin: 5px 0; }
    .ai-src { margin-top: 10px; }
  `],
})
export class AiInterpret {
  modulo = input.required<string>();
  datos = input.required<any>();
  subtitulo = input('Análisis generado por IA sobre los datos de este módulo.');
  private api = inject(ApiService);
  loading = signal(false);
  result = signal<Interpretation | null>(null);
  html = computed(() => mdToHtml(this.result()?.interpretacion || ''));

  run() {
    this.loading.set(true);
    this.api.interpret(this.modulo(), this.datos()).subscribe({
      next: (r) => { this.result.set(r); this.loading.set(false); },
      error: () => { this.result.set({ interpretacion: 'No fue posible generar la interpretación.', fuente: 'error', modelo: null }); this.loading.set(false); },
    });
  }
}
