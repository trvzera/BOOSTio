import test from "node:test";
import assert from "node:assert/strict";
import { preferenciasMontagemHtml, prioridadeMontagemValida, preferenciaProcessadorValida } from "../js/build/generation-priority.js";

test("confirmação separa marca da CPU e prioridade, com rádios Lottie e marca neutra por padrão", () => {
  const html = preferenciasMontagemHtml();
  assert.equal((html.match(/type="radio"/g) || []).length, 5);
  assert.equal((html.match(/data-lottie="circledot"/g) || []).length, 5);
  assert.match(html, /name="preferencia_processador" value="sem-preferencia" required checked/);
  assert.doesNotMatch(html, /name="prioridade_montagem"[^>]*checked/);
  assert.match(html, /type="submit"[^>]*disabled/);
  assert.match(html, /aria-describedby="generation-brand-help"/);
  assert.match(html, /não para a placa de vídeo/);
});

test("revisão restaura as duas escolhas sem interpolar valores desconhecidos", () => {
  const html = preferenciasMontagemHtml("custo_beneficio", "intel");
  assert.match(html, /value="intel" required checked/);
  assert.match(html, /value="custo_beneficio" required checked/);
  assert.doesNotMatch(html, /type="submit"[^>]*disabled/);
  assert.doesNotMatch(preferenciasMontagemHtml('<script>', '<script>'), /<script>/);
  for (const valor of [null, {}, [], true, "Intel", "nvidia", ""]) assert.equal(preferenciaProcessadorValida(valor), false);
  for (const marca of ["intel", "amd", "sem-preferencia"]) assert.equal(preferenciaProcessadorValida(marca), true);
  assert.equal(prioridadeMontagemValida("desempenho"), true);
});
