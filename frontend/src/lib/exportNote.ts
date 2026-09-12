import type { Case, Result } from '../api/client'
export const escapeMarkdown=(text:string)=>text.replace(/[\\`*_{}[\]()#+.!|~-]/g,'\\$&').replace(/</g,'&lt;').replace(/>/g,'&gt;')
export function markdownContent(result:Result,consultation:Case){
  const esc=escapeMarkdown
  const lines=['# MediNote — Consultation fictive · Brouillon à relire','',
    `Méthode : ${esc(result.method)} · Origine : ${esc(result.origin)}`,
    `Cas : ${esc(result.case_id)} · Exécution : ${esc(result.run_id)}`,'']
  for(const section of result.note.sections){
    lines.push(`## ${esc(section.title)}`)
    if(!section.assertions.length)lines.push('Non mentionné')
    for(const assertion of section.assertions){
      const references=assertion.citations.map(c=>`(${esc(c.segment_id)}${c.resolvable?'':', source introuvable'})`).join(' ')
      lines.push(`${esc(assertion.text)} ${references}`)
    }
    lines.push('')
  }
  lines.push('## Sources',...consultation.segments.map(s=>`${esc(s.segment_id)} — ${esc(s.speaker)} : ${esc(s.text)}`),'','## Métadonnées')
  for(const [key,value] of Object.entries(result.metadata))lines.push(`${esc(key)} : ${esc(value===null?'Non mesuré':String(value))}`)
  lines.push(`Revue : ${esc(result.review.kind)}`,`Empreinte de note : ${result.note.note_sha256}`,'Ce brouillon fictif ne constitue pas une validation clinique.','')
  return lines.join('\n')
}
function download(content:string,mime:string,name:string){const url=URL.createObjectURL(new Blob([content],{type:mime}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
export function downloadMarkdown(result:Result,consultation:Case){download(markdownContent(result,consultation),'text/markdown;charset=utf-8',`medinote-${result.case_id}-${result.method}-${result.run_id}.md`)}
export function downloadJson(result:Result,consultation:Case){download(JSON.stringify({notice:'Consultation fictive · Brouillon à relire',consultation,result},null,2),'application/json',`medinote-${result.case_id}-${result.method}-${result.run_id}.json`)}
