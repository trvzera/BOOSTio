import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {linkDaPaginaAtual,marcarPaginaAtual} from "../js/components/navigation-current.js";

test("links da página atual ignoram filtros da origem mas não desativam ações ou seções",()=>{
  const atual="https://boostio.example/pages/builds.html?filtro=teste";
  assert.equal(linkDaPaginaAtual("./builds.html",atual),true);
  for(const destino of ["./builds.html?criar=1","./index.html","./builds.html#conteudo","mailto:contato@boostio.example","https://outro.example/pages/builds.html"])
    assert.equal(linkDaPaginaAtual(destino,atual),false,destino);
  assert.equal(linkDaPaginaAtual("./index.html","https://boostio.example/pages/"),true);
});

test("footer e menus recebem aria-current sem remover href ou foco do teclado",()=>{
  const link=href=>({attrs:{href},getAttribute(k){return this.attrs[k]??null;},setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];}});
  const inicio=link("./index.html"),sobre=link("./sobre.html"),criar=link("./builds.html?criar=1");
  const raiz={querySelectorAll(){return [inicio,sobre,criar];}};
  marcarPaginaAtual(raiz,"https://boostio.example/pages/index.html");
  assert.equal(inicio.attrs["aria-current"],"page");assert.equal(inicio.attrs.href,"./index.html");assert.equal(inicio.attrs.tabindex,undefined);
  assert.equal(sobre.attrs["aria-current"],undefined);assert.equal(criar.attrs["aria-current"],undefined);
  marcarPaginaAtual(raiz,"https://boostio.example/pages/sobre.html");
  assert.equal(inicio.attrs["aria-current"],undefined);assert.equal(sobre.attrs["aria-current"],"page");
});

test("página atual fica azul sem hover/animar o Lottie e footer usa hover no link, não no li",async()=>{
  const [footer,menu,ui]=await Promise.all(["../styles/home/footer.css","../styles/componentes/site-menu.css","../js/components/ui.js"].map(p=>readFile(new URL(p,import.meta.url),"utf8")));
  assert.match(footer,/:not\(\[aria-current="page"\]\):is\(:hover,:focus-visible\)/);
  assert.doesNotMatch(footer,/\.footer-item:hover/);
  assert.match(menu,/\.profile-link\[aria-current="page"\].*color: var\(--cor-p1\)/);
  assert.match(ui,/controle\?\.getAttribute\("aria-current"\) === "page"/);
});
