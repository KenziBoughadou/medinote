import { DownloadSimple } from '@phosphor-icons/react'
import type { Case, Result } from '../api/client'
import { downloadJson, downloadMarkdown } from '../lib/exportNote'
export function ExportMenu({result,consultation}:{result:Result,consultation:Case}){return <details className="export-menu"><summary><DownloadSimple size={18} aria-hidden="true"/>Exporter</summary><div><button onClick={()=>downloadMarkdown(result,consultation)}>Markdown</button><button onClick={()=>downloadJson(result,consultation)}>JSON</button></div></details>}
