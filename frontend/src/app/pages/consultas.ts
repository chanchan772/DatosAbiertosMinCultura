import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../core/api.service';
import { mdToHtml } from '../shared/ai-interpret';

interface Turno { pregunta: string; respuesta: string; fuente: string; modelo: string | null; html: string }

@Component({
  selector: 'page-consultas',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
  <header class="section-head">
    <span class="badge violet">Asistente IA</span>
    <h2 style="margin-top:10px">Consulta los datos en lenguaje natural</h2>
    <p>Pregunta lo que quieras sobre la asistencia y el acceso al cine en Colombia. El asistente
    (DeepSeek) responde <b>solo con base en los datos calculados</b> por el tablero — no inventa cifras.</p>
  </header>

  <div class="card" style="margin-top:16px">
    <div class="ask">
      <input type="text" [ngModel]="q()" (ngModelChange)="q.set($event)"
        (keyup.enter)="preguntar()" placeholder="Ej. ¿Qué departamentos tienen más municipios sin cine?"
        [disabled]="loading()">
      <button class="btn primary" (click)="preguntar()" [disabled]="loading() || !q().trim()">
        {{ loading() ? 'Consultando…' : 'Preguntar' }}</button>
    </div>
    <div class="chips">
      <span class="small muted">Ejemplos:</span>
      @for (e of ejemplos; track e) {
        <button class="chip" (click)="usar(e)" [disabled]="loading()">{{ e }}</button>
      }
    </div>
  </div>

  <div class="stack" style="margin-top:16px">
    @for (t of historia(); track $index) {
    <div class="card turno">
      <div class="pregunta"><span class="qmark">Q</span>{{ t.pregunta }}</div>
      <div class="respuesta" [innerHTML]="t.html"></div>
      <div class="small muted">{{ t.fuente === 'deepseek' ? 'DeepSeek ' + t.modelo : 'No disponible' }}
        · respuesta basada en las cifras del tablero.</div>
    </div>
    }
    @if (loading()) {
      <div class="card"><div class="skeleton" style="height:14px; width:35%; margin-bottom:10px"></div>
        <div class="skeleton" style="height:12px"></div><div class="skeleton" style="height:12px; width:90%; margin-top:6px"></div></div>
    }
    @if (!historia().length && !loading()) {
      <div class="card empty">
        <div class="empty-ic">💬</div>
        <p>Hazle una pregunta a los datos. Por ejemplo, sobre demanda insatisfecha, concentración
        del mercado, estacionalidad o la proyección 2027.</p>
      </div>
    }
  </div>
  `,
  styles: [`
    .ask { display: flex; gap: 10px; }
    .ask input { flex: 1; }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 12px; }
    .chip { background: var(--bg-alt); border: 1px solid var(--line); border-radius: 999px; padding: 5px 12px;
      font-size: 12.5px; color: var(--ink-soft); }
    .chip:hover { border-color: var(--plum-600); color: var(--plum-700); }
    .turno .pregunta { display: flex; gap: 10px; align-items: center; font-weight: 600; font-size: 15px; }
    .qmark { width: 24px; height: 24px; border-radius: 7px; background: var(--plum-700); color: #fff;
      display: grid; place-items: center; font-size: 12px; font-weight: 700; flex: none; }
    .respuesta { margin: 14px 0 8px; font-size: 14.5px; line-height: 1.68; color: var(--ink); }
    .respuesta :is(p) { margin: 0 0 10px; } .respuesta :is(strong) { color: var(--plum-700); }
    .respuesta :is(ul) { margin: 6px 0 12px; padding-left: 20px; } .respuesta :is(li) { margin: 5px 0; }
    .empty { text-align: center; padding: 44px 30px; color: var(--ink-soft); }
    .empty-ic { font-size: 34px; margin-bottom: 8px; }
  `],
})
export class Consultas {
  private api = inject(ApiService);
  q = signal('');
  loading = signal(false);
  historia = signal<Turno[]>([]);
  ejemplos = [
    '¿Cuáles son los 5 municipios con mayor demanda insatisfecha?',
    '¿Qué tan concentrado está el mercado de exhibición?',
    '¿Cuánto se proyecta para 2027 y con qué incertidumbre?',
    '¿Por qué el cine colombiano tiene tan poca participación?',
    '¿Qué significa que un municipio sea “saturado”?',
  ];

  usar(e: string) { this.q.set(e); this.preguntar(); }

  preguntar() {
    const pregunta = this.q().trim();
    if (!pregunta || this.loading()) return;
    this.loading.set(true);
    this.api.query(pregunta).subscribe({
      next: (r) => {
        this.historia.update((h) => [{ pregunta, respuesta: r.respuesta, fuente: r.fuente,
          modelo: r.modelo, html: mdToHtml(r.respuesta) }, ...h]);
        this.q.set(''); this.loading.set(false);
      },
      error: () => {
        this.historia.update((h) => [{ pregunta, respuesta: 'No fue posible responder ahora.',
          fuente: 'error', modelo: null, html: '<p>No fue posible responder ahora.</p>' }, ...h]);
        this.loading.set(false);
      },
    });
  }
}
