import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {homedir} from 'node:os';
const require=createRequire(homedir()+'/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json');
const {chromium}=require('playwright');
const root=fileURLToPath(new URL('../../../../',import.meta.url)).replace(/\/$/,'');
const out=root+'/materiais/apresentacao/2026-11-10/assets';
const original=JSON.parse(await fs.readFile(root+'/frontend/data/catalogo-demo.json','utf8'));
const counts={};const catalogo=original.map(p=>({...p,id:p.categoria+':'+(counts[p.categoria]=(counts[p.categoria]||0)+1)}));
function build(id,nome,parts){const componentes={};for(const [pn,q]of parts){const p=catalogo.find(p=>p.part_number===pn);if(!p)continue;const item={id:Number(p.id.split(':').at(-1)),quantidade:q};if(['memoria_ram','ssd','hd','fan'].includes(p.categoria))(componentes[p.categoria]??=[]).push(item);else componentes[p.categoria]=item;}return {id,nome,descricao:'Configuração de demonstração',criado_em:'2026-11-08T12:00:00Z',estado:{titulo:nome,descricao:'Configuração de demonstração',orcamento:6000,visibilidade:'privado',travada:false,incluirPerifericos:false,incluirRede:false,percentualPerifericos:0,rede:{},componentes}};}
const builds=[build('s-1','Estudos e programação',[['SEED-CPU-03',1],['SEED-MB-17',1],['SEED-RAM-03',1],['SEED-SSD-06',1],['SEED-PSU-04',1],['SEED-CASE-02',1],['SEED-FAN-01',2]]),build('s-2','Jogos e criação',[['SEED-CPU-04',1],['SEED-MB-17',1],['SEED-RAM-03',2],['SEED-SSD-04',1],['SEED-GPU-04',1],['SEED-PSU-03',1],['SEED-CASE-02',1],['SEED-FAN-01',2],['SEED-ACOOL-02',1]])];
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1,reducedMotion:'reduce'});
await context.route('http://127.0.0.1:5000/**',async route=>{const path=new URL(route.request().url()).pathname;let data={};if(path==='/auth/me')data={auth:true,usuario:{id:999,nome:'Demonstração BOOSTio',email:'demo@boostio.example',verificado:true,ativo:true,budget:6000,usar_budget:false,preferencias_uso:{nivel_hardware:'avancado',tutorial:'concluido',versao_tutorial:1}}};else if(path==='/auth/csrf')data={csrf_token:'demo-local'};else if(path==='/build/catalogo')data={pecas:catalogo};else if(path==='/build/')data={builds};else if(path.startsWith('/build/s-'))data={build:builds.find(b=>path.includes(b.id))||builds[0]};await route.fulfill({status:200,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'http://127.0.0.1:8765','Access-Control-Allow-Credentials':'true'},body:JSON.stringify(data)});});
const page=await context.newPage();
page.on('pageerror',e=>console.log('pageerror',e.message));
async function go(name){await page.goto('http://127.0.0.1:8765/pages/'+name,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(600);}
async function shot(name){await page.screenshot({path:out+'/'+name+'.png'});console.log('capturada',name);}
await go('formulario.html');await shot('01-formulario');
await go('configuracao-build.html?build_id=s-1');await page.waitForSelector('#builder-title',{timeout:10000});await shot('02-editor');
await go('builds.html');await shot('03-builds');
await page.evaluate(async()=>{const {abrirComparacao}=await import('/js/build/comparacao.js');const {carregarCatalogoConta,buildDaConta}=await import('/js/build/conta.js');const {listarBuilds}=await import('/js/api/build/builds.js');abrirComparacao((await listarBuilds()).builds.map(buildDaConta),await carregarCatalogoConta());});await page.waitForTimeout(350);await shot('04-comparacao');
await page.evaluate(()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close()));
await page.evaluate(async()=>{const {abrirMelhorias}=await import('/js/build/melhorias.js');const {carregarCatalogoConta,buildDaConta}=await import('/js/build/conta.js');const {listarBuilds}=await import('/js/api/build/builds.js');abrirMelhorias(buildDaConta((await listarBuilds()).builds[0]),await carregarCatalogoConta(),async()=>{});});await page.waitForTimeout(350);await page.locator('[data-upgrade-group="memoria_ram"] > summary').click();await page.locator('[data-upgrade-category="memoria_ram"]:not([disabled])').first().click();await page.waitForTimeout(400);await shot('05-melhorias');
await go('configuracoes-prontas.html');await shot('06-prontas');
await go('index.html');await shot('07-inicio');
await fs.writeFile(out+'/origem-telas.json',JSON.stringify({origem:'HTML/CSS/JavaScript reais do frontend local; respostas de sessão, builds e catálogo simuladas com o catálogo demonstrativo versionado. Estas capturas não comprovam execução de backend nem resultados de IA.',builds,catalogoTamanho:catalogo.length},null,2));
await browser.close();
