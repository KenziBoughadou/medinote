import { test, expect } from 'vitest'
import { escapeMarkdown } from './exportNote'
import { formatMetric, formatCost } from './formatters'
test('aucun zéro pour une valeur absente',()=>{expect(formatMetric(null)).toBe('Non évalué');expect(formatCost(null)).toBe('Non mesuré')})
test('échappe les valeurs modèle',()=>{expect(escapeMarkdown('<img>*test*[x](url)')).toBe('&lt;img&gt;\\*test\\*\\[x\\]\\(url\\)')})
