import { useEffect, useState } from 'react'
import { AppHeader } from './components/AppHeader'
import { ApiDataProvider } from './data/api-provider'
import { RecordedDataProvider } from './data/recorded-provider'
import { DemoPage } from './pages/DemoPage'
import { ResultsPage } from './pages/ResultsPage'
import { MethodologyPage } from './pages/MethodologyPage'
const provider=new URLSearchParams(window.location.search).get('mode')==='offline'?new RecordedDataProvider():new ApiDataProvider()
const currentPage=()=>['results','methodology'].includes(window.location.hash.slice(1))?window.location.hash.slice(1):'demo'
export default function App(){
  const [page,setPage]=useState(currentPage)
  useEffect(()=>{const change=()=>setPage(currentPage());window.addEventListener('hashchange',change);return()=>window.removeEventListener('hashchange',change)},[])
  return <><a className="skip-link" href="#main-content">Aller au contenu</a><AppHeader page={page}/><main id="main-content" tabIndex={-1}>{page==='results'?<ResultsPage provider={provider}/>:page==='methodology'?<MethodologyPage/>:<DemoPage provider={provider}/>}</main><footer className="site-footer"><span>MediNote · Prototype IA/NLP</span><a href="#methodology">Données fictives, limites explicites</a></footer></>
}
