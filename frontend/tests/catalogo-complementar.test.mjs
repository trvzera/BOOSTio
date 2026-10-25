import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { completarMedidas } from "../js/build/medidas-fisicas.js";
import { fichaTecnica, rotulosTecnicos } from "../js/build/catalogo.js";
import { informacoesFans, encaixeRadiador } from "../js/build/fans.js";

const ler = arquivo => JSON.parse(readFileSync(new URL(arquivo,import.meta.url)));
const manifesto = ler("../data/medidas-fisicas.json");
const casos = ler("./fixtures/catalogo-complementar.json");
for (const {esperado,...base} of casos) test("complemento compartilhado: " + base.part_number,() => {
  const original={...base,preco:99,esgotado:false,quantidade:3};
  const peca=completarMedidas(original,manifesto);
  for (const [k,v] of Object.entries(esperado)) assert.deepEqual(peca[k],v,k);
  for (const k of ["preco","esgotado","modelo","part_number"]) assert.equal(peca[k],original[k]);
  assert.equal(original.quantidade,3);
  for (const mudanca of [{link:null},{link:"https://www.kabum.com.br/produto/1"},{modelo:base.modelo + " V2"},{part_number:"outra"}]) {
    assert.equal(completarMedidas({...original,...mudanca},manifesto).fonte_medidas,undefined);
  }
});

test("embalagem avulsa/kit, consumo e ficha legível não são confundidos",() => {
  const fichas=manifesto.pecas.filter(f=>f.verificado_em==="2026-10-24");
  const porPN = pn => fichas.find(f=>f.part_numbers.includes(pn));
  assert.equal(porPN("ACFAN00120A").medidas.quantidade,1);
  assert.equal(porPN("ACFAN00137A").medidas.quantidade,5);
  assert.equal(porPN("ACFAN00137A").medidas.consumo_energia,6);
  assert.equal(porPN("981-000014").medidas.microfone_reducao_ruido,true);
  assert.equal(porPN("981-000014").medidas.cancelamento_ruido,false);
  for (const ficha of fichas) {
    for (const campo of Object.keys(ficha.medidas)) assert.ok(rotulosTecnicos[campo],campo);
    const dados=completarMedidas({categoria:ficha.categoria,fabricante:ficha.fabricante,
      modelo:ficha.modelo,part_number:ficha.part_numbers[0]},manifesto);
    for (const [,valor] of fichaTecnica(dados)) assert.ok(!String(valor).includes("[object Object]"));
  }
});

test("posições condicionais e acessórios opcionais não viram aprovação de encaixe",() => {
  const lian=completarMedidas(casos[2],manifesto), corsair=completarMedidas(casos[3],manifesto);
  const fan={peca:{tamanho_mm:120,quantidade:1},item:{quantidade:11}};
  assert.equal(informacoesFans(lian,[fan]).quantidade,false);
  assert.ok(!lian.radiadores_suportados_mm.includes(420));
  assert.notEqual(encaixeRadiador(lian,{tamanho_radiador_mm:420}),true);
  assert.equal(informacoesFans(corsair,[{...fan,item:{quantidade:8}}]).quantidade,null);
  assert.equal(informacoesFans(corsair,[{...fan,item:{quantidade:8}}]).distribuicao,null);
});
