import test from "node:test";
import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import { definirTextoSeMudou, iconeAnimado } from "../js/components/ui.js";
import { redirecionamentoSessao, linksVisitante, linksAutenticado } from "../js/components/navigation-config.js";
import { perfilLoading } from "../js/components/page-loading.js";
import { ofertasPeca } from "../js/build/catalogo.js";
import { destinoAnterior, rotuloVoltar } from "../js/components/navigation-back.js";

test("tooltip não gera novas mutações ao repetir o mesmo motivo", () => {
  let texto = "", escritas = 0;
  const elemento = {get textContent() { return texto; },set textContent(valor) { texto = valor; escritas++; }};
  for (let i = 0; i < 100; i++) definirTextoSeMudou(elemento,"Preencha o formulário.");
  assert.equal(escritas,1);
  definirTextoSeMudou(elemento,"Aguarde o envio.");
  assert.equal(escritas,2);
});
test("visitante não entra em loop no login e só recebe Entrar/Criar conta no menu", () => {
  assert.equal(redirecionamentoSessao("login.html",false),null);
  assert.equal(redirecionamentoSessao("signin.html",false),null);
  assert.equal(redirecionamentoSessao("formulario.html",false),null);
  assert.equal(redirecionamentoSessao("configuracoes.html",false),"login.html");
  assert.equal(redirecionamentoSessao("login.html",true),"index.html");
  assert.deepEqual(linksVisitante.map(link => link.pagina),["login.html","signin.html"]);
  assert.ok(linksAutenticado.every(link => !link.pagina.includes("#")));
});
test("home mantém velocidade fixa; apenas editor/catálogo/peça aceleram", () => {
  for (const visitada of [true,false]) for (const cache of [true,false]) {
    const home = perfilLoading({home:true,visitada,cache,frequente:true});
    assert.equal(home.modo,"full"); assert.equal(home.velocidade,1); assert.equal(home.velocidadePronta,1);
  }
  const normal = perfilLoading({home:false,visitada:true});
  const frequente = perfilLoading({home:false,visitada:true,frequente:true,cache:true});
  assert.equal(normal.fadeMs,480); assert.equal(normal.velocidadePronta,1);
  assert.ok(frequente.fadeMs < normal.fadeMs); assert.equal(frequente.velocidadePronta,2.2);
});
test("formulário mantém sua política de sessão com espera mínima e fade maior", () => {
  const repetida = perfilLoading({home:false,visitada:true,formulario:true});
  assert.equal(repetida.modo,"fade");
  assert.equal(repetida.minimoMs,800);
  assert.equal(repetida.fadeMs,700);
  const primeira = perfilLoading({home:false,visitada:false,formulario:true});
  assert.equal(primeira.modo,"full");
  assert.equal(primeira.velocidade,1);
  assert.equal(primeira.fadeMs,700);
});
test("retorno preserva a origem completa e o contexto da build", () => {
  const atual = "https://boostio.example/frontend/pages/peca.html?id=cpu&build=b1";
  const origem = "https://boostio.example/frontend/pages/pecas.html?categoria=processador&build=b1#modelos";
  assert.equal(destinoAnterior(atual,origem,"./index.html"),origem);
  assert.equal(rotuloVoltar(origem),"Voltar ao catálogo");
  const editor = "https://boostio.example/frontend/pages/configuracao-build.html?id=b1";
  assert.equal(destinoAnterior(atual,editor,"./pecas.html"),editor);
  assert.equal(rotuloVoltar(editor),"Voltar à build");
});
test("acesso direto ou origem externa usa o destino interno de referência", () => {
  const atual = "https://boostio.example/frontend/pages/pecas.html?categoria=ssd&build=b1";
  const padrao = "./configuracao-build.html?id=b1";
  const destino = "https://boostio.example/frontend/pages/configuracao-build.html?id=b1";
  for (const origem of ["",undefined,"https://external.example/","javascript:alert(1)"]) {
    assert.equal(destinoAnterior(atual,origem,padrao),destino);
  }
});
test("retorno ignora âncoras da própria página e evita voltar à tela de erro", () => {
  const atual = "https://boostio.example/frontend/pages/formulario.html";
  for (const origem of [atual + "#etapa", "https://boostio.example/frontend/pages/erro.html?codigo=500"]) {
    assert.equal(destinoAnterior(atual,origem,"./index.html"),"https://boostio.example/frontend/pages/index.html");
  }
});
test("logos das lojas apontam para os SVGs/PNG disponíveis", async () => {
  const ofertas = ofertasPeca({fabricante:"AMD",modelo:"Modelo",preco:1});
  for (const oferta of ofertas) await access(new URL(oferta.logo));
  assert.ok(ofertas.find(o => o.codigo === "pichau").logo.endsWith("pichau.png"));
});
test("seta de voltar mantém direção independente da animação", () => {
  assert.match(iconeAnimado("arrow","back"),/data-direction="back"/);
});
test("classes de tipografia preservam famílias e tamanhos originais", async () => {
  const css = await readFile(new URL("../styles/utilitarios/tipografia.css",import.meta.url),"utf8");
  for (const [classe,tamanho] of [["font-1-xxl","4rem"],["font-1-xl","3rem"],["font-1-l","1.5rem"],["font-2-s","1.2rem"],["font-2-xs","0.75rem"]]) {
    const bloco = css.match(new RegExp("\\." + classe + "\\s*\\{([^}]+)\\}"))[1];
    assert.ok(bloco.includes("font-size: " + tamanho));
    assert.ok(bloco.includes(classe.startsWith("font-1") ? '"Lexend"' : '"Poppins"'));
  }
});
