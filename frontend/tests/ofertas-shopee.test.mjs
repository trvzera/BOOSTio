import test from "node:test";
import assert from "node:assert/strict";
import { ofertasPeca } from "../js/build/catalogo.js";
import { cartoesOfertasHtml } from "../js/build/ofertas-peca.js";
import { obterHistoricoDaPeca } from "../js/build/carregar-historico-precos.js";
import { historicoPrecosHtml, normalizarHistoricoPrecos } from "../js/build/price-history.js";

const agora = "2026-11-07T01:00:00+00:00";
const shopee = {id:11, loja:"shopee", produto_id_loja:"10:9", vendedor_id:"10", vendedor_nome:null, url:"https://shopee.com.br/product/10/9", preco:899.9, esgotado:null, atualizadoEm:agora};
const ml = {id:12, loja:"mercado_livre", produto_id_loja:"MLB10", vendedor_id:"7", vendedor_nome:null, url:"https://produto.mercadolivre.com.br/MLB-10-_JM", preco:929, esgotado:null, atualizadoEm:agora};
const kabum = {loja:"kabum", url:"https://www.kabum.com.br/produto/1/x", preco:950, esgotado:false, atualizadoEm:agora};
const peca = ofertas => ({id:"processador:1", categoria:"processador", fabricante:"AMD", modelo:"Ryzen 5 5500", link:kabum.url, ofertas});

test("KaBuM, Pichau, Mercado Livre e Shopee aparecem juntas, cada uma com seu preço", () => {
  const lista = ofertasPeca(peca([kabum, ml, shopee]));
  assert.deepEqual(lista.map(o => [o.loja, o.preco]), [["KaBuM!", 950], ["Mercado Livre", 929], ["Shopee", 899.9], ["Pichau", null]]);
  const loja = lista.find(o => o.codigo === "shopee");
  assert.equal(loja.marketplace, true);
  assert.equal(loja.vendedor, "Loja 10");
  assert.equal(loja.estoqueConfirmado, false);
  assert.equal(lista.find(o => o.codigo === "kabum").marketplace, undefined);
});

test("o cartão da Shopee mostra preço, loja e aviso de estoque não confirmado", () => {
  const html = cartoesOfertasHtml(peca([shopee]));
  assert.match(html, /Shopee/);
  assert.match(html, /R\$\s?899,90/);
  assert.match(html, /estoque não confirmado/);
  assert.match(html, /Loja 10/);
});

test("anúncio da Shopee com endereço de outro domínio, http ou dados inválidos é ignorado", () => {
  const ruins = [
    {url:"https://shopee.com.br.evil.test/product/10/9"}, {url:"http://shopee.com.br/product/10/9"},
    {url:"https://user:senha@shopee.com.br/product/10/9"}, {url:"https://exemplo.com/product/10/9"},
    {id:0}, {preco:0}, {preco:"899,90"}, {vendedor_id:"abc"}, {atualizadoEm:"ontem"},
  ];
  for (const ruim of ruins) assert.equal(ofertasPeca(peca([{...shopee, ...ruim}])).some(o => o.codigo === "shopee"), false, JSON.stringify(ruim));
  for (const url of ["https://s.shopee.com.br/abc", "https://shope.ee/abc", "https://www.shopee.com.br/x"])
    assert.equal(ofertasPeca(peca([{...shopee, url}])).some(o => o.codigo === "shopee"), true, url);
});

test("loja inesperada não vira cartão nem acessa propriedades herdadas do objeto", () => {
  for (const loja of ["constructor", "__proto__", "outra"]) assert.equal(ofertasPeca(peca([{...shopee, loja}])).length, 2);
});

test("histórico da oferta da Shopee valida a loja devolvida e identifica a origem", async () => {
  const p = {id:"processador:1", categoria:"processador"};
  const base = {peca_id:p.id, loja:"shopee", oferta_id:11, historico_precos:[], tem_mais:false};
  const consultarOferta = async () => base;
  assert.deepEqual(await obterHistoricoDaPeca(p, {conta:true, ofertaId:11, lojaOferta:"shopee", consultarOferta}),
    {historico_precos:[], historico_precos_incompleto:false, historico_loja:"shopee"});
  await assert.rejects(obterHistoricoDaPeca(p, {conta:true, ofertaId:11, lojaOferta:"mercado_livre", consultarOferta}));
  await assert.rejects(obterHistoricoDaPeca(p, {conta:true, ofertaId:11, lojaOferta:"outra", consultarOferta}), /Loja da oferta inválida/);

  await assert.rejects(obterHistoricoDaPeca(p, {conta:true, ofertaId:11, consultarOferta}));
});

test("gráfico de histórico da Shopee usa só registros da Shopee", () => {
  const dados = [{data:"2026-11-01", preco:100, loja:"kabum", esgotado:false}, {data:"2026-11-02", preco:200, loja:"shopee", esgotado:null}];
  assert.deepEqual(normalizarHistoricoPrecos(dados, Date.parse("2026-11-07"), "shopee"), [{instante:Date.parse("2026-11-02"), preco:200}]);
  assert.match(historicoPrecosHtml({historico_loja:"shopee", historico_precos:dados}, Date.parse("2026-11-07")), /Shopee/);
});

test("anúncios cadastrados precedem buscas e usam o lottie de seta",()=>{
  const semLink={...peca([ml,shopee]),link:null};
  const ofertas=ofertasPeca(semLink);
  assert.equal(ofertas[0].codigo,'mercado_livre');
  assert.ok(ofertas.slice(0,2).every(o=>o.direta));
  const html=cartoesOfertasHtml(semLink);
  assert.match(html,/data-lottie="arrow" data-direction="external"/);
  assert.doesNotMatch(html,/↗/);
});
