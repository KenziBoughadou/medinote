import { render, screen, fireEvent } from '@testing-library/react'
import { test, expect, vi } from 'vitest'
import { CitationButton } from './CitationButton'
test('citation accessible au clavier et aucune injection HTML',()=>{const select=vi.fn();render(<CitationButton citation={{citation_id:'c',segment_id:'s001',quote:'<img onerror=alert(1)>',resolvable:true}} onSelect={select}/>);fireEvent.click(screen.getByRole('button'));expect(select.mock.calls[0][0]).toBe('s001');expect(document.querySelector('img')).toBeNull()})
test('référence introuvable sans lien',()=>{render(<CitationButton citation={{citation_id:'c',segment_id:'absent',quote:null,resolvable:false}} onSelect={()=>{}}/>);expect(screen.getByText(/Source introuvable/)).toBeInTheDocument();expect(screen.queryByRole('button')).toBeNull()})
