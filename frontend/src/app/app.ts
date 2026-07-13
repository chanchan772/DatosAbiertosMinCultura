import { Component, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

interface NavItem { path: string; label: string; icon: string; desc: string }

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  collapsed = signal(false);
  nav: NavItem[] = [
    { path: '/panorama', label: 'Panorama nacional', icon: '◫', desc: 'Estado del consumo' },
    { path: '/brechas', label: 'Mapa de brechas', icon: '◉', desc: 'Demanda insatisfecha' },
    { path: '/simulador', label: 'Simulador de exhibidor', icon: '⧉', desc: 'Captura hipotética' },
    { path: '/proyeccion', label: 'Estacionalidad y 2027', icon: '⟋', desc: 'Series de tiempo' },
    { path: '/datos', label: 'Catálogo de datos', icon: '▤', desc: 'Fuentes y procedencia' },
    { path: '/metodologia', label: 'Metodología', icon: '∴', desc: 'Fórmulas y supuestos' },
  ];
}
