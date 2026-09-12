import { request } from '../api/client'
import type { Capabilities, Example, Method, Report, Result, Summary } from '../api/client'
import type { DataProvider } from './provider'
export class ApiDataProvider implements DataProvider {
  readonly offline=false
  listExamples(){return request<Summary[]>('/api/examples')}
  getExample(id:string){return request<Example>(`/api/examples/${encodeURIComponent(id)}`)}
  getCapabilities(){return request<Capabilities>('/api/capabilities')}
  generate(case_id:string,method:Method){return request<Result>('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({case_id,method})})}
  getReport(){return request<Report>('/api/report')}
}
