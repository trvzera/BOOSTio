

import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {homedir} from 'node:os';
import {build} from './autor-slides.mjs';
const require=createRequire(homedir()+'/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/package.json');
const {Presentation,PresentationFile}=await import(require.resolve('@oai/artifact-tool'));
const out=process.argv[2];
if(!out){console.error('Informe a pasta de saída.');process.exit(1);}
await fs.mkdir(out,{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
console.log(await build(p));
for(const [i,sl] of p.slides.items.entries()){
 const png=await p.export({slide:sl,format:'png',scale:1});
 await fs.writeFile(`${out}/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await png.arrayBuffer()));
}
const pptx=await PresentationFile.exportPptx(p);
await pptx.save(`${out}/BOOSTio-Pitch-3A2.pptx`);
