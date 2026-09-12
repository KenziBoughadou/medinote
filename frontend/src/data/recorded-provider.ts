import { ApiFailure, request } from '../api/client'
import type { Case, Example, Method, Report, Result, Summary } from '../api/client'
import type { DataProvider } from './provider'
type Bundle = {consultations:Case[],results:Record<string,Record<Method,Result>>}
const focus:Record<string,string>={'main-digestif-01':'Cas simple','main-respiratoire-01':'Négation','main-cardiovasculaire-01':'Antécédent familial','main-neurologique-01':'Incertitude','main-musculosquelettique-01':'Correction','main-prevention-01':'Médicament'}
export class RecordedDataProvider implements DataProvider {
  readonly offline=true
  private bundle:Promise<Bundle>|null=null
  private load(){return this.bundle ??= request<Bundle>('/data/bundle.v1.json')}
  async listExamples():Promise<Summary[]>{const b=await this.load();return b.consultations.map(c=>({case_id:c.case_id,title:c.title,focus:focus[c.case_id],origins:{direct:b.results[c.case_id].direct.origin,structured:b.results[c.case_id].structured.origin}}))}
  async getExample(id:string):Promise<Example>{const b=await this.load();const c=b.consultations.find(c=>c.case_id===id);if(!c)throw new ApiFailure('Exemple introuvable.');return {consultation:c,results:b.results[id]}}
  async getCapabilities(){return {live_available:false,reason:'Génération indisponible hors ligne.',methods:['direct','structured'] as Method[],visitor_remaining:0,global_remaining:0,next_attempt_at:null}}
  async generate():Promise<Result>{throw new ApiFailure('Génération indisponible hors ligne.','OFFLINE')}
  getReport(){return request<Report>('/data/report.v1.json')}
}
