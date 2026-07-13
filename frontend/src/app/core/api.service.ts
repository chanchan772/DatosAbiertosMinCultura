import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Overview, DemandResult, MunicipioGeo, MunicipioDetail, Forecast, SimResult,
  MunicipioItem, Catalog, Narrative,
} from './models';

export const API_BASE = 'http://127.0.0.1:8000';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  overview(): Observable<Overview> {
    return this.http.get<Overview>(`${API_BASE}/api/overview`);
  }
  demand(anio = 2025, banda = 'pob_15_45'): Observable<DemandResult> {
    return this.http.get<DemandResult>(`${API_BASE}/api/demand`, { params: { anio, banda } });
  }
  demandMap(anio = 2025, banda = 'pob_15_45'): Observable<{ municipios: MunicipioGeo[] }> {
    return this.http.get<{ municipios: MunicipioGeo[] }>(`${API_BASE}/api/demand/map`, { params: { anio, banda } });
  }
  municipio(cod: string, anio = 2025, banda = 'pob_15_45'): Observable<MunicipioDetail> {
    return this.http.get<MunicipioDetail>(`${API_BASE}/api/demand/municipio/${cod}`, { params: { anio, banda } });
  }
  forecast(anio = 2027): Observable<Forecast> {
    return this.http.get<Forecast>(`${API_BASE}/api/forecast`, { params: { anio } });
  }
  municipios(): Observable<MunicipioItem[]> {
    return this.http.get<MunicipioItem[]>(`${API_BASE}/api/municipios`);
  }
  simulate(cod_mpio: string, n_salas: number, banda = 'pob_15_45'): Observable<SimResult> {
    return this.http.post<SimResult>(`${API_BASE}/api/simulate`, { cod_mpio, n_salas, banda });
  }
  catalog(): Observable<Catalog> {
    return this.http.get<Catalog>(`${API_BASE}/api/catalog`);
  }
  methodology(): Observable<any> {
    return this.http.get<any>(`${API_BASE}/api/methodology`);
  }
  narrative(tipo: string, contexto: any): Observable<Narrative> {
    return this.http.post<Narrative>(`${API_BASE}/api/narrative`, { tipo, contexto });
  }
}
