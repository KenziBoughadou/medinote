import type { Capabilities, Example, Method, Report, Result, Summary } from '../api/client'
export interface DataProvider {
  readonly offline:boolean
  listExamples():Promise<Summary[]>
  getExample(id:string):Promise<Example>
  getCapabilities():Promise<Capabilities>
  generate(id:string,method:Method):Promise<Result>
  getReport():Promise<Report>
}
