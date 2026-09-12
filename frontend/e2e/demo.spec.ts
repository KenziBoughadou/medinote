import { test, expect } from '@playwright/test'
test('six cas, A/B, sources et navigation',async({page})=>{
  await page.goto('/?mode=offline');await expect(page.locator('#case option')).toHaveCount(6)
  const ids=await page.locator('#case option').evaluateAll(options=>options.map(o=>(o as HTMLOptionElement).value))
  for(const id of ids){await page.selectOption('#case',id);await expect(page.locator('.source-pane .pane-heading p')).toHaveText((await page.locator('#case option:checked').textContent())!.split(' — ').slice(1).join(' — '));await expect(page.locator('.note-pane')).toHaveCount(2)}
  const citation=page.locator('.note-pane').first().getByRole('button',{name:'Afficher la source s002'}).first()
  await citation.click();await expect(page.locator('#source-s002')).toBeFocused();await expect(page.getByText('Source sélectionnée')).toBeVisible()
  await page.getByRole('button',{name:'Revenir à la citation'}).click();await expect(citation).toBeFocused()
  await expect(page.getByRole('link',{name:'GitHub'})).toHaveAttribute('href','https://github.com/KenziBoughadou/medinote')
  await page.getByRole('link',{name:'Résultats',exact:true}).click();await expect(page.getByText('Annotation des sorties en attente')).toBeVisible();await expect(page.getByText('Non évalué',{exact:true}).first()).toBeVisible()
})
