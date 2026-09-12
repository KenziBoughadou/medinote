import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import type { Method } from '../api/client'
import type { DataProvider } from '../data/provider'
import { RecordedDataProvider } from '../data/recorded-provider'
import { demoReducer, initialState } from '../state/demoReducer'
export function useDemo(initialProvider:DataProvider){
  const [provider,setProvider]=useState(initialProvider)
  const [state,dispatch]=useReducer(demoReducer,initialState)
  const counter=useRef(0);const busy=useRef(false)
  useEffect(()=>{
    let cancelled=false
    async function initialize(){
      let active=initialProvider
      try {
        let examples
        try {examples=await active.listExamples()} catch {
          if(active.offline)throw new Error('Les fichiers de démonstration sont indisponibles.')
          active=new RecordedDataProvider();examples=await active.listExamples()
        }
        if(cancelled)return
        setProvider(active);dispatch({type:'initialized',examples,offline:active.offline})
        const caps=await active.getCapabilities()
        if(!cancelled)dispatch({type:'capabilities',value:caps})
      } catch(e){if(!cancelled)dispatch({type:'loadError',message:e instanceof Error?e.message:'Chargement impossible.'})}
    }
    void initialize();return ()=>{cancelled=true}
  },[initialProvider])
  useEffect(()=>{
    if(!state.selectedCase || state.data[state.selectedCase])return
    let cancelled=false
    provider.getExample(state.selectedCase).then(example=>{if(!cancelled)dispatch({type:'loaded',example})})
      .catch(e=>{if(!cancelled)dispatch({type:'loadError',message:e instanceof Error?e.message:'Chargement impossible.'})})
    return ()=>{cancelled=true}
  },[provider,state.selectedCase,state.data])
  useEffect(()=>{
    if(!state.capabilities?.next_attempt_at || provider.offline)return
    const delay=Math.max(1000,new Date(state.capabilities.next_attempt_at).getTime()-Date.now()+250)
    const timer=setTimeout(()=>{provider.getCapabilities().then(value=>dispatch({type:'capabilities',value})).catch(()=>{})},delay)
    return ()=>clearTimeout(timer)
  },[provider,state.capabilities])
  const generate=useCallback(async(method:Method)=>{
    if(busy.current || !state.selectedCase || !state.capabilities?.live_available)return
    busy.current=true
    const pending={caseId:state.selectedCase,method,requestId:++counter.current}
    dispatch({type:'start',pending})
    try {const result=await provider.generate(pending.caseId,method);dispatch({type:'success',pending,result})}
    catch(e){dispatch({type:'failure',pending,message:e instanceof Error?e.message:'Génération impossible.'})}
    finally {
      busy.current=false
      try {dispatch({type:'capabilities',value:await provider.getCapabilities()})}catch{/* L'erreur de relance reste affichée. */}
    }
  },[provider,state.selectedCase,state.capabilities])
  return {state,dispatch,generate,provider}
}
