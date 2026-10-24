import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

test("texto sem classe herda Poppins e títulos continuam Lexend", async()=>{
  const css=await readFile(new URL("../styles/global/global.css",import.meta.url),"utf8");
  assert.match(css,/body\s*\{[^}]*color: var\(--cor-6\);[^}]*font-family: var\(--font-body, "Poppins", sans-serif\)/s);
  assert.match(css,/button, input, textarea, select, optgroup\s*\{[^}]*font: inherit;[^}]*color: inherit/s);
  assert.match(css,/h1, h2, h3, h4, h5, h6\s*\{[^}]*font-family: var\(--font-heading, "Lexend", sans-serif\)/s);
});

test("as duas verificações de e-mail descrevem seis dígitos e têm seis campos",async()=>{
  for(const arquivo of ["signin.html","configuracoes.html"]){
    const html=await readFile(new URL("../pages/"+arquivo,import.meta.url),"utf8");
    assert.match(html,/6 dígitos/);
    assert.doesNotMatch(html,/(?:4|quatro) dígitos/);
    assert.equal((html.match(/class="code-input"/g)||[]).length,6);
  }
  const ui=await readFile(new URL("../js/components/ui.js",import.meta.url),"utf8");
  assert.match(ui,/preencha seus seis dígitos/);
  assert.doesNotMatch(ui,/quatro dígitos/);
});

test("instruções de exclusão e senha recebem tipografia explícita",async()=>{
  const html=await readFile(new URL("../pages/configuracoes.html",import.meta.url),"utf8");
  assert.match(html,/label class="font-1-m" for="delete-current-password"/);
  assert.match(html,/<p class="font-2-xs">Conta somente Google\?/);
});

test("interface descreve desativação, preservação e recuperação assistida sem prometer apagar dados",async()=>{
  const html=await readFile(new URL("../pages/configuracoes.html",import.meta.url),"utf8");
  const js=await readFile(new URL("../js/pages/configuracoes.js",import.meta.url),"utf8");
  assert.match(html,/Desativar minha conta/);
  assert.match(html,/a recuperação deve ser solicitada à equipe/);
  assert.match(html,/Builds públicas podem continuar acessíveis/);
  assert.doesNotMatch(html,/removidos permanentemente|serão apagados|Excluir permanentemente/);
  assert.match(js,/Conta desativada\. Redirecionando/);
});
