import test from "node:test";
import assert from "node:assert/strict";
import { normalizarHistoricoPrecos, filtrarHistoricoPrecos, historicoPrecosHtml } from "../js/build/price-history.js";
import { fichaTecnica } from "../js/build/catalogo.js";

const agora = Date.parse("2026-11-02T12:00:00Z");
const registro = (data, preco, extras = {}) => ({data, preco, loja:"kabum", ...extras});

test("histórico ausente não transforma preço atual ou demonstrativo em cotações anteriores", () => {
  for (const historico_precos of [undefined, null, {}, "texto", []]) {
    const html = historicoPrecosHtml({preco:1500, preco_atualizado_em:"2026-11-02", historico_precos}, agora);
    assert.match(html, /Ainda não há histórico desta peça/);
    assert.doesNotMatch(html, /<svg|<table|data-history-period=|1\.500/);
  }
});

test("aceita somente preços positivos finitos com data válida e origem KaBuM", () => {
  const registros = [registro("2026-11-01", 500), registro("2026-02-30", 100), registro("2026-11-03", 200),
    registro("2026-11-01", "300"), registro("2026-11-01", null), registro("2026-11-01", 0),
    registro("2026-11-01", -100), registro("2026-11-01", Infinity), registro("2026-11-01", NaN),
    registro("2026-11-01", 100, {esgotado:true}), registro("2026-11-01", 100, {loja:"pichau"}),
    registro("2026-11-01", 100, {loja:null}), registro("2026-11-01T15:00:00", 100),
    registro("2026-11-01T24:10:00Z", 100), registro("<img src=x onerror=alert(1)>", 100), null];
  assert.deepEqual(normalizarHistoricoPrecos(registros, agora), [{instante:Date.parse("2026-11-01T00:00:00Z"), preco:500}]);
});

test("ordena as datas, aceita horário com fuso e mantém um preço por instante sem alterar a entrada", () => {
  const registros = [registro("2026-11-02T09:00:00-03:00", 700), registro("2026-11-01", 600),
    registro("2026-11-01", 650, {loja:" KaBuM! "})];
  const antes = structuredClone(registros);
  assert.deepEqual(normalizarHistoricoPrecos(registros, agora), [
    {instante:Date.parse("2026-11-01T00:00:00Z"), preco:650}, {instante:agora, preco:700}]);
  assert.deepEqual(registros, antes);
});

test("filtro de trinta dias usa datas corridas, inclui hoje e não as últimas trinta observações", () => {
  const todos = normalizarHistoricoPrecos([registro("2026-08-01", 400), registro("2026-10-03", 500),
    registro("2026-10-04", 600), registro("2026-11-02", 700)], agora);
  assert.deepEqual(filtrarHistoricoPrecos(todos, "30", agora).map(r => r.preco), [600, 700]);
  assert.deepEqual(filtrarHistoricoPrecos(todos, "90", agora).map(r => r.preco), [500, 600, 700]);
  assert.deepEqual(filtrarHistoricoPrecos(todos, "todos", agora), todos);
  assert.notEqual(filtrarHistoricoPrecos(todos, "todos", agora), todos);
  assert.deepEqual(filtrarHistoricoPrecos(todos, "invalido", agora), []);
});

test("um registro ou preços constantes não sugerem tendência nem geram coordenadas inválidas", () => {
  const unico = historicoPrecosHtml({historico_precos:[registro("2026-11-02", 500)]}, agora);
  assert.match(unico, /Ainda não é possível mostrar uma tendência/);
  assert.match(unico, /Ver registros de preços/);
  assert.doesNotMatch(unico, /NaN|Infinity/);
  const constante = historicoPrecosHtml({historico_precos:[registro("2026-11-01", 500), registro("2026-11-02", 500)]}, agora);
  assert.match(constante, /M12\.00 100\.00 L628\.00 100\.00/);
  assert.doesNotMatch(constante, /NaN|Infinity/);
});

test("a alternativa em tabela e o resumo mantêm os valores reais sem misturar lojas", () => {
  const html = historicoPrecosHtml({historico_precos:[registro("2026-10-01", 800), registro("2026-10-15", 500),
    registro("2026-11-01", 700), registro("2026-11-01", 1, {loja:"outra"})]}, agora);
  assert.match(html, /Histórico de preços/);
  for (const valor of ["800,00", "500,00", "700,00"]) assert.ok(html.includes(valor));
  assert.match(html, /<th scope="col">Data<\/th><th scope="col">Preço<\/th>/);
  assert.match(html, /aria-pressed="true">Todo o período/);
  assert.match(html, /role="status" aria-atomic="true"/);
  assert.match(html, /Valores registrados, sem frete/);
});

test("série histórica não aparece como especificação técnica da peça", () => {
  const campos = fichaTecnica({categoria:"memoria_ram",capacidade:16,historico_precos:[registro("2026-11-01", 500)]});
  assert.ok(!campos.some(([rotulo]) => /historico|histórico/i.test(rotulo)));
});
