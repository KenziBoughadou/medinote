import { render, screen } from '@testing-library/react'
import { test, expect, vi } from 'vitest'
import App from './App'
test('navigation accessible',()=>{vi.stubGlobal('fetch',vi.fn(()=>new Promise(()=>{})));render(<App/>);expect(screen.getByRole('link',{name:'MediNote'})).toBeInTheDocument();expect(screen.getByRole('navigation')).toBeInTheDocument();vi.unstubAllGlobals()})
