import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { conteudoApresentacao, passosApresentacao } from "../js/components/onboarding-content.js";

test("apresentação oferece três níveis sem selecionar um por padrão",() => {
  assert.equal(passosApresentacao.length,3);
  const html=conteudoApresentacao(0,null);
  assert.doesNotMatch(html,/value=""|Não tenho preferência| checked/);
  assert.equal((html.match(/type="radio"/g) || []).length,3);
  assert.match(html,/data-lottie="circledot"/);
  assert.match(html,/name="onboarding-level"/);
  assert.match(html,/pule o tutorial/);
});

test("apresentação explica os testes e deixa a informação de conta separada dos cards",() => {
  const html=conteudoApresentacao(1,"iniciante");
  assert.match(html,/class="onboarding-requirements"/);
  assert.match(html,/Testar build/);
  assert.match(html,/jogos e no Blender/);
});

test("prévia reutiliza os mesmos textos e isola os identificadores",() => {
  for(let passo=0;passo<3;passo++) {
    assert.ok(conteudoApresentacao(passo,"iniciante").includes(passosApresentacao[passo][0]));
    assert.ok(conteudoApresentacao(passo,"iniciante",{previa:true}).includes(passosApresentacao[passo][0]));
  }
  const html=conteudoApresentacao(0,"iniciante",{previa:true});
  assert.match(html,/name="tutorial-preview-level" value="iniciante" checked/);
  assert.doesNotMatch(html,/name="onboarding-level"/);
});

test("guia visual foi retirado e prévia não grava preferências",async()=>{
  const js=await readFile(new URL("../js/pages/test-onboarding.js",import.meta.url),"utf8");
  const html=await readFile(new URL("../testes.html",import.meta.url),"utf8");
  assert.doesNotMatch(js,/passosGuiados|test-tour-target|salvarPreferenciasDaConta/);
  assert.doesNotMatch(html,/data-preview-onboarding="guiado"/);
  assert.match(html,/data-preview-onboarding="curto"/);
});
