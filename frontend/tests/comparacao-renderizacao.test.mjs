import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { consultarRenderizacoes,classificarRenderizacoes } from "../js/build/comparacao-renderizacao.js";
import { ordenarModelosPorPreco } from "../js/build/modelos.js";

const catalogo=[{id:"cpu-1",categoria:"processador",fabricante:"AMD",modelo:"Ryzen 5 5600",nucleo:6},{id:"cpu-2",categoria:"processador",fabricante:"Intel",modelo:"Core i3-12100F"}];
const build=(id,cpu)=>({id,titulo:id,componentes:{processador:{id:cpu,quantidade:1}}});
const dado=(score,extra={})=>({score,tipo:"cpu",versao:"5.2.0",metodo:"CPU",quantidade:3,...extra});

test("renderização compara a mesma versão/método e trata empate sem somar CPU e GPU",()=>{
  assert.deepEqual(classificarRenderizacoes([{id:"a",dados:dado(100)},{id:"b",dados:dado(150)}]).melhores,["b"]);
  assert.deepEqual(classificarRenderizacoes([{id:"a",dados:dado(100)},{id:"b",dados:dado(100)}]).melhores,["a","b"]);
  for(const dados of [dado(200,{versao:"4.5.0"}),dado(200,{tipo:"gpu",metodo:"CUDA"}),dado(NaN),{score:300}])
    assert.equal(classificarRenderizacoes([{id:"a",dados:dado(100)},{id:"b",dados}]).comparavel,false);
  assert.equal(classificarRenderizacoes([{id:"a",dados:dado(100)},{id:"b",erro:"sem dados"}]).comparavel,false);
});

test("consulta por componente deduplica modelos e reutiliza somente resultados bem-sucedidos no mesmo modal",async()=>{
  let chamadas=0;const cache=new Map(),controle=new AbortController();
  const cliente={consultarBlender:async(parametros,opcoes)=>{chamadas++;assert.equal(parametros.tipo,"cpu");assert.equal(opcoes.signal,controle.signal);return dado(120);}};
  const builds=[build("a","cpu-1"),build("b","cpu-1")];
  const respostas=await consultarRenderizacoes(builds,catalogo,{cliente,cache,signal:controle.signal});
  assert.equal(chamadas,1);assert.equal(respostas.length,2);assert.equal(respostas[0].dados.score,120);
  await consultarRenderizacoes(builds,catalogo,{cliente,cache,signal:controle.signal});assert.equal(chamadas,1);
});

test("falha individual não inventa score e modelos sem identificação não fazem consulta",async()=>{
  let chamadas=0;const cache=new Map();
  const cliente={consultarBlender:async()=>{chamadas++;throw new Error("Dados indisponíveis");}};
  const resultados=await consultarRenderizacoes([build("a","cpu-1"),build("b","desconhecida")],catalogo,{cliente,cache});
  assert.equal(chamadas,1);assert.equal(resultados[0].erro,"Dados indisponíveis");assert.equal(resultados[1].dados,undefined);assert.equal(cache.size,0);
  assert.equal(classificarRenderizacoes(resultados).comparavel,false);
  await assert.rejects(consultarRenderizacoes([],[],{tipo:"outro"}));
});

test("consulta cancelada não fica no cache",async()=>{
  const controle=new AbortController(),cache=new Map();
  const cliente={consultarBlender:async()=>{controle.abort();return dado(123);}};
  await consultarRenderizacoes([build("a","cpu-1")],catalogo,{cliente,cache,signal:controle.signal});
  assert.equal(cache.size,0);
});

test("modelos são ordenados pelo preço cadastrado crescente, com preço ausente ao final",()=>{
  const itens=[{build:{titulo:"C"},avaliacao:{preco:300}},{build:{titulo:"Sem cotação"},avaliacao:{preco:0}},{build:{titulo:"A"},avaliacao:{preco:100}}];
  assert.deepEqual(ordenarModelosPorPreco(itens).map(item=>item.avaliacao.preco),[100,300,0]);
  assert.equal(itens[0].avaliacao.preco,300);
});

test("comparação fica em destaque, estado vazio tem contorno e todo card mostra preço",async()=>{
  const ler=nome=>readFile(new URL(nome,import.meta.url),"utf8");
  const pagina=await ler("../pages/builds.html"),js=await ler("../js/pages/builds-conta.js"),css=await ler("../styles/conta/builds.css");
  assert.match(pagina,/builds-compare-callout/);assert.match(pagina,/class="btn-primary" id="btn-compare-builds"/);
  assert.match(css,/border: 1px dashed var\(--cor-3\)/);assert.match(css,/text-align: center/);
  assert.match(js,/class="build-card-price"/);assert.match(js,/Total parcial/);
  const editor=await ler("../js/pages/configuracao-build.js");
  assert.match(editor,/id="builder-title"/);assert.match(editor,/id="rename-build"/);assert.match(editor,/iconeAnimado\("pencil"\)/);
});
