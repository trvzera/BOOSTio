import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { avaliarDisponibilidadeFps, motivoRequisitosFps } from "../js/benchmark/disponibilidade.js";

const catalogo=JSON.parse(readFileSync(new URL("../data/catalogo-demo.json",import.meta.url)));
function base() {
  const componentes={};
  for(const id of ["SEED-CPU-02","SEED-MB-03","SEED-RAM-01","SEED-SSD-01","SEED-GPU-02","SEED-PSU-01","SEED-CASE-01","SEED-ACOOL-01"]) {
    const peca=catalogo.find(p=>p.id===id);
    componentes[peca.categoria]=["memoria_ram","ssd"].includes(peca.categoria)?[{id,quantidade:1}]:{id,quantidade:1};
  }
  return {id:"s-1",componentes};
}
const avaliar=(build=base(),pecas=catalogo)=>avaliarDisponibilidadeFps(build,pecas);
const alterar=(categoria,dados)=>catalogo.map(p=>p.categoria===categoria?{...p,...dados}:p);

test("build completa com CPU/GPU reconhecidas e RAM conhecida pode estimar FPS",()=>{
  const build=base(),antes=structuredClone(build),r=avaliar(build);
  assert.equal(r.permitido,true);assert.equal(r.hardware.gpu,"rtx-3060");assert.equal(r.memoriaGb,8);
  assert.deepEqual(build,antes);
});

test("CPU/GPU ausentes ou próprias não são substituídas por outro modelo",()=>{
  for(const categoria of ["processador","placa_video"]) {
    const build=base();build.componentes[categoria]={proprio:"Minha peça"};
    assert.equal(avaliar(build).codigo,categoria==="processador"?"cpu-nao-identificada":"gpu-nao-identificada");
  }
  const build=base();delete build.componentes.placa_video;
  const r=avaliar(build,alterar("processador",{videointegrado:true}));
  assert.equal(r.codigo,"video-integrado");assert.match(r.motivo,/Blender pelo processador/);
});

test("hardware sem correspondência exata no provedor fica bloqueado",()=>{
  assert.equal(avaliar(base(),alterar("placa_video",{memoria_gb:8})).codigo,"hardware-nao-suportado");
  assert.equal(avaliar(base(),alterar("processador",{modelo:"CPU não mapeada"})).codigo,"hardware-nao-suportado");
});

test("RAM própria, ausente, sem capacidade ou com quantidade inválida bloqueia a consulta",()=>{
  for(const selecao of [[],[{proprio:"RAM própria"}],[{id:"SEED-RAM-01",quantidade:0}],[null]]) {
    const build=base();build.componentes.memoria_ram=selecao;
    assert.equal(avaliar(build).codigo,"ram-nao-identificada");
  }
  assert.equal(avaliar(base(),alterar("memoria_ram",{capacidade_gb:null})).codigo,"ram-nao-identificada");
});

test("peças obrigatórias ausentes e conflitos conhecidos bloqueiam FPS independentemente do ID",()=>{
  for(const id of ["s-1","local","1"]) {
    const build=base();build.id=id;delete build.componentes.fonte;
    assert.equal(avaliar(build).codigo,"build-incompleta");
  }
  assert.equal(avaliar(base(),alterar("placa_mae",{socket:"AM5"})).codigo,"incompativel");
});

test("pendências físicas não são confundidas com ausência de dados de desempenho",()=>{
  const build=base();build.compatibilidade={status:"nao_verificado",naoVerificado:[{codigo:"suporte-cpu-bios",mensagem:"Conferir BIOS."}]};
  assert.equal(avaliar(build).permitido,true);
  const p=catalogo.map(peca=>({...peca,esgotado:true,preco:null}));
  assert.equal(avaliar(build,p).permitido,true,"preço e estoque não mudam as especificações do PC que já possui");
});

test("requisitos mínimos confirmados bloqueiam; abaixo do recomendado não bloqueia",()=>{
  assert.match(motivoRequisitosFps({ram:{atendeMinimo:false}}),/abaixo do mínimo/);
  assert.match(motivoRequisitosFps({ram:{completa:false}}),/totalmente identificada/);
  assert.match(motivoRequisitosFps({ram:{completa:true},impedimentosMinimos:["VRAM insuficiente."]}),/VRAM insuficiente/);
  assert.equal(motivoRequisitosFps({ram:{atendeMinimo:true,completa:true,status:"abaixo_recomendado"},impedimentosMinimos:[]}),"");
  assert.equal(motivoRequisitosFps(null),"");
});

test("argumentos inválidos falham sem aprovar a build",()=>{
  for(const b of [null,{}, {componentes:[]}])assert.equal(avaliar(b).permitido,false);
  assert.equal(avaliarDisponibilidadeFps(base(),null).permitido,false);
});
