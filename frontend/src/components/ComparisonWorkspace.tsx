import { useRef } from 'react'
import type { Dispatch } from 'react'
import type { Method } from '../api/client'
import type { Action, DemoState } from '../state/demoReducer'
import { ConsultationPane } from './ConsultationPane'
import { NotePane } from './NotePane'
export function ComparisonWorkspace({state,dispatch,generate}:{state:DemoState,dispatch:Dispatch<Action>,generate:(method:Method)=>void}){
  const trigger=useRef<HTMLButtonElement|null>(null)
  const example=state.selectedCase?state.data[state.selectedCase]:null
  if(!example)return <p role="status">Chargement de la consultation…</p>
  function onCitation(id:string,button:HTMLButtonElement){trigger.current=button;dispatch({type:'segment',id});requestAnimationFrame(()=>{const el=document.getElementById('source-'+id);el?.scrollIntoView({block:'center',behavior:'instant'});el?.focus({preventScroll:true})})}
  return <><div className="workspace"><ConsultationPane consultation={example.consultation} active={state.activeSegment} onReturn={()=>trigger.current?.focus()}/><div className="method-tabs" role="group" aria-label="Méthode affichée">{(['direct','structured'] as Method[]).map(m=><button key={m} aria-pressed={state.methodTab===m} onClick={()=>dispatch({type:'tab',method:m})}>{m==='direct'?'A · Résumé direct':'B · Extraction structurée'}</button>)}</div>{(['direct','structured'] as Method[]).map(m=><NotePane key={m} method={m} result={example.results[m]} consultation={example.consultation} visible={state.methodTab===m} capabilities={state.capabilities} busy={!!state.activeRequest} pending={state.activeRequest?.caseId===state.selectedCase&&state.activeRequest?.method===m} error={state.errors[m]} onGenerate={()=>generate(m)} onCitation={onCitation}/>)}</div></>
}
