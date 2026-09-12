import { test, expect } from 'vitest'
import { demoReducer, initialState } from './demoReducer'
import type { Result } from '../api/client'
test('une réponse obsolète ne remplace pas le cas sélectionné',()=>{const pending={caseId:'old',method:'direct' as const,requestId:1};const state={...initialState,selectedCase:'new',activeRequest:pending};const next=demoReducer(state,{type:'success',pending,result:{case_id:'old'} as Result});expect(next.data).toEqual({});expect(next.activeRequest).toBeNull()})
test('une erreur de relance conserve les notes',()=>{const pending={caseId:'c',method:'direct' as const,requestId:1};const state={...initialState,selectedCase:'c',activeRequest:pending};const next=demoReducer(state,{type:'failure',pending,message:'Quota atteint'});expect(next.data).toBe(state.data);expect(next.errors.direct).toBe('Quota atteint')})
