import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { completarMedidas } from "../js/build/medidas-fisicas.js";
import { completarCatalogoDemo } from "../js/build/hardware.js";
import { modelosProntos } from "../js/build/modelos.js";
import { avaliarBuild } from "../js/build/compatibilidade.js";
const ler = caminho => JSON.parse(readFileSync(new URL(caminho,import.meta.url)));
const manifesto = ler("../data/medidas-fisicas.json");
for (const {esperado,...dados} of ler("./fixtures/fichas-memoria.json")) test("DDR, slots e limite do anúncio exato: " + dados.part_number,()=>{
  const antiga = {...dados,tipo_memoria:esperado.tipo_memoria === "DDR4" ? "DDR5" : "DDR4",preco:99,esgotado:true};
  const nova = completarMedidas(antiga,manifesto);
  for (const [k,v] of Object.entries(esperado)) assert.equal(nova[k],v);
  assert.equal(nova.preco,99);assert.equal(nova.esgotado,true);
  assert.equal(completarMedidas({...dados,link:"https://www.kabum.com.br/produto/999999"},manifesto).fonte_medidas,undefined);
});
test("curadoria mantém DDR coerente após corrigir variantes no catálogo",()=>{
  const catalogo=completarCatalogoDemo(ler("../data/catalogo-demo.json"),manifesto);
  for (const build of modelosProntos(catalogo)) assert.deepEqual(avaliarBuild(build,catalogo).erros,[],build.titulo);
});
