import type { Capabilities, Example, Method, Result, Summary } from '../api/client'
export type Pending = {caseId:string,method:Method,requestId:number}
export type DemoState = {
  selectedCase:string|null; examples:Summary[]; data:Record<string,Example>; activeSegment:string|null;
  methodTab:Method; activeRequest:Pending|null; network:'loading'|'online'|'offline'|'error';
  errors:Partial<Record<Method,string>>; loadError:string|null; capabilities:Capabilities|null
}
export const initialState:DemoState={selectedCase:null,examples:[],data:{},activeSegment:null,methodTab:'direct',activeRequest:null,network:'loading',errors:{},loadError:null,capabilities:null}
export type Action =
  | {type:'initialized',examples:Summary[],offline:boolean}
  | {type:'select',caseId:string}
  | {type:'loaded',example:Example}
  | {type:'loadError',message:string}
  | {type:'segment',id:string|null}
  | {type:'tab',method:Method}
  | {type:'capabilities',value:Capabilities}
  | {type:'start',pending:Pending}
  | {type:'success',pending:Pending,result:Result}
  | {type:'failure',pending:Pending,message:string}
export function demoReducer(state:DemoState,action:Action):DemoState{
  switch(action.type){
    case 'initialized':return {...state,examples:action.examples,selectedCase:action.examples[0]?.case_id??null,network:action.offline?'offline':'online'}
    case 'select':return {...state,selectedCase:action.caseId,activeSegment:null,errors:{},loadError:null}
    case 'loaded':return {...state,data:{...state.data,[action.example.consultation.case_id]:action.example},loadError:null}
    case 'loadError':return {...state,loadError:action.message,network:state.examples.length?state.network:'error'}
    case 'segment':return {...state,activeSegment:action.id}
    case 'tab':return {...state,methodTab:action.method}
    case 'capabilities':return {...state,capabilities:action.value}
    case 'start':return {...state,activeRequest:action.pending,errors:{...state.errors,[action.pending.method]:undefined}}
    case 'success':case 'failure':{
      if(state.activeRequest?.requestId!==action.pending.requestId)return state
      const next={...state,activeRequest:null}
      if(state.selectedCase!==action.pending.caseId)return next
      if(action.type==='failure')return {...next,errors:{...state.errors,[action.pending.method]:action.message}}
      if(action.result.case_id!==action.pending.caseId || action.result.method!==action.pending.method)return next
      const old=state.data[action.pending.caseId]
      if(!old)return next
      return {...next,data:{...state.data,[action.pending.caseId]:{...old,results:{...old.results,[action.pending.method]:action.result}}}}
    }
  }
}
