import test from "node:test";
import assert from "node:assert/strict";
import { destinoAnterior, destinoBuild } from "../js/components/navigation-back.js";

const base="https://boostio.example/pages/";
test("Voltar à build não aceita início, outra build ou página externa do histórico",()=>{
  const atual=base+"pecas.html?categoria=processador&build=s-3";
  const destino=base+"configuracao-build.html?build_id=s-3";
  for(const anterior of [base+"index.html",base+"configuracao-build.html?build_id=s-2",base+"builds.html","https://outro.example/",null])
    assert.equal(destinoAnterior(atual,anterior,"./configuracao-build.html?build_id=s-3",true),destino);
});
test("retorno contextual preserva filtros e hash somente na mesma categoria/build",()=>{
  const atual=base+"peca.html?id=processador:1&build=s-3";
  const padrao="./pecas.html?categoria=processador&build=s-3";
  const origem=base+"pecas.html?build=s-3&categoria=processador&marca=AMD#produto-1";
  assert.equal(destinoAnterior(atual,origem,padrao,true),origem);
  for(const errada of [origem.replace("s-3","s-4"),origem.replace("categoria=processador","categoria=placa_mae")])
    assert.equal(destinoAnterior(atual,errada,padrao,true),new URL(padrao,atual).href);
});
test("voltar genérico continua respeitando a página anterior, sem destinos inseguros",()=>{
  const atual=base+"sobre.html";
  assert.equal(destinoAnterior(atual,base+"termos.html","./index.html"),base+"termos.html");
  assert.equal(destinoAnterior(atual,"https://externo.example/","./index.html",true),base+"index.html");
  assert.equal(destinoAnterior(atual,"javascript:alert(1)","javascript:alert(1)",true),base+"index.html");
});
test("retorno de falha mantém ID da conta/local e nunca inicia build sem ID",()=>{
  assert.equal(destinoBuild(base+"pecas.html?build=s-12"),"./configuracao-build.html?build_id=s-12");
  assert.equal(destinoBuild(base+"peca.html?id=ssd:1&build=demo-1"),"./configuracao-build.html?id=demo-1");
  assert.equal(destinoBuild(base+"pecas.html?build=a%26b%22"),"./configuracao-build.html?id=a%26b%22");
  for(const atual of ["pecas.html","peca.html?build=","configuracao-build.html?build_id=s-1","pecas.html?build=%20"])
    assert.equal(destinoBuild(base+atual),"./builds.html");
});
