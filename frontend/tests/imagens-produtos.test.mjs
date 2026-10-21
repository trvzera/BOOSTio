import test from "node:test";
import assert from "node:assert/strict";
import { readFile,access } from "node:fs/promises";
import { completarImagens,enderecoImagem,iniciarImagens,carregarManifestoImagens } from "../js/build/imagens-produtos.js";
import { imagemPeca } from "../js/build/catalogo.js";

test("mapa de imagens usa part number exato, sem confundir nomes ou IDs de bancos diferentes",() => {
  const origem=[{id:"processador:999",part_number:"CPU-A",modelo:"Modelo"},{id:"processador:1",part_number:"OUTRO",modelo:"Modelo"}];
  const resultado=completarImagens(origem,{"CPU-A":"../imgs/produtos/processador-1.jpg"});
  assert.equal(resultado[0].imagem,"../imgs/produtos/processador-1.jpg");
  assert.equal(resultado[0].id,"processador:999");
  assert.equal(resultado[1].imagem,null);
  assert.equal(origem[0].imagem,undefined);
});

test("imagem informada pela API tem prioridade e URLs inválidas não bloqueiam alternativa exata",() => {
  const mapa={A:"../imgs/produtos/processador-1.jpg"};
  assert.equal(completarImagens([{part_number:"A",imagem:"https://cdn.example.test/cpu.webp"}],mapa)[0].imagem,"https://cdn.example.test/cpu.webp");
  assert.equal(completarImagens([{part_number:"A",imagem_url:"https://cdn.example.test/outro.webp"}],mapa)[0].imagem,"https://cdn.example.test/outro.webp");
  assert.equal(completarImagens([{part_number:"A",imagem:"javascript:alert(1)"}],mapa)[0].imagem,mapa.A);
  for(const valor of [null,1,{},"javascript:alert(1)","java\nscript:alert(1)","data:image/svg+xml,test","file:///etc/passwd"])
    assert.equal(enderecoImagem(valor),"");
});

test("caminhos de imagens independem de estar em pages ou no laboratório",() => {
  const caminho="../imgs/produtos/processador-1.jpg";
  const esperado=new URL("../imgs/produtos/processador-1.jpg",import.meta.url).href;
  assert.equal(enderecoImagem(caminho),esperado);
  const html=imagemPeca({categoria:"processador",modelo:'CPU <teste>',imagem:caminho});
  assert.ok(html.includes('src="'+esperado+'"'));
  assert.match(html,/alt="CPU &lt;teste&gt;"/);
  assert.match(html,/width="160" height="160" loading="lazy" decoding="async"/);
  assert.match(html,/data-product-placeholder hidden/);
});

test("as imagens do manifesto existem nos caminhos publicados",async () => {
  const mapa=JSON.parse(await readFile(new URL("../data/imagens-produtos.json",import.meta.url),"utf8"));
  assert.ok(Object.keys(mapa).length>0);
  await Promise.all(Object.values(mapa).map(caminho=>access(new URL(caminho,new URL("../pages/",import.meta.url)))));
});

test("imagem sem vínculo fica neutra e uma foto quebrada exibe alternativa sem repetir listeners",() => {
  assert.doesNotMatch(imagemPeca({categoria:"processador"}),/<img/);
  let listener,chamadas=0;
  const alternativa={hidden:true,hasAttribute:nome=>nome==="data-product-placeholder"};
  const imagem={hidden:false,complete:false,nextElementSibling:alternativa,addEventListener:(nome,acao)=>{assert.equal(nome,"error");chamadas++;listener=acao;}};
  const raiz={querySelectorAll:()=>[imagem]};
  iniciarImagens(raiz);iniciarImagens(raiz);
  assert.equal(chamadas,1);listener();
  assert.equal(imagem.hidden,true);assert.equal(alternativa.hidden,false);
});

test("falha no manifesto não derruba catálogo e permite nova consulta",async t => {
  let chamadas=0;
  t.mock.method(globalThis,"fetch",async()=>{
    chamadas++;
    return new Response(JSON.stringify(chamadas===1?{}:{A:"../imgs/produtos/processador-1.jpg"}),{status:chamadas===1?503:200});
  });
  assert.deepEqual(await carregarManifestoImagens(),{});
  assert.equal((await carregarManifestoImagens()).A,"../imgs/produtos/processador-1.jpg");
  assert.equal(chamadas,2);
});
