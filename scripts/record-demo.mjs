import { createRequire } from 'node:module'
import { mkdir, rename, stat, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { execFileSync } from 'node:child_process'
const require=createRequire(new URL('../frontend/package.json',import.meta.url))
const {chromium}=require('playwright')
const output=fileURLToPath(new URL('../docs/assets/',import.meta.url))
const origin=process.env.MEDINOTE_CAPTURE_ORIGIN??'http://127.0.0.1:5173'
function probeVideo(){return JSON.parse(execFileSync('ffprobe',['-v','quiet','-show_format','-of','json',output+'/demo.webm'],{encoding:'utf8'}))}
async function finalizeVideo(){
  const recordedDuration=Number(probeVideo().format.duration)
  if(recordedDuration<175||recordedDuration>185||(await stat(output+'/demo.webm')).size>=25*1024*1024){
    // Chromium's video clock can drift from the wall clock under load. Preserve
    // every captured frame and normalize the complete walkthrough to 3 minutes.
    execFileSync('ffmpeg',['-y','-i',output+'/demo.webm','-vf',`setpts=${180/recordedDuration}*PTS`,'-t','180','-c:v','libvpx-vp9','-b:v','600k','-an',output+'/demo-small.webm'],{stdio:'ignore'})
    await rename(output+'/demo-small.webm',output+'/demo.webm')
  }
  const duration=Number(probeVideo().format.duration);const size=(await stat(output+'/demo.webm')).size
  if(duration<175||duration>185||size>=25*1024*1024)throw new Error('Capture hors des bornes du plan')
  await writeFile(output+'/capture-metadata.json',JSON.stringify({created_at:new Date().toISOString(),duration_seconds:duration,recorded_duration_seconds:recordedDuration,size_bytes:size,viewport:[1280,720],provider_network:'disabled',origin:'illustrative',audio:false},null,2)+'\n')
  process.stdout.write(`Capture vérifiée : ${duration} s, ${size} octets.\n`)
}
export async function recordDemo(){
  await mkdir(output,{recursive:true})
  const browser=await chromium.launch()
  try {
    for(const [name,width,height] of [['desktop',1440,1000],['mobile',390,844]]){
      const context=await browser.newContext({viewport:{width,height},reducedMotion:'reduce'})
      await context.route(url=>url.hostname!=='127.0.0.1'&&url.hostname!=='localhost',route=>route.abort())
      const page=await context.newPage();await page.goto(origin+'/?mode=offline');await page.locator('.source-pane').waitFor()
      await page.screenshot({path:`${output}/demo-${name}.png`,fullPage:true});await context.close()
    }
    const context=await browser.newContext({viewport:{width:1280,height:720},reducedMotion:'reduce',recordVideo:{dir:output+'/temporary',size:{width:1280,height:720}}})
    await context.route(url=>url.pathname.startsWith('/api/')||!['127.0.0.1','localhost'].includes(url.hostname),route=>route.abort())
    const started=Date.now();const page=await context.newPage();const waitUntil=async seconds=>{const delay=seconds*1000-(Date.now()-started);if(delay>0)await page.waitForTimeout(delay)}
    await page.goto(origin+'/?mode=offline');await page.locator('.source-pane').waitFor()
    await waitUntil(12);await page.selectOption('#case','main-respiratoire-01')
    await waitUntil(30);await page.locator('.note-pane').first().getByRole('button',{name:'Afficher la source s006'}).first().click()
    await waitUntil(45);await page.getByRole('button',{name:'Revenir à la citation'}).click()
    await waitUntil(60);await page.locator('.note-pane').last().getByRole('button',{name:'Afficher la source s006'}).first().click()
    await waitUntil(80);await page.locator('.note-pane').first().getByText('Provenance et mesures').click()
    await page.locator('.note-pane').first().locator('.provenance').scrollIntoViewIfNeeded()
    await waitUntil(100);await page.locator('.note-pane').first().getByText('Exporter',{exact:true}).click()
    const download=page.waitForEvent('download');await page.locator('.note-pane').first().getByRole('button',{name:'Markdown',exact:true}).click();await download
    await waitUntil(120);await page.getByRole('link',{name:'Résultats',exact:true}).click();await page.evaluate(()=>window.scrollTo(0,0))
    await waitUntil(142);await page.getByRole('link',{name:'Méthodologie',exact:true}).click();await page.evaluate(()=>window.scrollTo(0,0))
    await waitUntil(163);await page.getByRole('heading',{name:'Un protocole traçable'}).scrollIntoViewIfNeeded()
    await waitUntil(173);await page.evaluate(()=>window.scrollTo(0,0));await page.getByRole('link',{name:'GitHub'}).focus()
    await waitUntil(180);await page.close();await context.close()
    await rename(await page.video().path(),output+'/demo.webm')
    await finalizeVideo()
  } finally {await browser.close()}
}
if(process.argv.includes('--finalize-existing'))await finalizeVideo()
else await recordDemo()
