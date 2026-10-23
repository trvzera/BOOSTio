import test from 'node:test';
import assert from 'node:assert/strict';
import { planejarMelhoriaRam, contextoMelhoriaRam, AVISO_DUAL_CHANNEL } from '../js/build/melhorias-ram.js';

const placa = {id:'placa_mae:1',categoria:'placa_mae',tipo_memoria:'DDR4',quantidade_slots_ram:4,memoria_maxima_gb:64};
const ram = {id:'memoria_ram:1',categoria:'memoria_ram',capacidade_gb:8,quantidade_pentes:1,frequencia_mhz:3200,ddr:'DDR4',latencia:'CL16',preco:150};
const outra = {...ram,id:'memoria_ram:2',fabricante:'Outra marca',capacidade_gb:16,preco:250};
const kit = {...ram,id:'memoria_ram:3',capacidade_gb:32,quantidade_pentes:2,preco:450};
const catalogo = [placa,ram,outra,kit];
const base = () => ({titulo:'QA',componentes:{placa_mae:{id:placa.id,quantidade:1},memoria_ram:[{id:ram.id,quantidade:1}]},compatibilidade:{erros:[{codigo:'ram-slots',mensagem:'Diagnóstico anterior'}]}});
const propor = (itens,modo='adicionar',build=base(),pecas=catalogo) => planejarMelhoriaRam(build,pecas,{modo,itens});

test('RAM pode acrescentar o mesmo modelo sem remover a atual e cobra somente a compra',()=>{
  const build=base(),antes=structuredClone(build);
  const resultado=propor([{id:ram.id,quantidade:1}],'adicionar',build);
  assert.deepEqual(resultado.build.componentes.memoria_ram,[{id:ram.id,quantidade:2}]);
  assert.equal(resultado.gastoCentavos,15000);assert.equal(resultado.pentes,2);assert.equal(resultado.capacidadeGb,16);
  assert.equal(resultado.build.compatibilidade.status,'nao_verificado');assert.deepEqual(resultado.build.compatibilidade.erros,[]);assert.deepEqual(build,antes);
});

test('RAM aceita múltiplos modelos e capacidades sem prometer dual channel',()=>{
  const resultado=propor([{id:ram.id,quantidade:1},{id:outra.id,quantidade:1}]);
  assert.deepEqual(resultado.build.componentes.memoria_ram,[{id:ram.id,quantidade:2},{id:outra.id,quantidade:1}]);
  assert.equal(resultado.capacidadeGb,32);assert.equal(resultado.gastoCentavos,40000);
  assert.match(AVISO_DUAL_CHANNEL,/slots indicados no manual/);assert.match(AVISO_DUAL_CHANNEL,/não garantem/);
  assert.match(AVISO_DUAL_CHANNEL,/Misturar modelos/);
});

test('kits contam pentes por kit e capacidade por item, sem multiplicar GB pelos pentes',()=>{
  const resultado=propor([{id:kit.id,quantidade:1}]);
  assert.equal(resultado.pentes,3);assert.equal(resultado.capacidadeGb,40);
  assert.throws(()=>propor([{id:kit.id,quantidade:2}]),/slots/);
});

test('substituir é explícito e pode usar dois pentes em lugar de quatro sem reduzir capacidade',()=>{
  const build=base();build.componentes.memoria_ram[0].quantidade=4;
  const resultado=propor([{id:kit.id,quantidade:1}],'substituir',build);
  assert.deepEqual(resultado.build.componentes.memoria_ram,[{id:kit.id,quantidade:1}]);
  assert.equal(resultado.pentes,2);assert.equal(resultado.capacidadeGb,32);
  assert.throws(()=>propor([{id:ram.id,quantidade:1}],'substituir',build),/reduziria/);
});

