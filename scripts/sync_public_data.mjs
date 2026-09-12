import { mkdir, copyFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
const target = new URL('../frontend/public/data/', import.meta.url)
await mkdir(target, {recursive:true})
for (const name of ['bundle.v1.json','report.v1.json']) await copyFile(new URL(`../public-data/${name}`,import.meta.url),fileURLToPath(new URL(name,target)))
