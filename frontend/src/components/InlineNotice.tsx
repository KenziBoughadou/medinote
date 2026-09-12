import type { ReactNode } from 'react'
export function InlineNotice({children,error=false}:{children:ReactNode,error?:boolean}){return <p className={'notice'+(error?' error':'')} role={error?'alert':'status'}>{children}</p>}
