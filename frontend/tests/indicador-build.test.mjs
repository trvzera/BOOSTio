import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { indicadorBuild } from "../js/build/indicador.js";

test("barrinha preserva botão acessível e estados de compatibilidade, sem texto visual de i",()=>{
  for(const [estado,esperado] of [[{},"ok"],[{faltam:["RAM"]},"aviso"],[{erros:["Socket incompatível"]},"erro"],
    [{compatibilidade:{naoVerificado:[{mensagem:"Confirme no manual"}]}},"aviso"]]){
    const html=indicadorBuild({erros:[],avisos:[],faltam:[],...estado},"painel");
    assert.match(html,new RegExp('build-indicator '+esperado+'"'));
    assert.match(html,/<button type="button" class="compatibility-trigger" aria-label="[^"]+" aria-controls="painel" aria-expanded="false"><\/button>/);
    assert.match(html,/id="painel".*aria-hidden="true" inert/);
    assert.doesNotMatch(html,/build-info-icon|>i</);
  }
});

test("indicador vem antes do nome no editor, nos cards e na build pública",async()=>{
  const [editor,cards,publica]=await Promise.all(["../js/pages/configuracao-build.js","../js/pages/builds-conta.js","../js/build/publica.js"].map(p=>readFile(new URL(p,import.meta.url),"utf8")));
  assert.match(editor,/indicadorBuild\(resultado,"compatibility-details"\) \+ '<h1 id="builder-title">/);
  assert.match(cards,/class="build-title-line">\$\{indicadorBuild\([^\n]+?<h2/);
  assert.match(publica,/class="builder-title-line">' \+ indicadorBuild\(avaliacao,'public-compatibility'\) \+ '<h1>/);
});

test("barrinha mantém alvo de interação e cores primária, aviso e erro sem estilos antigos de informação",async()=>{
  const css=await readFile(new URL("../styles/build/editor.css",import.meta.url),"utf8");
  assert.match(css,/\.build-indicator \{ --indicator-color: var\(--cor-p1\)/);
  assert.match(css,/\.build-indicator\.aviso \{ --indicator-color: var\(--status-warning\)/);
  assert.match(css,/\.build-indicator\.erro \{ --indicator-color: var\(--status-error\)/);
  assert.match(css,/\.compatibility-trigger, \.compatibility-marker \{[^}]*width: 1\.5rem; min-height: 2\.75rem/);
  assert.match(css,/\.compatibility-trigger:focus-visible \{ outline:/);
  assert.doesNotMatch(css,/\.build-info-icon|\.build-indicator\.information/);
});
