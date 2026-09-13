import { test, expect } from '@playwright/test'
test('six cas, A/B, sources et navigation',async({page})=>{
  await page.goto('/?mode=offline');await expect(page.locator('#case option')).toHaveCount(6)
  const ids=await page.locator('#case option').evaluateAll(options=>options.map(o=>(o as HTMLOptionElement).value))
  for(const id of ids){await page.selectOption('#case',id);await expect(page.locator('.source-pane .pane-heading p')).toHaveText((await page.locator('#case option:checked').textContent())!.split(' — ').slice(1).join(' — '));await expect(page.locator('.note-pane')).toHaveCount(2)}
  const citation=page.locator('.note-pane').first().getByRole('button',{name:'Afficher la source s002'}).first()
  await citation.click();await expect(page.locator('#source-s002')).toBeFocused();await expect(page.getByText('Source sélectionnée')).toBeVisible()
  await page.getByRole('button',{name:'Revenir à la citation'}).click();await expect(citation).toBeFocused()
  await expect(page.getByRole('link',{name:'GitHub'})).toHaveAttribute('href','https://github.com/KenziBoughadou/medinote')
  await page.getByRole('link',{name:'Résultats',exact:true}).click();await expect(page.getByText('Références et sorties revues humainement')).toBeVisible()
  const coverage=page.getByRole('row').filter({has:page.getByRole('rowheader',{name:'Couverture fidèle',exact:true})})
  await expect(coverage).toContainText('95,8');await expect(coverage).toContainText('92,5')
  await expect(page.getByRole('link',{name:'Méthode de relecture'})).toHaveAttribute('href','https://github.com/KenziBoughadou/medinote/blob/main/docs/HUMAN_REVIEW_RESULTS.md')
  await page.goto('/?mode=offline#methodology')
  await expect(page.getByRole('link',{name:'Lire le protocole expérimental'})).toHaveAttribute('href','https://github.com/KenziBoughadou/medinote/blob/main/docs/EXPERIMENT_PROTOCOL.md')
})
