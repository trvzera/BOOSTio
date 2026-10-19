import test from "node:test";
import assert from "node:assert/strict";
import { definirDetalheAberto,iniciarDetalhesAnimados } from "../js/components/animated-details.js";

class Summary extends EventTarget {
  atributos = new Map();
  setAttribute(nome,valor) { this.atributos.set(nome,valor); }
  getBoundingClientRect() { return {height:42}; }
  clicar() { this.dispatchEvent(new Event("click",{cancelable:true})); }
}
class Details extends EventTarget {
  dataset = {};
  open = false;
  summary = new Summary();
  animacoes = [];
  querySelector() { return this.summary; }
  getBoundingClientRect() { return {height:this.open ? 200 : 48}; }
  animate(frames,opcoes) {
    const animacao = {frames,opcoes,cancelada:false,cancel() { this.cancelada = true; }};
    this.animacoes.push(animacao);
    return animacao;
  }
}
function ambiente(rodar,{reduzido = false} = {}) {
  const media = globalThis.matchMedia, estilo = globalThis.getComputedStyle;
  globalThis.matchMedia = () => ({matches:reduzido});
  globalThis.getComputedStyle = () => ({paddingTop:"2px",paddingBottom:"2px",borderTopWidth:"1px",borderBottomWidth:"1px",getPropertyValue:nome => nome === "--details-duration" ? "320" : ""});
  try { rodar(); } finally {
    if (media === undefined) delete globalThis.matchMedia; else globalThis.matchMedia = media;
    if (estilo === undefined) delete globalThis.getComputedStyle; else globalThis.getComputedStyle = estilo;
  }
}
test("details anima alturas naturais, atualiza ARIA e não duplica listeners",() => ambiente(() => {
  const details = new Details(), raiz = {querySelectorAll:() => [details]};
  iniciarDetalhesAnimados(raiz); iniciarDetalhesAnimados(raiz);
  details.summary.clicar();
  assert.equal(details.animacoes.length,1);
  assert.deepEqual(details.animacoes[0].frames,{height:["48px","200px"]});
  assert.equal(details.animacoes[0].opcoes.duration,320);
  assert.equal(details.summary.atributos.get("aria-expanded"),"true");
  details.animacoes[0].onfinish();
  assert.equal(details.open,true);
  assert.equal(details.dataset.animating,undefined);
  details.summary.clicar();
  assert.deepEqual(details.animacoes[1].frames,{height:["200px","48px"]});
  assert.equal(details.summary.atributos.get("aria-expanded"),"false");
  details.animacoes[1].onfinish();
  assert.equal(details.open,false);
}));
test("cliques rápidos cancelam a animação anterior sem reabrir o menu",() => ambiente(() => {
  const details = new Details();
  definirDetalheAberto(details,true);
  const antiga = details.animacoes[0];
  details.summary.clicar();
  assert.equal(antiga.cancelada,true);
  antiga.onfinish();
  details.animacoes[1].onfinish();
  assert.equal(details.open,false);
  assert.equal(details.summary.atributos.get("aria-expanded"),"false");
}));
test("fechamento por código interrompe animações e permite abrir novamente",() => ambiente(() => {
  const details = new Details();
  definirDetalheAberto(details,true);
  const antiga = details.animacoes[0];
  definirDetalheAberto(details,false,{animar:false});
  antiga.onfinish();
  assert.equal(details.open,false);
  assert.equal(details.dataset.animating,undefined);
  details.summary.clicar();
  details.animacoes[1].onfinish();
  assert.equal(details.open,true);
}));
test("details respeita movimento reduzido e funciona sem Web Animations",() => {
  ambiente(() => {
    const details = new Details();
    definirDetalheAberto(details,true);
    assert.equal(details.open,true);
    assert.equal(details.animacoes.length,0);
    details.summary.clicar();
    assert.equal(details.open,false);
  },{reduzido:true});
  ambiente(() => {
    const details = new Details(); details.animate = undefined;
    definirDetalheAberto(details,true);
    assert.equal(details.open,true);
    assert.equal(details.summary.atributos.get("aria-expanded"),"true");
  });
});
