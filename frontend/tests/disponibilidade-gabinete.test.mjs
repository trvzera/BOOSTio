import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { avaliarGabinetes, validarEstiloGabinete } from "../js/build/disponibilidade-gabinete.js";

const grandeAquario = {categoria:"gabinete",porte_referencia:"full-tower",estilo_referencia:"panoramico",cor_referencia:["preto"],disponivel:true};
test("referências verificadas liberam três estilos grandes sem inventar ofertas no catálogo", () => {
  const dados = JSON.parse(readFileSync(new URL('../data/previa-gabinetes.json',import.meta.url),'utf8'));
  const referencias = JSON.parse(readFileSync(new URL('../data/referencias-gabinetes.json',import.meta.url),'utf8')).modelos;
  const r = validarEstiloGabinete(dados.pecas,{porte:"full-tower",estilo:"panoramico"},referencias);
  assert.deepEqual(r,{bloqueados:["panoramico-3-faces"],estilo:"panoramico",alterado:false});
  assert.equal(avaliarGabinetes(dados.pecas,{porte:"full-tower"}).identificados.length,0);
  for(const referencia of referencias) {
    assert.match(referencia.fonte,/^https:\/\//);
    assert.equal(referencia.verificado_em,"2026-11-16");
    assert.equal("preco" in referencia,false);
    assert.equal("disponivel" in referencia,false);
  }
});
test("tamanho libera somente estilos identificados e preserva a opção sem preferência", () => {
  const pequeno = {...grandeAquario,porte_referencia:"mini-tower",disponivel:false};
  const r = validarEstiloGabinete([pequeno],{porte:"mini-tower",estilo:"panoramico"});
  assert.deepEqual(r,{bloqueados:["discreto","vidro","panoramico-3-faces"],estilo:"panoramico",alterado:false});
  assert.equal(validarEstiloGabinete([pequeno],{porte:"mini-tower",cor:"branco"}).bloqueados.includes("panoramico"),false);
  assert.deepEqual(validarEstiloGabinete([]),{bloqueados:[],estilo:"sem-preferencia",alterado:false});
});
test("troca de tamanho limpa estilo indisponível e fichas incompletas não liberam combinações", () => {
  const r = validarEstiloGabinete([grandeAquario,{categoria:"gabinete",formato:"ATX"}],{porte:"mini-tower",estilo:"panoramico"});
  assert.equal(r.alterado,true);
  assert.equal(r.estilo,"sem-preferencia");
  assert.equal(r.bloqueados.length,4);
  assert.equal(r.bloqueados.includes("sem-preferencia"),false);
  assert.equal(validarEstiloGabinete([grandeAquario],{porte:"full-tower",estilo:"panoramico"}).alterado,false);
});
test("grande e aquário não é uma combinação proibida, e ausência de fichas não prova inexistência", () => {
  const preferencia = {porte:"full-tower",estilo:"panoramico"};
  assert.equal(avaliarGabinetes([grandeAquario],preferencia).estado,"disponivel");
  assert.equal(avaliarGabinetes([],preferencia).estado,"sem-dados");
  assert.equal(avaliarGabinetes([{categoria:"gabinete",formato:"ATX"}],preferencia).estado,"dados-insuficientes");
  assert.equal(avaliarGabinetes([{...grandeAquario,porte_referencia:"mid-tower"}],preferencia).estado,"sem-modelos");
});
test("cor, estoque e dados ausentes são avaliados separadamente", () => {
  assert.equal(avaliarGabinetes([grandeAquario],{cor:"branco"}).estado,"sem-modelos");
  assert.equal(avaliarGabinetes([{...grandeAquario,cor_referencia:[]}],{cor:"branco"}).estado,"dados-insuficientes");
  assert.equal(avaliarGabinetes([{...grandeAquario,disponivel:false}]).estado,"indisponivel");
  assert.equal(avaliarGabinetes([{...grandeAquario,cor_referencia:["preto","branco"]}],{cor:"misto"}).estado,"disponivel");
  assert.equal(avaliarGabinetes([{...grandeAquario,cor_referencia:["preto","branco"]}],{cor:"preto"}).estado,"sem-modelos");
});
