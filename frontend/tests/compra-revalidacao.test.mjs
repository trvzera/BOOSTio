import test from "node:test";
import assert from "node:assert/strict";
import { compararCatalogosCompra } from "../js/build/compra-revalidacao.js";
import { catalogoBuilds } from "../js/api/build/builds.js";
import { conteudoCompra } from "../js/build/acoes-build.js";
const antes=[{id:"ram",categoria:"memoria_ram",preco:100,esgotado:false}];
const build={componentes:{memoria_ram:[{id:"ram",quantidade:2}]}};
test("compra compara centavos e quantidades sem alterar build ou catálogo",()=>{
  const copia=structuredClone(build),atual=[{...antes[0],preco:120.15}];
  const r=compararCatalogosCompra(build,antes,atual);
  assert.equal(r.antes,20000);assert.equal(r.depois,24030);assert.equal(r.diferenca,4030);
  assert.equal(r.linhas[0].alterado,true);assert.equal(r.parcial,false);assert.deepEqual(build,copia);assert.equal(antes[0].preco,100);
});
test("sem estoque, preço ou peça não simula oferta nem diferença completa",()=>{
  for (const atual of [[{...antes[0],esgotado:true}],[{...antes[0],preco:0}],[{...antes[0],esgotado:null}],[]]) {
    const r=compararCatalogosCompra(build,antes,atual);
    assert.equal(r.linhas[0].indisponivel,true);assert.equal(r.parcial,true);
  }
  assert.equal(compararCatalogosCompra(build,antes,[]).diferenca,null);
});
test("preço menor e peça própria não viram economia ou preço inventado",()=>{
  assert.equal(compararCatalogosCompra(build,antes,[{...antes[0],preco:90}]).diferenca,-2000);
  const propria={componentes:{ssd:[{proprio:"Meu SSD",quantidade:1}]}};
  assert.equal(compararCatalogosCompra(propria,[],[]).diferenca,null);
});
test("compra força reconsulta sem cache do navegador",async()=>{
  const original=globalThis.fetch;
  globalThis.fetch=async(url,opcoes)=>{
    assert.equal(opcoes.cache,"no-store");assert.equal(opcoes.method,"GET");
    return {ok:true,status:200,json:async()=>({pecas:antes})};
  };
  try {assert.deepEqual((await catalogoBuilds({cache:"force-cache"})).pecas,antes);}
  finally {globalThis.fetch=original;}
});

test("compra lista links por peça mesmo com cabo ou Wi-Fi a incluir",()=>{
  for(const tipo of ["cabo","wifi"]) {
    const peca={id:"cpu",categoria:"processador",fabricante:"Teste",modelo:"CPU",preco:100,esgotado:false,
      link:"https://www.kabum.com.br/produto/123/modelo"};
    const atual={componentes:{processador:{id:"cpu",quantidade:1}},incluirRede:true,rede:{tipo,possuiAcessorio:false}};
    const original=structuredClone(atual);
    const html=conteudoCompra(atual,[peca],compararCatalogosCompra(atual,[peca],[peca]));
    assert.match(html,/Acessório de rede a incluir/);
    assert.match(html,/https:\/\/www\.kabum\.com\.br\/produto\/123\/modelo/);
    assert.match(html,/Quantidade: 1/);
    assert.deepEqual(atual,original);
    const cat=tipo==="cabo"?"cabo_rede":"adaptador_wifi";
    atual.componentes[cat]={id:"rede",quantidade:1};
    const catalogo=[peca,{id:"rede",categoria:cat,fabricante:"Teste",modelo:"Rede",preco:10,esgotado:false}];
    assert.doesNotMatch(conteudoCompra(atual,catalogo,compararCatalogosCompra(atual,catalogo,catalogo)),/Acessório de rede a incluir/);
  }
});
