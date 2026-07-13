import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'panorama', pathMatch: 'full' },
  { path: 'panorama', loadComponent: () => import('./pages/panorama').then((m) => m.Panorama) },
  { path: 'brechas', loadComponent: () => import('./pages/brechas').then((m) => m.Brechas) },
  { path: 'simulador', loadComponent: () => import('./pages/simulador').then((m) => m.Simulador) },
  { path: 'proyeccion', loadComponent: () => import('./pages/proyeccion').then((m) => m.Proyeccion) },
  { path: 'consultas', loadComponent: () => import('./pages/consultas').then((m) => m.Consultas) },
  { path: 'datos', loadComponent: () => import('./pages/datos').then((m) => m.Datos) },
  { path: 'metodologia', loadComponent: () => import('./pages/metodologia').then((m) => m.Metodologia) },
  { path: '**', redirectTo: 'panorama' },
];
