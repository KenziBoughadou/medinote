export function formatMetric(value:number|null|undefined){return value==null?'Non évalué':new Intl.NumberFormat('fr-FR',{style:'percent',maximumFractionDigits:1}).format(value)}
export function formatCost(value:number|null|undefined){return value==null?'Non mesuré':new Intl.NumberFormat('fr-FR',{style:'currency',currency:'USD',maximumFractionDigits:5}).format(value)}
export const originLabel={illustrative:'Illustration éditoriale · IA',llm_recorded:'Génération IA archivée',llm_live:'Nouvelle génération IA'}
