import test from "node:test";
import assert from "node:assert/strict";
import { ofertasPeca } from "../js/build/catalogo.js";
import { cartoesOfertasHtml } from "../js/build/ofertas-peca.js";
import { obterHistoricoDaPeca } from "../js/build/carregar-historico-precos.js";
import { nomesLojas } from "../js/build/price-history.js";

const agora = "2026-11-24T01:00:00+00:00";
const gigantec = {id:21, loja:"gigantec", produto_id_loja:"35711", vendedor_id:"", vendedor_nome:null,
  url:"https://www.awin1.com/pclick.php?p=1&a=2&m=3", preco:187.9, esgotado:false, atualizadoEm:agora};
const peca = ofertas => ({id:"fonte:1", categoria:"fonte", fabricante:"Rise Mode", modelo:"Elektra X 500W", ofertas});

test("a oferta da Gigantec aparece com o link afiliado, o preço e o nome da loja", () => {
  const loja = ofertasPeca(peca([gigantec])).find(o => o.codigo === "gigantec");
  assert.equal(loja.loja, "Gigantec");
  assert.equal(loja.preco, 187.9);
  assert.equal(loja.vendedor, "Gigantec");
  assert.equal(loja.marketplace, true);
  assert.equal(loja.estoqueConfirmado, true);
  assert.match(cartoesOfertasHtml(peca([gigantec])), /R\$\s?187,90/);
});

test("a Gigantec só aceita links https da Awin ou do site da loja", () => {
  for (const url of ["https://www.awin1.com.evil.test/x", "http://www.awin1.com/x", "https://exemplo.com/x", "https://user:senha@www.awin1.com/x"])
    assert.equal(ofertasPeca(peca([{...gigantec, url}])).some(o => o.codigo === "gigantec"), false, url);
  assert.equal(ofertasPeca(peca([{...gigantec, url:"https://www.gigantec.com.br/p.html"}])).some(o => o.codigo === "gigantec"), true);
  assert.equal(ofertasPeca(peca([{...gigantec, vendedor_id:"123"}])).some(o => o.codigo === "gigantec"), false);
});

test("o histórico por loja reconhece a Gigantec", async () => {
  assert.equal(nomesLojas.gigantec, "Gigantec");
  const consultar = async () => ({peca_id:"fonte:1", loja:"gigantec", historico_precos:[], tem_mais:false});
  const r = await obterHistoricoDaPeca({id:"fonte:1", categoria:"fonte"}, {conta:true, loja:"gigantec", consultar});
  assert.equal(r.historico_loja, "gigantec");
});
