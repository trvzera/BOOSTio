import test from "node:test";
import assert from "node:assert/strict";
import { autoriaBuildHtml } from "../js/build/autoria.js";
import { buildDaConta, estadoParaConta } from "../js/build/conta.js";

test("autoria mostra o nome de exibição escapado e mantém builds legadas sem rótulo falso",()=>{
  assert.equal(autoriaBuildHtml({}),"");
  assert.equal(autoriaBuildHtml({criador:{nome:"  "}}),"");
  const html=autoriaBuildHtml({criador:{nome:'Ana <script> & "B"'}});
  assert.match(html,/Criada por/);
  assert.match(html,/Ana &lt;script&gt; &amp; &quot;B&quot;/);
  assert.doesNotMatch(html,/<script>/);
});

test("autoria é metadado da API, não expõe perfil nem entra no estado enviado",()=>{
  const build=buildDaConta({id:"s-1",nome:"Teste",criado_em:"2026-10-24T12:00:00Z",estado:{componentes:{}},
    criador:{nome:"Giovanni",id:99,email:"nao-exibir@example.test",budget:5000}});
  assert.deepEqual(build.criador,{nome:"Giovanni"});
  assert.ok(!("criador" in estadoParaConta(build)));
  assert.doesNotMatch(autoriaBuildHtml(build),/nao-exibir|5000|99/);
});

test("autoria inválida ou antiga sem metadado não interrompe o editor",()=>{
  for(const criador of [null,{},"Nome",{nome:123},{nome:""}]) {
    const build=buildDaConta({id:"s-1",nome:"Teste",estado:{componentes:{}},criador});
    assert.equal(autoriaBuildHtml(build),"");
  }
});
