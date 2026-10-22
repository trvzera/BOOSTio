import test from "node:test";
import assert from "node:assert/strict";
import { access, readFile, readdir } from "node:fs/promises";
import { definirTextoSeMudou, iconeAnimado } from "../js/components/ui.js";
import { redirecionamentoSessao, linksVisitante, linksAutenticado } from "../js/components/navigation-config.js";
import { perfilLoading } from "../js/components/page-loading.js";
import { ofertasPeca } from "../js/build/catalogo.js";
import { destinoAnterior, rotuloVoltar } from "../js/components/navigation-back.js";
import { avisoFreteHtml } from "../js/build/acoes-build.js";

test("nomes acessíveis preservam o texto visível dos botões para controle por voz",async () => {
  const fontes = [
    ['../js/pages/forms.js','aria-label="Voltar à etapa anterior"'],
    ['../pages/builds.html','aria-label="Comparar builds salvas na minha conta"'],
    ['../pages/configuracoes.html','aria-label="Confirmar identidade com Google para alterar o perfil"'],
    ['../js/pages/configuracoes-prontas.js','aria-label="Abrir build e personalizar: '],
  ];
  for (const [arquivo,rotulo] of fontes) assert.ok((await readFile(new URL(arquivo,import.meta.url),'utf8')).includes(rotulo));
  const carrossel=await readFile(new URL('../js/services-carousel.js',import.meta.url),'utf8');
  assert.match(carrossel,/cardsGrid\.tabIndex = 0/);
  assert.match(carrossel,/cardsGrid\.setAttribute\("role","region"\)/);
  assert.match(carrossel,/cardsGrid\.removeAttribute\("tabindex"\)/);
});

test("montagem lembra de reservar orçamento para frete sem inventar uma cotação",() => {
  const aviso = avisoFreteHtml();
  assert.match(aviso,/Frete não incluído/);
  assert.match(aviso,/Reserve parte do orçamento para a entrega/);
  assert.match(aviso,/CEP e as lojas escolhidas/);
  assert.match(aviso,/class="shipping-notice planning-help" role="note"/);
  assert.doesNotMatch(aviso,/R\$|\d+%|role="alert"/);
});

