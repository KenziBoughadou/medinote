import type { components } from './schema'
export type Example = components['schemas']['PublicExample']
export type Case = components['schemas']['ConsultationCase']
export type Result = components['schemas']['GenerationResult']
export type Method = components['schemas']['Method']
export type Summary = components['schemas']['ExampleSummary']
export type Capabilities = components['schemas']['Capabilities']
export type Report = components['schemas']['PublishedReport']
export type Citation = components['schemas']['Citation']
export class ApiFailure extends Error {
  constructor(message:string, public code='NETWORK_UNAVAILABLE', public retryAfter:number|null=null){super(message)}
}
export async function request<T>(path:string,init?:RequestInit):Promise<T>{
  let response:Response
  try {response=await fetch(path,{...init,signal:AbortSignal.timeout(init?.method==='POST'?65000:10000),cache:'no-store'})}
  catch {throw new ApiFailure('Le service est indisponible. Les exemples restent consultables.')}
  if(!response.ok){
    let body:components['schemas']['ApiError']|null=null
    try {body=await response.json()} catch { /* Une gateway peut répondre sans JSON. */ }
    throw new ApiFailure(body?.error?.message ?? 'Le service est temporairement indisponible.',body?.error?.code,body?.error?.retry_after_seconds)
  }
  try {return await response.json() as T} catch {throw new ApiFailure('La réponse du service est illisible.')}
}
