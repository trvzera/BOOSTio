import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { informacoesFans, encaixeRadiador, orientacoesVentilacao, fluxoFan } from "../js/build/fans.js";
import { completarCatalogoDemo, validarEncaixe } from "../js/build/hardware.js";
import { normalizarBuild, removerPeca } from "../js/build/estado.js";
import { avaliarBuild, selecionarPecaCompativel, pecaCompativel } from "../js/build/compatibilidade.js";
import { estadoParaConta } from "../js/build/conta.js";
import { exportarJson, exportarCsv, importarBuild } from "../js/build/arquivos.js";

const fixture = JSON.parse(readFileSync(new URL("./fixtures/encaixe-fans.json",import.meta.url)));
const radiadores = JSON.parse(readFileSync(new URL("./fixtures/radiadores-dimensoes.json",import.meta.url)));
for (const caso of radiadores.casos) test('radiador Python/JS: ' + caso.nome,() => {
  assert.equal(encaixeRadiador({...radiadores.gabinete,...caso.gabinete},{...radiadores.water,...caso.water}),caso.esperado);
});
for (const caso of fixture.casos) test("encaixe compartilhado Python/JS: " + caso.nome,() => {
  const info = informacoesFans({...fixture.gabinete,...caso.gabinete},caso.fans,caso.water ?? null,caso.substituir === true);
  for (const [campo,valor] of Object.entries(caso.esperado)) assert.equal(info[campo],valor,campo);
});

test("fonte, altura/slots de GPU e baias rejeitam somente limites conhecidos",() => {
  const gabinete = {tamanho_max_fonte_mm:160,formatos_fonte:["ATX"],tamanho_max_altura_gpu_mm:150,slots_expansao:3,baias_25:1};
  const params = {gabinete,fonte:{comprimento_mm:161,formato:"SFX"},gpu:{altura_mm:151,slots_ocupados:4},discos:[{peca:{formato:"2.5"},item:{quantidade:2}}]};
  assert.equal(validarEncaixe(params).erros.length,5);
  params.fonte = {comprimento_mm:160,formato:"ATX"}; params.gpu = {altura_mm:150,slots_ocupados:3};params.discos[0].item.quantidade=1;
  assert.equal(validarEncaixe(params).erros.length,0);
  assert.ok(validarEncaixe({gabinete:{},air:{dimensoes:150}}).avisos.length);
});

const manifesto = JSON.parse(readFileSync(new URL("../data/medidas-fisicas.json",import.meta.url)));
test("fichas oficiais exigem identificação exata e corrigem medidas ambíguas sem mutar peças",() => {
  const caseBase = {id:"case",categoria:"gabinete",fabricante:"Cooler Master",modelo:"MasterBox Q300L",part_number:"SEED-CASE-01",tamanho_max_cooler_mm:160};
  const airBase = {id:"air",categoria:"air_cooler",fabricante:"Deepcool",modelo:"AK400",part_number:"SEED-ACOOL-02",dimensoes:129};
  const [gabinete,air] = completarCatalogoDemo([caseBase,airBase],manifesto);
  assert.equal(gabinete.quantidade_max_fans,6);assert.equal(gabinete.tamanho_max_cooler_mm,159);assert.equal(air.altura_mm,155);
  assert.equal(caseBase.tamanho_max_cooler_mm,160);assert.equal(airBase.altura_mm,undefined);
  for (const alteracao of [{part_number:"outro"},{modelo:"MasterBox Q300L V2"},{fabricante:"Outra"}]) {
    assert.equal(completarCatalogoDemo([{...caseBase,...alteracao}],manifesto)[0].posicoes_fans,undefined);
  }
});

test("filtro impede conflito por posição na adição e na escolha posterior de gabinete",() => {
  const gabinete = {id:"case",categoria:"gabinete",...fixture.gabinete};
  const fan = {id:"fan",categoria:"fan",tamanho_mm:140,quantidade:3}; // só existem duas posições de 140
  const catalogo = [gabinete,fan];
  const build = normalizarBuild({componentes:{gabinete:{id:"case"}}});
  assert.equal(pecaCompativel(build,fan,catalogo),false);
  assert.throws(() => selecionarPecaCompativel(build,fan,catalogo),/posições compartilhadas/);
  const semGabinete = normalizarBuild({componentes:{fan:[{id:"fan",quantidade:1}]}});
  assert.equal(pecaCompativel(semGabinete,gabinete,catalogo),false);
});

