import test from "node:test";
import assert from "node:assert/strict";
import { readFile, readdir, access } from "node:fs/promises";
import { iniciarCodigoVerificacao } from "../js/components/verification-code.js";

const paginas = new URL("../pages/",import.meta.url);
const arquivos = (await readdir(paginas)).filter(nome => nome.endsWith(".html")).map(nome => new URL(nome,paginas));
arquivos.push(new URL("../testes.html",import.meta.url));
const ler = url => readFile(url,"utf8");

test("cada página tem título e descrição próprios, idioma e atalho para o conteúdo",async () => {
  const titulos = new Set(), descricoes = new Set();
  for (const url of arquivos) {
    const html = await ler(url), titulo = html.match(/<title>([^<]+)<\/title>/)?.[1];
    const descricao = html.match(/<meta name="description" content="([^"]+)"/)?.[1];
    assert.match(html,/<html lang="pt-BR">/,url.pathname);
    assert.ok(titulo?.includes("BOOSTio"),url.pathname);
    assert.ok(descricao?.length > 30,url.pathname);
    assert.ok(!titulos.has(titulo),titulo); assert.ok(!descricoes.has(descricao),descricao);
    titulos.add(titulo); descricoes.add(descricao);
    const alvo = html.match(/class="skip-link" href="#([^"]+)"/)?.[1];
    assert.ok(alvo,url.pathname);
    const main = html.match(/<main\b[^>]*>/)?.[0] || "";
    assert.ok(main.includes(`id="${alvo}"`) && main.includes('tabindex="-1"'),url.pathname);
  }
});

