import test from "node:test";
import assert from "node:assert/strict";
import {paginas,nomePagina,caminhoComparacao,paginaDeTestesLocal} from "../js/components/page-routes.js";
import {paginaPrivada,redirecionamentoSessao} from "../js/components/navigation-config.js";
import {linkDaPaginaAtual} from "../js/components/navigation-current.js";
import {destinoAnterior,destinoBuild,rotuloVoltar} from "../js/components/navigation-back.js";

test("rotas limpas e URLs antigas identificam a mesma página sem perder diretórios locais",() => {
  for(const nome of paginas) {
    const limpa = nome === "index.html" ? "/" : "/" + nome.replace(".html","");
    assert.equal(nomePagina(limpa),nome);
    assert.equal(caminhoComparacao("/pages/" + nome),limpa);
    assert.equal(caminhoComparacao("/" + nome),limpa);
    assert.equal(caminhoComparacao(limpa),limpa);
  }
  assert.equal(caminhoComparacao("/frontend/pages/login.html"),"/frontend/login");
  assert.equal(caminhoComparacao("/js/header.js"),"/js/header.js");
});
test("URLs limpas mantêm a autenticação, o retorno público e a proteção do formulário",() => {
  for(const pagina of ["/", "/login", "/signin", "/sobre", "/termos", "/erro", "/esqueci-senha"]) assert.equal(paginaPrivada(pagina),false,pagina);
  for(const pagina of ["/formulario", "/builds", "/configuracoes", "/pecas", "/peca", "/configuracao-build", "/nao-existe"]) assert.equal(paginaPrivada(pagina),true,pagina);
  assert.equal(redirecionamentoSessao("/login",true),"index.html");
  assert.equal(paginaPrivada("/configuracao-build","?compartilhar_id=s-3"),false);
  assert.equal(paginaPrivada("/configuracao-build","?compartilhar_id=invalido"),true);
});
test("somente o laboratório em loopback pode abrir sem a consulta de sessão", () => {
  for (const url of ["http://127.0.0.1:5501/testes.html", "http://localhost:5500/frontend/testes.html", "http://[::1]:5500/testes"]) {
    assert.equal(paginaDeTestesLocal(new URL(url)), true, url);
  }
  for (const url of ["https://boostio.example/testes", "https://localhost.example/testes.html", "http://127.0.0.1:5501/pages/formulario.html"]) {
    assert.equal(paginaDeTestesLocal(new URL(url)), false, url);
  }
  assert.equal(redirecionamentoSessao("/testes", false), "login.html");
});
test("menu atual e retorno contextual aceitam origem limpa e destino legado",() => {
  assert.equal(linkDaPaginaAtual("/pages/builds.html","https://boostio.example/builds?filtro=teste"),true);
  assert.equal(linkDaPaginaAtual("/pages/builds.html?criar=1","https://boostio.example/builds"),false);
  const atual = "https://boostio.example/peca?id=ssd:1&build=s-3";
  const origem = "https://boostio.example/pecas?categoria=ssd&build=s-3#produto-1";
  assert.equal(destinoAnterior(atual,origem,"/pages/pecas.html?categoria=ssd&build=s-3",true),origem);
  assert.equal(destinoBuild(atual),"./configuracao-build.html?build_id=s-3");
  assert.equal(rotuloVoltar("https://boostio.example/configuracao-build?build_id=s-3"),"Voltar à build");
  assert.equal(destinoAnterior(atual,"https://boostio.example/erro","/builds"),"https://boostio.example/builds");
});