test('limites são os da placa-mãe atual, incluindo capacidade máxima',()=>{
  assert.throws(()=>propor([{id:ram.id,quantidade:4}]),/slots/);
  const pequena={...placa,memoria_maxima_gb:16};
  assert.throws(()=>propor([{id:outra.id,quantidade:1}],'adicionar',base(),[pequena,ram,outra]),/máximo/);
  for(const campo of ['memoria_maxima_gb','tipo_memoria']){
    assert.throws(()=>contextoMelhoriaRam(base(),[{...placa,[campo]:null},ram]),/Faltam/);
  }
  assert.throws(()=>propor([{id:ram.id,quantidade:1}],'adicionar',{componentes:{memoria_ram:base().componentes.memoria_ram}}),/placa-mãe atual/);
});

test('slots desconhecidos permitem dois pentes provisórios sem inventar capacidade máxima',()=>{
  const cat=[{...placa,quantidade_slots_ram:null},ram];
  const contexto=contextoMelhoriaRam(base(),cat);
  assert.equal(contexto.slots,2);assert.equal(contexto.slotsProvisorios,true);
  const resultado=propor([{id:ram.id,quantidade:1}],'adicionar',base(),cat);
  assert.equal(resultado.pentes,2);assert.equal(resultado.slotsProvisorios,true);
  assert.throws(()=>propor([{id:ram.id,quantidade:2}],'adicionar',base(),cat),/slots/);
  assert.equal(cat[0].quantidade_slots_ram,null);
  assert.throws(()=>contextoMelhoriaRam(base(),[{...cat[0],memoria_maxima_gb:null},ram]),/capacidade máxima/);
});

for(const [mudanca,mensagem] of [[{ddr:'DDR5'},/DDR/],[{frequencia_mhz:2666},/frequência/],
  [{latencia:'CL22'},/latência/],[{latencia:null},/latência/],[{esgotado:true},/indisponível/],[{preco:0},/preço/]])
  test('expansão bloqueia memória incompatível ou inferior: '+JSON.stringify(mudanca),()=>{
    const candidata={...outra,...mudanca};
    assert.throws(()=>propor([{id:candidata.id,quantidade:1}],'adicionar',base(),[placa,ram,candidata]),mensagem);
  });

test('RAM própria não identificada, tranca e quantidades inválidas não passam',()=>{
  const build=base();build.componentes.memoria_ram=[{proprio:'Minha RAM',quantidade:1}];
  assert.throws(()=>propor([{id:ram.id,quantidade:1}],'adicionar',build),/Identifique/);
  assert.throws(()=>propor([{id:ram.id,quantidade:1}],'adicionar',{...base(),travada:true}),/Destranque/);
  for(const quantidade of [null,0,-1,true,1.5,65])assert.throws(()=>propor([{id:ram.id,quantidade}]),/quantidades/);
  assert.throws(()=>propor([{id:ram.id,quantidade:1},{id:ram.id,quantidade:1}]),/Agrupe/);
});

test('catálogo alterado é revalidado na confirmação e proposta vazia preserva o diagnóstico',()=>{
  const pecas=structuredClone(catalogo);pecas[0].quantidade_slots_ram=1;
  assert.throws(()=>propor([{id:ram.id,quantidade:1}],'adicionar',base(),pecas),/slots/);
  assert.deepEqual(propor([]).build,base());
});

test('a prévia não oculta erros do servidor sobre outras peças',()=>{
  const build=base();build.compatibilidade.erros.push({codigo:'socket',mensagem:'Socket incompatível'});
  const resultado=propor([{id:ram.id,quantidade:1}],'adicionar',build);
  assert.equal(resultado.build.compatibilidade.status,'incompativel');
  assert.deepEqual(resultado.build.compatibilidade.erros,[{codigo:'socket',mensagem:'Socket incompatível'}]);
});

test('substituir pelo mesmo modelo e quantidade não é sugerido como compra de melhoria',()=>{
  assert.throws(()=>propor([{id:ram.id,quantidade:1}],'substituir'),/mantém as mesmas memórias/);
});
