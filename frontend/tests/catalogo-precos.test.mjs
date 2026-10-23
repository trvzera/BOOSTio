import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { informacoesPreco, fichaTecnica, ofertasPeca } from "../js/build/catalogo.js";

test("conta distingue preço cadastrado de exemplo e mostra a data disponível", () => {
  const peca = {preco:1234.56,preco_atualizado_em:"2026-10-20T15:30:00+00:00"};
  const conta = informacoesPreco(peca,true);
  assert.equal(conta.rotulo,"Preço cadastrado");
  assert.match(conta.valor,/1\.234,56/);
  assert.match(conta.nota,/20\/10\/2026/);
  assert.match(conta.nota,/não é cotação em tempo real/);
  assert.equal(informacoesPreco(peca).rotulo,"Preço demonstrativo");
});

test("ausência de cotação ou data não vira preço zero ou atualização inventada", () => {
  for (const preco of [null,undefined,0,-1,NaN,Infinity,true,"123"]) {
    const info = informacoesPreco({preco},true);
    assert.equal(info.valor,"Preço não informado");
    assert.match(info.nota,/Data de atualização não informada/);
  }
  const info = informacoesPreco({preco:100,preco_atualizado_em:"<script>",esgotado:true},true);
  assert.match(info.nota,/Data de atualização não informada/);
  assert.match(info.nota,/indisponível/);
  assert.doesNotMatch(info.nota,/<script>|Invalid Date/);
});

test("metadados do preço ficam fora da ficha técnica e a página distingue a conta",async () => {
  assert.deepEqual(fichaTecnica({modelo:"GPU",preco:100,preco_atualizado_em:"2026-10-20T15:30:00Z"}),[["Modelo","GPU"]]);
  const pagina = await readFile(new URL("../js/pages/peca.js",import.meta.url),"utf8");
  assert.match(pagina,/informacoesPreco\(peca,conta\)/);
  assert.match(pagina,/h\(preco\.nota\)/);
});

test("oferta enviada pelo catálogo mostra preço e indisponibilidade só na loja correspondente",()=>{
  const peca={preco:1234.56,link:"https://www.kabum.com.br/produto/123/gpu",ofertas:[
    {loja:"kabum",url:"https://www.kabum.com.br/produto/123/gpu",preco:1234.56,atualizadoEm:"2026-10-23T12:00:00Z",esgotado:true},
  ]};
  const [kabum,pichau]=ofertasPeca(peca);
  assert.equal(kabum.preco,1234.56);assert.equal(kabum.esgotado,true);
  assert.equal(kabum.atualizadoEm,"2026-10-23T12:00:00Z");
  assert.equal(pichau.preco,null);assert.equal(pichau.direta,false);
});