test("páginas privadas e técnicas não são publicadas nos mecanismos de busca",async () => {
  for (const nome of ["login","signin","esqueci-senha","reset-senha","builds","configuracoes","configuracao-build","configuracoes-prontas","pecas","peca","formulario","erro"])
    assert.match(await ler(new URL(nome+".html",paginas)),/<meta name="robots" content="noindex,/,nome);
  assert.match(await ler(new URL("../testes.html",import.meta.url)),/name="robots" content="noindex,/);
  for (const nome of ["index","sobre","termos"])
    assert.doesNotMatch(await ler(new URL(nome+".html",paginas)),/name="robots" content="noindex/,nome);
});

test("atalho de acessibilidade só fica visível com foco de teclado",async () => {
  const css = await ler(new URL("../styles/utilitarios/acessibilidade.css",import.meta.url));
  assert.match(css,/\.skip-link \{[^}]*transform: translateY\(calc\(-100% - 20px\)\)/s);
  assert.match(css,/\.skip-link:focus-visible \{ transform: none; \}/);
  assert.doesNotMatch(css,/\.skip-link:focus\s*\{/);
});

test("fontes originais são antecipadas sem alterar a família e imagens reservam espaço",async () => {
  for (const url of arquivos) {
    const html = await ler(url);
    for (const fonte of ["Lexend[wght].woff2","Poppins-Regular.woff2"]) {
      const tag = [...html.matchAll(/<link\b[^>]*>/g)].map(m=>m[0]).find(t=>t.includes(fonte));
      assert.ok(tag?.includes('rel="preload"') && tag.includes('as="font"') && tag.includes("crossorigin"),url.pathname);
      await access(new URL(tag.match(/href="([^"]+)"/)[1],url));
    }
    for (const imagem of html.matchAll(/<img\b[^>]*>/g)) {
      assert.match(imagem[0],/\balt="[^"]*"/,url.pathname);
      assert.match(imagem[0],/\bwidth="\d+"/,url.pathname);
      assert.match(imagem[0],/\bheight="\d+"/,url.pathname);
    }
  }
});

test("campos de conta possuem rótulos reais e autocomplete apropriado",async () => {
  for (const nome of ["login","signin","esqueci-senha","reset-senha","configuracoes"]) {
    const html = await ler(new URL(nome+".html",paginas));
    for (const [tag] of html.matchAll(/<input\b[^>]*>/g)) {
      if (/type="(?:checkbox|radio|hidden)"/.test(tag)) continue;
      const id = tag.match(/\bid="([^"]+)"/)?.[1];
      assert.ok(/aria-label="[^"]+"/.test(tag) || (id && html.includes(`for="${id}"`)),nome+": "+tag);
      if (/type="password"/.test(tag)) assert.match(tag,/autocomplete="(?:current-password|new-password)"/);
    }
    if (html.includes('type="password"') && nome !== "configuracoes") assert.match(html,/<form[^>]*method="post"/);
  }
});

test("o conteúdo principal aceita foco e modais/menus fechados saem da navegação",async () => {
  const global = await ler(new URL("../styles/global/global.css",import.meta.url));
  assert.match(global,/main\s*\{\s*display:\s*block/);
  const header = await ler(new URL("../js/header.js",import.meta.url));
  assert.match(header,/atalho\.after\(logo\)/);
  const menus = await ler(new URL("../js/pages/builds-conta.js",import.meta.url));
  assert.match(menus,/role="group"[^>]*aria-hidden="true" inert/);
  assert.match(menus,/role="progressbar" aria-label=/);
  const modais = await ler(new URL("../js/components/modal-accessibility.js",import.meta.url));
  assert.match(modais,/modal\.inert = !aberto/);
  assert.match(modais,/evento\.key === "Escape"/);
  assert.match(modais,/evento\.key === "Tab"/);
});

test("home mantém um único h1, navegação do carrossel por botões e vídeos sob demanda",async () => {
  const html = await ler(new URL("index.html",paginas));
  assert.equal([...html.matchAll(/<h1\b/g)].length,1);
  assert.equal([...html.matchAll(/<button[^>]*class="dot/g)].length,3);
  assert.match(html,/class="video-motion-toggle/);
  const homeCss = await ler(new URL("../styles/home/home.css",import.meta.url));
  assert.match(homeCss,/#main-page\s*\{[^}]*isolation:\s*isolate/s);
  for (const video of ["background","pc"]) {
    assert.match(html,new RegExp(`data-src="../video/${video}.webm"`));
    await access(new URL(`../imgs/${video}-poster.jpg`,import.meta.url));
  }
  const css = await ler(new URL("../styles/componentes/no-script.css",import.meta.url));
  assert.match(css,/#loading-screen\s*\{[^}]*display:\s*none/s);
});

function campos() {
  let foco = -1;
  const inputs = Array.from({length:4},(_,indice) => ({value:"",disabled:false,isConnected:true,handlers:{},
    addEventListener(nome,handler) { this.handlers[nome] = handler; },focus() { foco = indice; }}));
  return {inputs,foco:() => foco};
}
test("código aceita colagem completa sem cancelar o evento nativo",async () => {
  const {inputs,foco} = campos(); let alteracoes = 0, cancelado = false;
  iniciarCodigoVerificacao(inputs,() => alteracoes++);
  inputs[0].handlers.paste({clipboardData:{getData:() => "12 34"},preventDefault:() => { cancelado = true; }});
  await new Promise(resolve => setTimeout(resolve,10));
  assert.equal(cancelado,false);
  assert.equal(inputs.map(i=>i.value).join(""),"1234");
  assert.equal(foco(),3); assert.equal(alteracoes,1);
});
test("código aceita autofill, digitação, retorno e colagem parcial sem preencher campos desativados",async () => {
  const {inputs,foco} = campos(); iniciarCodigoVerificacao(inputs,() => {});
  inputs[0].value = "1234"; inputs[0].handlers.input();
  assert.equal(inputs.map(i=>i.value).join(""),"1234");
  inputs[2].value = ""; inputs[2].handlers.keydown({key:"Backspace"}); assert.equal(foco(),1);
  inputs[2].handlers.paste({clipboardData:{getData:() => "98"}});
  await new Promise(resolve => setTimeout(resolve,10));
  assert.equal(inputs.map(i=>i.value).join(""),"1298");
  inputs[0].disabled = true; inputs[0].handlers.paste({clipboardData:{getData:() => "0000"}});
  await new Promise(resolve => setTimeout(resolve,10)); assert.equal(inputs[0].value,"1");
});
