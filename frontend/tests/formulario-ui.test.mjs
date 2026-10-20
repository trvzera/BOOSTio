import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { ajustarNumero } from "../js/components/number-stepper.js";

test("controles numéricos ajustam orçamento e porcentagem sem perder centavos", () => {
  assert.equal(ajustarNumero("1234.56",{passo:100}),1334.56);
  assert.equal(ajustarNumero("1234.56",{passo:100,direcao:-1}),1134.56);
  assert.equal(ajustarNumero("20",{passo:1}),21);
  assert.equal(ajustarNumero("0.1",{passo:.2}),.3);
});

test("controles respeitam limites e permitem recuperar campo vazio", () => {
  assert.equal(ajustarNumero("999999.99",{passo:100,maximo:1000000}),1000000);
  assert.equal(ajustarNumero("50",{passo:100,direcao:-1,minimo:.01}),.01);
  assert.equal(ajustarNumero("",{passo:100,minimo:.01}),100);
  assert.equal(ajustarNumero("",{direcao:-1,minimo:1}),1);
  assert.equal(ajustarNumero("99",{maximo:99}),99);
});

test("navegação usa Lotties direcionados e não depende mais do Font Awesome", async () => {
  const forms = await readFile(new URL("../js/pages/forms.js",import.meta.url),"utf8");
  const html = await readFile(new URL("../pages/formulario.html",import.meta.url),"utf8");
  assert.match(forms,/iconeAnimado\("arrow","back"\)/);
  assert.match(forms,/\$\{iconeAnimado\("arrow"\)\}/);
  assert.match(forms,/iniciarIcones\(conteudo\)/);
  assert.doesNotMatch(forms,/fa-solid/);
  assert.doesNotMatch(html,/font-awesome/);
});

test("respostas crescem com conteúdo em vez de ocultar a barra de rolagem", async () => {
  const css = await readFile(new URL("../styles/responsividades/r-forms.css",import.meta.url),"utf8");
  const orcamento = await readFile(new URL("../styles/forms/orcamento.css",import.meta.url),"utf8");
  assert.match(css,/#questions \{ height: auto;/);
  assert.match(css,/\.question-options \{[^}]*max-height: none; overflow: visible;/);
  assert.match(css,/#form-network \{[^}]*overflow: visible;/);
  assert.doesNotMatch(orcamento,/\.budget-fields \{[^}]*overflow-y: auto/);
});

test("erro ocupa o card central e revisar orçamento restaura as perguntas", async () => {
  const forms = await readFile(new URL("../js/pages/forms.js",import.meta.url),"utf8");
  const css = await readFile(new URL("../styles/responsividades/r-forms.css",import.meta.url),"utf8");
  assert.match(forms,/delete document.querySelector\("#questions"\).dataset.formState/);
  assert.match(forms,/dataset.formState = "error"/);
  assert.match(css,/\[data-form-state="error"\] > #question-info \{ display: none;/);
  assert.match(css,/\[data-form-state="error"\] > #question-content \{[^}]*justify-content: center;/);
});
