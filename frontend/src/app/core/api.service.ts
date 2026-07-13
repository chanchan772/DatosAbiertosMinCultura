import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  Overview, DemandResult, MunicipioGeo, MunicipioDetail, Forecast, SimResult,
  MunicipioItem, Catalog, Narrative,
} from './models';
import { buildMunicipioDetail, buildSimulate, fallbackNarrative } from './static-compute';

export const API_BASE = environment.apiBase;
const STATIC = environment.staticMode;

interface MapData {
  anio: number; banda: string; tasa_referencia: number; metodo_tasa: string;
  umbral_conurbacion_km: number; municipios: any[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private mapCache: Record<string, Observable<MapData>> = {};

  // ---- lectura ----
  overview(): Observable<Overview> {
    return STATIC ? this.http.get<Overview>('api/overview.json')
      : this.http.get<Overview>(`${API_BASE}/api/overview`);
  }
  demand(anio = 2025, banda = 'pob_15_45'): Observable<DemandResult> {
    return STATIC ? this.http.get<DemandResult>(`api/demand_${banda}.json`)
      : this.http.get<DemandResult>(`${API_BASE}/api/demand`, { params: { anio, banda } });
  }
  demandMap(anio = 2025, banda = 'pob_15_45'): Observable<{ municipios: MunicipioGeo[] }> {
    return STATIC ? this.getMap(banda).pipe(map((md) => ({ municipios: md.municipios as MunicipioGeo[] })))
      : this.http.get<{ municipios: MunicipioGeo[] }>(`${API_BASE}/api/demand/map`, { params: { anio, banda } });
  }
  forecast(anio = 2027): Observable<Forecast> {
    return STATIC ? this.http.get<Forecast>('api/forecast.json')
      : this.http.get<Forecast>(`${API_BASE}/api/forecast`, { params: { anio } });
  }
  municipios(): Observable<MunicipioItem[]> {
    return STATIC ? this.http.get<MunicipioItem[]>('api/municipios.json')
      : this.http.get<MunicipioItem[]>(`${API_BASE}/api/municipios`);
  }
  catalog(): Observable<Catalog> {
    return STATIC ? this.http.get<Catalog>('api/catalog.json')
      : this.http.get<Catalog>(`${API_BASE}/api/catalog`);
  }
  methodology(): Observable<any> {
    return STATIC ? this.http.get<any>('api/methodology.json')
      : this.http.get<any>(`${API_BASE}/api/methodology`);
  }

  // ---- interactivo ----
  municipio(cod: string, anio = 2025, banda = 'pob_15_45'): Observable<MunicipioDetail> {
    if (!STATIC) return this.http.get<MunicipioDetail>(`${API_BASE}/api/demand/municipio/${cod}`, { params: { anio, banda } });
    return this.getMap(banda).pipe(map((md) => {
      const row = md.municipios.find((x) => x.cod_mpio === String(cod).padStart(5, '0'));
      return buildMunicipioDetail(row, md.tasa_referencia, md.metodo_tasa, banda, md.anio, md.umbral_conurbacion_km);
    }));
  }
  simulate(cod_mpio: string, n_salas: number, banda = 'pob_15_45'): Observable<SimResult> {
    if (!STATIC) return this.http.post<SimResult>(`${API_BASE}/api/simulate`, { cod_mpio, n_salas, banda });
    return this.getMap(banda).pipe(map((md) => {
      const row = md.municipios.find((x) => x.cod_mpio === String(cod_mpio).padStart(5, '0'));
      return buildSimulate(row, n_salas, md.tasa_referencia, banda, md.anio);
    }));
  }
  narrative(tipo: string, contexto: any): Observable<Narrative> {
    return STATIC ? of(fallbackNarrative(tipo, contexto))
      : this.http.post<Narrative>(`${API_BASE}/api/narrative`, { tipo, contexto });
  }

  private getMap(banda: string): Observable<MapData> {
    if (!this.mapCache[banda]) {
      this.mapCache[banda] = this.http.get<MapData>(`api/map_${banda}.json`).pipe(shareReplay(1));
    }
    return this.mapCache[banda];
  }
}
