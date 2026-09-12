import { ArrowClockwise } from '@phosphor-icons/react'
import type { Capabilities } from '../api/client'
export function GenerationControls({capabilities,busy,pending,onGenerate}:{capabilities:Capabilities|null,busy:boolean,pending:boolean,onGenerate:()=>void}){return <button className="generate-button" disabled={busy||!capabilities?.live_available} onClick={onGenerate}><ArrowClockwise size={18} aria-hidden="true"/>{pending?'Génération en cours…':'Relancer l’IA'}</button>}
