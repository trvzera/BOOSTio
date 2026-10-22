import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { textoBuildsSalvas,textoBudgetPerfil } from "../js/conta/resumo-perfil.js";
import { listarBuilds } from "../js/api/build/builds.js";

test("contagem usa todas as builds da resposta, com zero e singular corretos",()=>{
  assert.equal(textoBuildsSalvas([]),"0 builds salvas");
  assert.equal(textoBuildsSalvas([{id:"s-1"}]),"1 build salva");
  assert.equal(textoBuildsSalvas([{id:"s-1"},{id:"s-2"},{id:"s-3"}]),"3 builds salvas");
  for(const valor of [undefined,null,{},3])assert.throws(()=>textoBuildsSalvas(valor));
});

test("pill mostra budget salvo sem confundir ausência, zero e falha",()=>{
  assert.match(textoBudgetPerfil({id:1,budget:5432.75,usar_budget:false}),/^Budget: R\$\s5\.432,75$/);
  assert.match(textoBudgetPerfil({id:1,budget:0}),/^Budget: R\$\s0,00$/);
  assert.equal(textoBudgetPerfil({id:1,budget:null}),"Budget não definido");
  assert.equal(textoBudgetPerfil(null),"Budget indisponível");
  for(const budget of ["5000",-1,Infinity,NaN,1000001])assert.equal(textoBudgetPerfil({id:1,budget}),"Budget indisponível");
});

test("listagem do perfil preserva sessão e permite cancelar sem escrita",async t=>{
  const controle=new AbortController();
  t.mock.method(globalThis,"fetch",async(url,opcoes)=>{
    assert.ok(url.endsWith("/build/"));assert.equal(opcoes.method,"GET");
    assert.equal(opcoes.signal,controle.signal);assert.equal(opcoes.credentials,"include");
    return new Response(JSON.stringify({builds:[]}));
  });
  assert.deepEqual(await listarBuilds({signal:controle.signal}),{builds:[]});
});

test("perfil deixa placeholders explícitos, atualiza após salvar e mantém alinhamentos",async()=>{
  const ler=nome=>readFile(new URL(nome,import.meta.url),"utf8");
  const html=await ler("../pages/configuracoes.html"),js=await ler("../js/pages/budget-perfil.js");
  assert.doesNotMatch(html,/X builds salvas/);
  assert.match(html,/id="profile-build-count" role="status"/);
  assert.match(html,/id="profile-budget-summary" role="status"/);
  assert.match(js,/atualizarResumo\(resposta\.usuario\)/);
  const css=await ler("../styles/responsividades/r-configuracoes.css");
  assert.match(css,/\.card-heading \{ align-items: center; \}/);
  assert.match(css,/#budget-profile-form \.planning-consent\.ui-check \{ display: flex; align-items: center; \}/);
});

test("hamburger restaura setas sem colocar setas nas ações do perfil",async()=>{
  const js=await readFile(new URL("../js/header.js",import.meta.url),"utf8");
  assert.match(js,/perfil \? '' : iconeAnimado\("arrow"\)/);
  assert.match(js,/\[data-menu-auth\]/);
});
