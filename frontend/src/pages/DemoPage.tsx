import type { DataProvider } from '../data/provider'
import { useDemo } from '../hooks/useDemo'
import { CaseSelector } from '../components/CaseSelector'
import { ComparisonWorkspace } from '../components/ComparisonWorkspace'
import { InlineNotice } from '../components/InlineNotice'
export function DemoPage({provider}:{provider:DataProvider}){
  const {state,dispatch,generate}=useDemo(provider)
  return <><div className="page-intro"><span className="eyebrow">Expérience de comparaison · NLP clinique</span><h1>Deux chemins vers une note.<br/>Les mêmes sources à vérifier.</h1><p>Explorez une consultation fictive, comparez les brouillons et retrouvez les passages cités. La conformité du format ne garantit pas la fidélité clinique.</p></div>{state.network==='offline'&&<InlineNotice>Mode hors ligne — bundle local. Les exemples et exports sont disponibles ; la génération IA est désactivée.</InlineNotice>}{state.loadError&&<InlineNotice error>{state.loadError}</InlineNotice>}<CaseSelector examples={state.examples} selected={state.selectedCase} onSelect={caseId=>dispatch({type:'select',caseId})}/><div className="availability" role="status">{state.capabilities?.reason??(state.capabilities?.live_available?`${state.capabilities.visitor_remaining} tentative(s) disponible(s) aujourd’hui. Une seule relance à la fois.`:'Chargement des disponibilités…')}</div>{state.examples.length>0&&<ComparisonWorkspace state={state} dispatch={dispatch} generate={generate}/>}<p className="footer-note">Prototype de recherche sur données synthétiques. Chaque assertion reste un brouillon à relire.</p></>
}
