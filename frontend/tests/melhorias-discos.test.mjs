import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { planejarMelhoriaDisco } from "../js/build/melhorias-discos.js";
import { avaliarTrocaMelhoria } from "../js/build/validar-melhoria.js";
import { avaliarBuild } from "../js/build/compatibilidade.js";

const placa = {id:"mb",categoria:"placa_mae",quantidade_slots_m2:2,quantidade_portas_sata:2};
const ssd = {id:"ssd1",categoria:"ssd",modelo:"SSD atual",tipo:"NVMe",capacidade_gb:1000,preco:500,
  velocidade_leitura_mbps:3500,velocidade_gravacao_mbps:2800};
const nova = {...ssd,id:"ssd2",modelo:"SSD novo",capacidade_gb:500,preco:200,velocidade_leitura_mbps:null,velocidade_gravacao_mbps:null};
const hd = {id:"hd1",categoria:"hd",modelo:"HD SATA",interface:"SATA III",capacidade_gb:2000,preco:300};
const catalogo = [placa,ssd,nova,hd];
const base = () => ({id:"qa",titulo:"QA",orcamento:2000,componentes:{placa_mae:{id:placa.id,quantidade:1},ssd:[{id:ssd.id,quantidade:1}]},
  compatibilidade:{status:"incompativel",erros:[{codigo:"socket",mensagem:"Conflito de outra peça"}]}});

test("expandir SSD mantém o volume atual mesmo quando faltam velocidades do novo disco", () => {
  const build=base(),antes=structuredClone(build);
  const resultado=planejarMelhoriaDisco(build,nova,catalogo);
  assert.deepEqual(resultado.componentes.ssd,[{id:ssd.id,quantidade:1},{id:nova.id,quantidade:1}]);
  assert.equal(avaliarBuild(resultado,catalogo).preco,700);
  assert.equal(resultado.orcamento,build.orcamento);
  assert.deepEqual(resultado.compatibilidade,build.compatibilidade);
  assert.deepEqual(build,antes);
});

test("expansão pode duplicar o mesmo SSD sem remover ou recomprar os atuais", () => {
  const resultado=planejarMelhoriaDisco(base(),ssd,catalogo);
  assert.deepEqual(resultado.componentes.ssd,[{id:ssd.id,quantidade:2}]);
  assert.equal(avaliarTrocaMelhoria(base(),ssd,catalogo,{modo:"adicionar"}).codigo,"expansao");
  assert.throws(()=>planejarMelhoriaDisco(resultado,ssd,catalogo),/slots M\.2/);
});

test("expansão de HD conta portas SATA, inclusive as usadas por SSD SATA", () => {
  const sata={...nova,id:"sata",tipo:"SATA",interface:"SATA III"};
  const build=base();build.componentes.ssd=[{id:sata.id,quantidade:1}];
  const pecas=[...catalogo,sata];
  const resultado=planejarMelhoriaDisco(build,hd,pecas);
  assert.deepEqual(resultado.componentes.ssd,build.componentes.ssd);
  assert.deepEqual(resultado.componentes.hd,[{id:hd.id,quantidade:1}]);
  assert.throws(()=>planejarMelhoriaDisco(resultado,hd,pecas),/portas SATA/);
});

test("disco novo não contorna limites ausentes, interface desconhecida ou placa ausente", () => {
  assert.throws(()=>planejarMelhoriaDisco(base(),nova,[{...placa,quantidade_slots_m2:null},ssd,nova]),/Falta a quantidade/);
  const semPlaca=base();delete semPlaca.componentes.placa_mae;
  assert.throws(()=>planejarMelhoriaDisco(semPlaca,nova,catalogo),/Selecione a placa-mãe/);
  assert.throws(()=>planejarMelhoriaDisco(base(),{...nova,tipo:null},catalogo),/conexão dos discos/);
});

test("expansão respeita portas compartilhadas entre M.2 SATA e SATA", () => {
  const mb={...placa,quantidade_slots_m2_sata:1,portas_sata_desativadas_por_m2_sata:2};
  const m2sata={...nova,id:"m2sata",tipo:"SATA",interface:"SATA III",formato:"M.2 2280"};
  const build=base();build.componentes.hd=[{id:hd.id,quantidade:1}];
  assert.throws(()=>planejarMelhoriaDisco(build,m2sata,[mb,ssd,m2sata,hd]),/portas SATA/);
});

test("modo substituir ainda rejeita discos inferiores ou sem velocidades comparáveis", () => {
  assert.throws(()=>planejarMelhoriaDisco(base(),nova,catalogo,{modo:"substituir"}),/reduziria/);
  assert.throws(()=>planejarMelhoriaDisco(base(),{...nova,capacidade_gb:2000},catalogo,{modo:"substituir"}),/Faltam dados/);
  const melhor={...ssd,id:"ssd3",capacidade_gb:2000,preco:800};
  const resultado=planejarMelhoriaDisco(base(),melhor,[...catalogo,melhor],{modo:"substituir"});
  assert.deepEqual(resultado.componentes.ssd,[{id:melhor.id,quantidade:1}]);
});

