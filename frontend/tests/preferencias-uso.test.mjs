import test from "node:test";
import assert from "node:assert/strict";
import { preferenciasUso, tutorialPendente, ajustarGuiasConhecimento } from "../js/conta/preferencias-uso.js";
import { atualizarPerfil, perfilAtual, limparPerfil } from "../js/conta/perfil.js";
import { salvarPreferenciasDaConta } from "../js/conta/salvar-preferencias-uso.js";

const prefs = (nivel,tutorial="concluido") => ({nivel_hardware:nivel,tutorial,versao_tutorial:1});
const usuario = (id,nivel) => ({id,budget:5000,usar_budget:true,preferencias_uso:prefs(nivel)});
const json = dados => new Response(JSON.stringify(dados),{headers:{"Content-Type":"application/json"}});

test("somente tutorial pendente da versão conhecida dispara apresentação automática",() => {
  assert.equal(tutorialPendente({id:1}),false);
  assert.equal(tutorialPendente({preferencias_uso:prefs(null,"pendente")}),true);
  for(const tutorial of ["pulado","concluido","nao-oferecido","outro"])
    assert.equal(tutorialPendente({preferencias_uso:prefs(null,tutorial)}),false);
  assert.equal(tutorialPendente({preferencias_uso:{...prefs(null,"pendente"),versao_tutorial:2}}),false);
  assert.equal(preferenciasUso({preferencias_uso:{nivel_hardware:"<script>"}}).nivel_hardware,null);
});

test("guias ajustam apresentação sem impedir abertura manual",t => {
  const guia={dataset:{},open:false};
  const antigo=globalThis.document;
  globalThis.document={documentElement:{dataset:{hardwareLevel:"experiente"}}};
  t.after(()=>{if(antigo)globalThis.document=antigo;else delete globalThis.document;});
  const raiz={querySelectorAll:()=>[guia]};
  ajustarGuiasConhecimento(raiz);assert.equal(guia.open,false);
  guia.open=true;ajustarGuiasConhecimento(raiz);assert.equal(guia.open,true);
  document.documentElement.dataset.hardwareLevel="iniciante";
  ajustarGuiasConhecimento(raiz);assert.equal(guia.open,true);
  document.documentElement.dataset.hardwareLevel="intermediario";guia.open=false;
  ajustarGuiasConhecimento(raiz);assert.equal(guia.open,true);
});

test("salvamento usa CSRF e só atualiza a própria conta com resposta confirmada",async t => {
  const anterior=globalThis.fetch;atualizarPerfil(usuario(1,null));
  t.after(()=>{globalThis.fetch=anterior;limparPerfil();});
  globalThis.fetch=async(url,opcoes)=>{
    if(url.endsWith("/auth/csrf"))return json({csrf_token:"teste"});
    assert.ok(url.endsWith("/usuarios/1/preferencias-uso"));
    assert.equal(opcoes.method,"PUT");assert.equal(opcoes.credentials,"include");
    assert.equal(opcoes.headers["X-CSRF-Token"],"teste");
    assert.deepEqual(JSON.parse(opcoes.body),{nivel_hardware:"iniciante"});
    return json({usuario:usuario(1,"iniciante")});
  };
  await salvarPreferenciasDaConta(1,{nivel_hardware:"iniciante"});
  assert.equal(perfilAtual().usuario.preferencias_uso.nivel_hardware,"iniciante");
  assert.equal(perfilAtual().usuario.budget,5000);
});

test("resposta incompleta não é anunciada como preferência salva",async t => {
  const anterior=globalThis.fetch;atualizarPerfil(usuario(1,null));
  t.after(()=>{globalThis.fetch=anterior;limparPerfil();});
  globalThis.fetch=async url=>json(url.endsWith("/auth/csrf")?{csrf_token:"teste"}:{usuario:{id:1}});
  await assert.rejects(salvarPreferenciasDaConta(1,{nivel_hardware:"iniciante"}),/confirmar/);
  assert.equal(perfilAtual().usuario.preferencias_uso.nivel_hardware,null);
});

test("resposta atrasada não aplica preferências de outra sessão",async t => {
  const anterior=globalThis.fetch;atualizarPerfil(usuario(1,"iniciante"));
  t.after(()=>{globalThis.fetch=anterior;limparPerfil();});
  let resolver, iniciou;
  const enviado=new Promise(r=>{iniciou=r;});
  globalThis.fetch=async url=>{
    if(url.endsWith("/auth/csrf"))return json({csrf_token:"teste"});
    iniciou();return new Promise(r=>{resolver=r;});
  };
  const salvar=salvarPreferenciasDaConta(1,{nivel_hardware:"experiente"});
  await enviado;atualizarPerfil(usuario(2,"intermediario"));resolver(json({usuario:usuario(1,"experiente")}));
  await assert.rejects(salvar,/mudaram/);
  assert.equal(perfilAtual().usuario.id,2);
  assert.equal(perfilAtual().usuario.preferencias_uso.nivel_hardware,"intermediario");
});
