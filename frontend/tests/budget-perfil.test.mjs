import test from "node:test";
import assert from "node:assert/strict";
import { carregarPerfil, atualizarPerfil, limparPerfil, revisaoPerfil } from "../js/conta/perfil.js";
import { planejamentoLocal } from "../js/build/planejamento.js";
import { atualizarBudgetUsuario } from "../js/api/usuario/atualizarBudgetUsuario.js";

const usuario = (id,budget = 5000,usar_budget = true) => ({id,budget,usar_budget});
const json = (dados,status = 200) => new Response(JSON.stringify(dados),{status,headers:{"Content-Type":"application/json"}});
function preparar(t) {
  const fetchOriginal = globalThis.fetch;
  limparPerfil();
  t.after(() => { globalThis.fetch = fetchOriginal; limparPerfil(); });
}

test("perfil consulta sessão com cookies e sem cache; deduplica somente enquanto pendente",async t => {
  preparar(t);
  let chamadas = 0, resolver;
  globalThis.fetch = (url,opcoes) => {
    chamadas++;
    assert.ok(url.endsWith("/auth/me"));
    assert.equal(opcoes.credentials,"include");
    assert.equal(opcoes.cache,"no-store");
    return new Promise(resolve => { resolver = resolve; });
  };
  const primeira = carregarPerfil(), simultanea = carregarPerfil();
  assert.equal(primeira,simultanea);
  resolver(json({auth:true,usuario:usuario(1,5432.75)}));
  await primeira;
  assert.equal(chamadas,1);
  assert.equal(planejamentoLocal().budget,5432.75);
  const nova = carregarPerfil();
  resolver(json({auth:true,usuario:usuario(2,null,false)}));
  await nova;
  assert.equal(chamadas,2);
  assert.equal(planejamentoLocal().budget,null);
});

test("resposta antiga não restaura budget após logout nem sobrescreve valor recém-salvo",async t => {
  preparar(t);
  let resolver;
  globalThis.fetch = () => new Promise(resolve => { resolver = resolve; });
  const antesLogout = carregarPerfil();
  limparPerfil();
  resolver(json({auth:true,usuario:usuario(1)}));
  assert.equal((await antesLogout).auth,false);
  assert.equal(planejamentoLocal().budget,null);
  const antesSalvar = carregarPerfil();
  atualizarPerfil(usuario(1,7000.1));
  resolver(json({auth:true,usuario:usuario(1,5000)}));
  assert.equal((await antesSalvar).usuario.budget,7000.1);
  assert.equal(planejamentoLocal().budget,7000.1);
});

test("sessão encerrada ou falha de rede não reutiliza budget de outra consulta",async t => {
  preparar(t);
  atualizarPerfil(usuario(1));
  globalThis.fetch = async () => json({auth:false,usuario:null});
  await carregarPerfil();
  assert.equal(planejamentoLocal().budget,null);
  atualizarPerfil(usuario(2,4000));
  globalThis.fetch = async () => { throw new TypeError("offline"); };
  await assert.rejects(carregarPerfil(),/conectar|conexão/);
  assert.equal(planejamentoLocal().budget,null);
  globalThis.fetch = async () => json({auth:true,usuario:usuario(2,4000,false)});
  await carregarPerfil();
  assert.equal(planejamentoLocal().budget,4000);
  assert.equal(planejamentoLocal().usarBudget,false);
});

test("resposta de salvamento atrasada não restaura a conta anterior",async t => {
  preparar(t);
  atualizarPerfil(usuario(1));
  const versao = revisaoPerfil();
  globalThis.fetch = async () => json({auth:true,usuario:usuario(2,3000)});
  await carregarPerfil();
  assert.equal(atualizarPerfil(usuario(1,9000),versao),null);
  assert.equal(planejamentoLocal().budget,3000);
});

test("salvar budget envia apenas valor e autorização à rota do dono, com cookies",async t => {
  preparar(t);
  globalThis.fetch = async (url,opcoes) => {
    if (url.endsWith("/auth/csrf")) {
      assert.equal(opcoes.credentials,"include");
      return json({csrf_token:"csrf-somente-testes"});
    }
    assert.ok(url.endsWith("/usuarios/42/budget"));
    assert.equal(opcoes.method,"PUT");
    assert.equal(opcoes.credentials,"include");
    assert.equal(opcoes.headers["X-CSRF-Token"],"csrf-somente-testes");
    assert.deepEqual(JSON.parse(opcoes.body),{budget:1234.56,usar_budget:true});
    return json({usuario:usuario(42,1234.56)});
  };
  assert.equal((await atualizarBudgetUsuario(42,1234.56,true)).usuario.budget,1234.56);
  // A API não faz salvamento otimista na projeção de perfil.
  assert.equal(planejamentoLocal().budget,null);
});

test("remover budget envia nulo; falhas HTTP/JSON não viram sucesso nem alteram perfil",async t => {
  preparar(t);
  atualizarPerfil(usuario(1));
  globalThis.fetch = async (url,opcoes) => {
    if (url.endsWith("/auth/csrf")) return json({csrf_token:"csrf-somente-testes"});
    assert.deepEqual(JSON.parse(opcoes.body),{budget:null,usar_budget:false});
    return json({erro:"Sem autorização"},403);
  };
  await assert.rejects(atualizarBudgetUsuario(1,null,false),{status:403});
  globalThis.fetch = async url => url.endsWith("/auth/csrf") ? json({csrf_token:"csrf-somente-testes"}) : new Response("<html>erro</html>",{status:500});
  await assert.rejects(atualizarBudgetUsuario(1,3000,true),{status:500});
  assert.equal(planejamentoLocal().budget,5000);
});