test("substituição que corrige excesso de discos não mantém o erro antigo de conexões", () => {
  const build=base();build.componentes.ssd[0].quantidade=2;
  build.compatibilidade.erros=[{codigo:"discos-m2",mensagem:"Diagnóstico anterior: excede M.2"}];
  const mb={...placa,quantidade_slots_m2:1};
  const melhor={...ssd,id:"maior",capacidade_gb:2000,preco:800};
  const resultado=planejarMelhoriaDisco(build,melhor,[mb,ssd,melhor],{modo:"substituir"});
  assert.deepEqual(resultado.componentes.ssd,[{id:melhor.id,quantidade:1}]);
  assert.deepEqual(resultado.compatibilidade.erros,[]);
  assert.equal(resultado.compatibilidade.status,"nao_verificado");
  assert.equal(build.compatibilidade.erros.length,1);
});

test("prévia preserva erros desconhecidos e de outras peças após corrigir conexões", () => {
  const build=base();build.compatibilidade.erros.push({codigo:"discos-m2",mensagem:"Diagnóstico anterior"},{codigo:"regra-nova",mensagem:"Não revalidada"});
  const resultado=planejarMelhoriaDisco(build,nova,catalogo);
  assert.deepEqual(resultado.compatibilidade.erros.map(e=>e.codigo),["socket","regra-nova"]);
  assert.equal(resultado.compatibilidade.status,"incompativel");
});

test("conexões sem limite conhecido não apagam diagnóstico anterior", () => {
  const build=base();build.compatibilidade.erros=[{codigo:"discos-m2",mensagem:"Conflito anterior"}];
  const maior={...ssd,id:"maior",capacidade_gb:2000};
  const resultado=planejarMelhoriaDisco(build,maior,[{...placa,quantidade_slots_m2:null},ssd,maior],{modo:"substituir"});
  assert.deepEqual(resultado.compatibilidade,build.compatibilidade);
});

test("expansão não inventa capacidade nem aceita modelos atuais não identificados", () => {
  assert.throws(()=>planejarMelhoriaDisco(base(),{...nova,capacidade_gb:null},catalogo),/capacidade/);
  const build=base();build.componentes.ssd=[{proprio:"Meu SSD",quantidade:1}];
  assert.throws(()=>planejarMelhoriaDisco(build,nova,catalogo),/Identifique todos os modelos/);
  assert.throws(()=>planejarMelhoriaDisco({...base(),travada:true},nova,catalogo),/Destranque/);
});

for(const preco of [null,"",true,0,-1,Infinity,"inválido"])
  test("disco sem preço válido não entra na prévia: "+String(preco),()=>{
    assert.throws(()=>planejarMelhoriaDisco(base(),{...nova,preco},catalogo),/preço válido/);
  });

test("disco esgotado e modo/categoria inválidos não são liberados", () => {
  assert.throws(()=>planejarMelhoriaDisco(base(),{...nova,esgotado:true},catalogo),/indisponível/);
  assert.throws(()=>planejarMelhoriaDisco(base(),nova,catalogo,{modo:"outro"}),/inválida/);
  assert.throws(()=>planejarMelhoriaDisco(base(),{...nova,categoria:"processador"},catalogo),/inválida/);
});

test("UI permite consulta sem budget, mas confirmação continua exigindo o teto", async () => {
  const js=await readFile(new URL("../js/build/melhorias.js",import.meta.url),"utf8");
  assert.match(js,/if \(exigirBudget && limite == null\) throw new Error\(MOTIVO_BUDGET\)/);
  assert.match(js,/if \(limite != null && gasto > limite\)/);
  assert.match(js,/simular\(propostas,undefined,rams,\{exigirBudget:false\}\)/);
  assert.match(js,/const confirmada = simular\(trocas,build\)/);
  assert.match(js,/data-upgrade-disk-mode=/);
  assert.match(js,/modosDiscos\.set\(categoria,caixa\.value\); trocas\.delete\(categoria\)/);
  assert.match(js,/planejarMelhoriaDisco\(proxima,peca,catalogo,\{modo:modoTroca\(peca\.categoria\),quantidade:quantidadeTroca\(peca\.categoria\)\}\)/);
  assert.match(js,/Todos os slots disponíveis de RAM estão ocupados/);
});

test("quantidades novas respeitam portas e preservam o disco atual",()=>{
  const mb={...placa,quantidade_slots_m2:4};
  const r=planejarMelhoriaDisco(base(),nova,[mb,ssd,nova],{quantidade:2});
  assert.deepEqual(r.componentes.ssd,[{id:ssd.id,quantidade:1},{id:nova.id,quantidade:2}]);
  assert.throws(()=>planejarMelhoriaDisco(base(),nova,[mb,ssd,nova],{quantidade:4}),/slots M\.2/);
  for (const quantidade of [0,-1,1.5,true,null,65]) assert.throws(()=>planejarMelhoriaDisco(base(),nova,catalogo,{quantidade}),/unidades/);
});
test("baias do gabinete limitam SSD SATA e HD, incluindo unidades já instaladas",()=>{
  const gabinete={id:"case",categoria:"gabinete",baias_35:1,baias_25:1};
  const disco={...hd,formato:"3.5"};
  const build=base();build.componentes.gabinete={id:"case",quantidade:1};
  assert.throws(()=>planejarMelhoriaDisco(build,disco,[...catalogo.filter(p=>p.id!==hd.id),disco,gabinete],{quantidade:2}),/baias/);
  assert.equal(build.componentes.hd,undefined);
});