test("aviso de frete fica junto ao total e também acompanha a compra da build",async () => {
  const editor = await readFile(new URL("../js/pages/configuracao-build.js",import.meta.url),"utf8");
  const salva = await readFile(new URL("../js/build/build-salva.js",import.meta.url),"utf8");
  const acoes = await readFile(new URL("../js/build/acoes-build.js",import.meta.url),"utf8");
  const css = await readFile(new URL("../styles/build/recursos.css",import.meta.url),"utf8");
  assert.match(editor,/'<\/strong>' \+ avisoFreteHtml\(\) \+ '<div class="summary-power"/);
  assert.match(salva,/class="summary-total">[^\n]+\n\s*\$\{avisoFreteHtml\(\)\}/);
  assert.match(acoes,/avisoFreteHtml\(\) \+ avisoCompraHtml\(\) \+ '<div class="build-purchase-list"/);
  assert.match(css,/\.shipping-notice strong \{[^}]*color: var\(--cor-p1\)/);
});

test("sair e excluir conta mantêm perigo vermelho, sem alterar a verificação de e-mail",async () => {
  const menu = await readFile(new URL("../styles/componentes/site-menu.css",import.meta.url),"utf8");
  const conta = await readFile(new URL("../styles/conta/configuracoes.css",import.meta.url),"utf8");
  assert.match(menu,/\.profile-logout:hover, \.profile-logout:focus-visible\s*\{[^}]*color: var\(--status-error\)/s);
  assert.match(conta,/#delete-modal \.modal-icon\s*\{[^}]*color: var\(--status-error\)/s);
});

test("checkboxes compartilham fonte e cor e detalhes não desativam sticky no desktop",async () => {
  const ui = await readFile(new URL("../styles/componentes/ui-system.css",import.meta.url),"utf8");
  const editor = await readFile(new URL("../styles/responsividades/r-editor-build.css",import.meta.url),"utf8");
  assert.match(ui,/\.ui-check \{[^}]*font-family: var\(--font-body\);[^}]*color: var\(--cor-6\)/s);
  assert.doesNotMatch(editor,/\.build-sidebar:has\(\.summary-metadata\[open\]\)\s*\{[^}]*position: static/s);
  assert.match(editor,/@media \(max-height: 760px\)/);
});

test("menu lateral não inclui ícones das opções, mantendo os do perfil",async () => {
  const js = await readFile(new URL("../js/header.js",import.meta.url),"utf8");
  assert.match(js,/perfil && item\.icone \? iconeAnimado\(item\.icone\)/);
});

test("configurações enquadra o Lottie sem escala CSS e tem fallback reconhecível",async () => {
  const js = await readFile(new URL("../js/components/ui.js",import.meta.url),"utf8");
  const css = await readFile(new URL("../styles/componentes/site-menu.css",import.meta.url),"utf8");
  const arquivo = JSON.parse(await readFile(new URL("../lottie/user.json",import.meta.url),"utf8"));
  assert.equal(arquivo.w,1000); assert.equal(arquivo.h,1000);
  assert.match(js,/elemento\.dataset\.lottie === "user"\s*\? \{rendererSettings:\{viewBoxSize:"175 170 750 750"/);
  assert.match(js,/registrarAnimacao\([^;]+,opcoes\)/);
  assert.doesNotMatch(css,/\[data-lottie="user"\] svg\s*\{\s*transform: scale/);
  assert.match(css,/\.profile-link:focus-visible \.ui-lottie \{ color: inherit; \}/);
  const icone = iconeAnimado("user");
  assert.match(icone,/aria-hidden="true"/); assert.match(icone,/<svg viewBox="0 0 24 24"/);
  assert.doesNotMatch(icone,/●/);
});

test("seletores de montagem e desempenho registram os quatro novos Lotties com alternativa estática",async () => {
  const ui = await readFile(new URL("../js/components/ui.js",import.meta.url),"utf8");
  for (const nome of ["gamepad","microchip","handsparkle","normalhand"]) {
    assert.ok(ui.includes(nome + ':"' + nome + '.json"'));
    const arquivo = JSON.parse(await readFile(new URL("../lottie/" + nome + ".json",import.meta.url),"utf8"));
    assert.ok(arquivo.w > 0 && arquivo.h > 0 && arquivo.op > arquivo.ip && arquivo.fr > 0);
    const icone = iconeAnimado(nome);
    assert.ok(icone.includes('data-lottie="' + nome + '"'));
    assert.match(icone,/aria-hidden="true"/);
    assert.match(icone,/<span class="ui-icon-fallback"><svg viewBox="0 0 24 24"/);
  }
});

test("montagem e benchmark usam os ícones correspondentes sem alterar ações e rótulos",async () => {
  const builds = await readFile(new URL("../js/pages/builds-conta.js",import.meta.url),"utf8");
  const acoes = await readFile(new URL("../js/build/acoes-build.js",import.meta.url),"utf8");
  const css = await readFile(new URL("../styles/build/recursos.css",import.meta.url),"utf8");
  for (const [nome,rotulo] of [["handsparkle","Formulário inteligente"],["normalhand","Montagem manual"]])
    assert.ok(builds.includes('iconeAnimado("' + nome + '") + \'<strong>' + rotulo + '</strong>'));
  for (const [nome,rotulo] of [["gamepad","Jogos · FPS"],["microchip","Blender · Renderização"]])
    assert.ok(acoes.includes('iconeAnimado("' + nome + '") + \'<span>' + rotulo + '</span>'));
  assert.match(css,/\.build-create-option:is\(:hover,:focus-visible\)/);
  assert.match(css,/\.build-create-option > \.ui-lottie \{[^}]*color: var\(--cor-p1\)/);
  assert.match(css,/span:not\(\.build-create-option-action\):not\(\.ui-lottie\)/);
});

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
  assert.equal(redirecionamentoSessao("formulario.html",false),"login.html");
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
  assert.equal(normal.fadeMs,600); assert.equal(normal.velocidadePronta,1);
  assert.ok(normal.minimoMs >= 300);
  assert.ok(frequente.fadeMs < normal.fadeMs); assert.equal(frequente.velocidadePronta,2.2);
  assert.ok(frequente.fadeMs >= 350); assert.ok(frequente.minimoMs >= 150);
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
test("menu dos cards usa dots Lottie e mantém alternativa estática acessível",async () => {
  const html = await readFile(new URL("../pages/builds.html",import.meta.url),"utf8");
  const js = await readFile(new URL("../js/pages/builds-conta.js",import.meta.url),"utf8");
  const ui = await readFile(new URL("../js/components/ui.js",import.meta.url),"utf8");
  const icone = iconeAnimado("dots");
  await access(new URL("../lottie/dots.json",import.meta.url));
  assert.match(ui,/dots:"dots\.json"/);
  assert.match(js,/\$\{iconeAnimado\("dots"\)\}/);
  assert.match(html,/src="\.\.\/js\/pages\/builds-conta\.js"/);
  assert.match(js,/class="build-menu-trigger"[^>]*>\$\{iconeAnimado\("dots"\)\}/);
  assert.match(icone,/aria-hidden="true"/);
  assert.equal([...icone.matchAll(/<circle\b/g)].length,3);
});
test("criar build oferece manual ou formulário, sem dois atalhos divergentes",async () => {
  const html = await readFile(new URL("../pages/builds.html",import.meta.url),"utf8");
  const js = await readFile(new URL("../js/pages/builds-conta.js",import.meta.url),"utf8");
  assert.doesNotMatch(html,/id="btn-create-build-form"/);
  assert.match(js,/Como você quer criar sua build/);
  assert.match(js,/Montagem manual/);
  assert.match(js,/Formulário inteligente/);
  assert.match(js,/criarBuildManual/);
});
test("importar build separa o arquivo das ações e preserva descrição acessível e botão responsivo",async () => {
  const js = await readFile(new URL("../js/pages/builds-conta.js",import.meta.url),"utf8");
  const css = await readFile(new URL("../styles/build/recursos.css",import.meta.url),"utf8");
  assert.match(js,/class="build-import-fields"/);
  assert.match(js,/<label class="planning-field" for="build-import-file">/);
  assert.match(js,/aria-describedby="build-import-help build-import-status"/);
  assert.match(js,/<div class="build-action-actions"><button[^>]*id="build-import-confirm"/);
  assert.match(css,/\.build-import-fields \{[^}]*display: grid;[^}]*gap: 16px/);
  assert.match(css,/\.build-action-actions \{[^}]*margin-top: 22px/);
  assert.match(css,/\.build-action-actions > \*, \.builds-toolbar > \* \{ width: 100%; \}/);
});
test("fechar e voltar compartilham controles visuais sem alterar a tipografia global",async () => {
  const css = await readFile(new URL("../styles/componentes/navigation-controls.css",import.meta.url),"utf8");
  const raiz = await readFile(new URL("../styles/style.css",import.meta.url),"utf8");
  assert.match(css,/\.ui-close-button/);
  assert.match(css,/\.ui-back-button/);
  assert.match(css,/min-height: 44px/);
  assert.match(css,/color: var\(--cor-p1\)/);
  assert.match(raiz,/navigation-controls\.css/);
});
test("ícone do setup atual usa o estado inverso sem afetar os demais", () => {
  assert.match(iconeAnimado("circledot","internal",{invertido:true}),/data-lottie-reversed="true"/);
  assert.doesNotMatch(iconeAnimado("circledot"),/data-lottie-reversed/);
});
test("footers apresentam a BOOSTio pela página Sobre nós, sem links para a equipe removida", async () => {
  const paginas = new URL("../pages/",import.meta.url);
  await access(new URL("sobre.html",paginas));
  for (const nome of (await readdir(paginas)).filter(nome => nome.endsWith(".html"))) {
    const html = await readFile(new URL(nome,paginas),"utf8");
    assert.doesNotMatch(html,/href="[^\"]*desenvolvedores\.html"/,nome);
    if (html.includes('id="about-section"')) assert.match(html,/href="\.\/sobre\.html"/,nome);
  }
});
test("classes de tipografia preservam famílias e tamanhos originais", async () => {
  const css = await readFile(new URL("../styles/utilitarios/tipografia.css",import.meta.url),"utf8");
  for (const [classe,tamanho] of [["font-1-xxl","4rem"],["font-1-xl","3rem"],["font-1-l","1.5rem"],["font-2-s","1.2rem"],["font-2-xs","0.75rem"]]) {
    const bloco = css.match(new RegExp("\\." + classe + "\\s*\\{([^}]+)\\}"))[1];
    assert.ok(bloco.includes("font-size: " + tamanho));
    assert.ok(bloco.includes(classe.startsWith("font-1") ? '"Lexend"' : '"Poppins"'));
  }
});