test("NR200 tem limites oficiais de fonte e GPU e ressalvas visíveis, sem somar posições compartilhadas",() => {
  const [gabinete,fonte] = completarCatalogoDemo([
    {categoria:'gabinete',fabricante:'Cooler Master',modelo:'MasterBox NR200',part_number:'SEED-CASE-11'},
    {categoria:'fonte',fabricante:'MSI',modelo:'MAG A650BN',part_number:'SEED-PSU-01',formato:'ATX'},
  ],manifesto);
  assert.equal(gabinete.fans_inclusos,2); assert.equal(fonte.comprimento_mm,140);
  assert.deepEqual(gabinete.formatos_fonte,['SFX','SFX-L']);
  const resultado=validarEncaixe({gabinete,fonte,gpu:{comprimento_mm:331,altura_mm:157,espessura_mm:61}});
  assert.equal(resultado.erros.length,5);
  assert.ok(resultado.avisos.some(v=>v.includes('custom loop')));
  assert.equal(gabinete.posicoes_fans.find(p=>p.nome==='Base').radiadores_mm.length,0);
  assert.equal(informacoesFans(gabinete,[{item:{quantidade:6},peca:{quantidade:1,tamanho_mm:120}}]).quantidade,false);
});

test("fans já inclusas atendem a presença de ventilação sem exigir compra extra",() => {
  const gabinete = {id:"case",categoria:"gabinete",fans_inclusos:1};
  const build = normalizarBuild({componentes:{gabinete:{id:"case"}}});
  assert.ok(!avaliarBuild(build,[gabinete]).faltam.includes("Fans"));
  assert.ok(avaliarBuild(build,[{...gabinete,fans_inclusos:null}]).faltam.includes("Fans"));
  assert.ok(avaliarBuild(build,[{...gabinete,fans_inclusos:0}]).faltam.includes("Fans"));
});

test('duplicar e misturar modelos de fans usa posições e não restrições de RAM',() => {
  const gabinete = {id:'case',categoria:'gabinete',fans_inclusos:0,quantidade_max_fans:7,tamanhos_fan_suportados_mm:[120]};
  const water = {id:'water',categoria:'water_cooler',quantidade_fans:2,tamanho_radiador_mm:240,tamanho_fan_mm:120};
  const a = {id:'a',categoria:'fan',fabricante:'A',modelo:'Normal',tamanho_mm:120,quantidade:1};
  const b = {...a,id:'b',fabricante:'B',modelo:'Reverse'};
  const cat = [gabinete,water,a,b];
  let build = normalizarBuild({componentes:{gabinete:{id:'case'},water_cooler:{id:'water'}}});
  for (let i=0;i<4;i++) build = selecionarPecaCompativel(build,a,cat);
  build = selecionarPecaCompativel(build,b,cat);
  assert.equal(avaliarBuild(build,cat).erros.length,0);
  assert.throws(()=>selecionarPecaCompativel(build,b,cat),/mais fans/);
  build.substituirFansWaterCooler = true;
  build = selecionarPecaCompativel(selecionarPecaCompativel(build,b,cat),b,cat);
  assert.equal(avaliarBuild(build,cat).erros.length,0);
  assert.ok(avaliarBuild(build,cat).avisos.some(v=>v.includes('Substituição')));
});

test('orientações explicam parafusos e fluxo sem transformar fan reversa em requisito',()=>{
  const orientacao = orientacoesVentilacao({gabinete:{},water:{quantidade_fans:2},fans:[{peca:{modelo:'TR120 Reverse'},item:{quantidade:1}}]});
  assert.match(orientacao.dicas.join(' '),/parafusos longos podem danificar/);
  assert.match(orientacao.dicas.join(' '),/preferência, não incompatibilidade/);
  assert.equal(fluxoFan({modelo:'TR120 Reverse'}),'reverso');
  assert.equal(fluxoFan({modelo:'Fan desconhecida'}),'nao_informado');
});

test('estado da conta e arquivos mantêm opção explícita de substituição',()=>{
  const build = normalizarBuild({titulo:'QA',substituirFansWaterCooler:true});
  assert.equal(estadoParaConta(build).substituirFansWaterCooler,true);
  assert.equal(normalizarBuild().substituirFansWaterCooler,false);
  assert.equal(removerPeca(build,'water_cooler').substituirFansWaterCooler,false);
  assert.equal(importarBuild(exportarJson(build),'json',[]).substituirFansWaterCooler,true);
  assert.equal(importarBuild(exportarCsv(build,[]),'csv',[]).substituirFansWaterCooler,true);
  assert.throws(()=>importarBuild(JSON.stringify({...build,substituirFansWaterCooler:'true'}),'json',[]),/Metadado inválido/);
});
