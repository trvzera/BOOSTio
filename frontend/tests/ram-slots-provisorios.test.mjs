import test from "node:test";
import assert from "node:assert/strict";
import { slotsRam } from "../js/build/hardware.js";
import { normalizarBuild, selecionarPeca, informacoesRam, limiteRam } from "../js/build/estado.js";
import { avaliarBuild, selecionarPecaCompativel, pecaCompativel } from "../js/build/compatibilidade.js";

const placa={id:"placa_mae:1",categoria:"placa_mae",tipo_memoria:"DDR4",quantidade_slots_ram:null};
const ram={id:"memoria_ram:1",categoria:"memoria_ram",ddr:"DDR4",frequencia_mhz:3200,quantidade_pentes:1,capacidade_gb:8};
const catalogo=[placa,ram];
const base=()=>normalizarBuild({componentes:{placa_mae:{id:placa.id}}});

test("slots ausentes ou inválidos usam dois provisórios; zero, um e quatro cadastrados prevalecem",()=>{
  for(const valor of [null,undefined,"","  ",false,true,-1,1.5,"desconhecido",[],NaN,Infinity])
    assert.deepEqual(slotsRam({...placa,quantidade_slots_ram:valor}),{slots:2,provisorio:true});
  for(const valor of [0,1,2,4,"4"])
    assert.deepEqual(slotsRam({...placa,quantidade_slots_ram:valor}),{slots:Number(valor),provisorio:false});
  assert.deepEqual(slotsRam(),{slots:0,provisorio:false});
});
test("placa-mãe sem slots não bloqueia a primeira RAM; dois pentes são permitidos e o terceiro não",()=>{
  let build=base();build=selecionarPecaCompativel(build,ram,catalogo);build=selecionarPecaCompativel(build,ram,catalogo);
  assert.equal(informacoesRam(build,catalogo).usados,2);
  assert.equal(limiteRam(build,catalogo),2);
  assert.equal(pecaCompativel(build,ram,catalogo),false);
  assert.throws(()=>selecionarPeca(build,ram,catalogo),/limite provisório/);
  assert.ok(avaliarBuild(build,catalogo).dicas.some(d=>/provisório.*dois pentes/.test(d)));
  assert.equal(placa.quantidade_slots_ram,null);
});
test("kits e marcas diferentes compartilham o limite provisório sem ignorar DDR",()=>{
  const kit={...ram,id:"memoria_ram:2",quantidade_pentes:2,capacidade_gb:16};
  const outra={...ram,id:"memoria_ram:3"},errada={...ram,id:"memoria_ram:4",ddr:"DDR5"};
  const cat=[...catalogo,kit,outra,errada];
  const comKit=selecionarPecaCompativel(base(),kit,cat);
  assert.equal(informacoesRam(comKit,cat).usados,2);
  assert.equal(pecaCompativel(comKit,ram,cat),false);
  const comUma=selecionarPecaCompativel(base(),ram,cat);
  assert.equal(pecaCompativel(comUma,outra,cat),true);
  assert.equal(pecaCompativel(base(),errada,cat),false);
});
test("selecionar uma placa sem slots depois de três pentes também bloqueia o excesso provisório",()=>{
  const build=normalizarBuild({componentes:{memoria_ram:[{id:ram.id,quantidade:3}]}});
  assert.throws(()=>selecionarPecaCompativel(build,placa,catalogo),/provisório/);
  const zero={...placa,quantidade_slots_ram:0};
  assert.equal(pecaCompativel(base(),ram,[zero,ram]),false);
});
