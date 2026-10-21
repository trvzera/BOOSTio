import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const ler = arquivo => readFile(new URL("../" + arquivo,import.meta.url),"utf8");
const [js,css,responsivo,editor,editorCss,imports] = await Promise.all([
  ler("js/build/melhorias.js"),ler("styles/build/melhorias.css"),
  ler("styles/responsividades/r-melhorias.css"),ler("js/pages/configuracao-build.js"),
  ler("styles/responsividades/r-editor-build.css"),ler("styles/style.css"),
]);

test("melhorias oferece abas identificadas e navegação por teclado no layout compacto",() => {
  assert.match(js,/role="tablist" aria-label="Etapas da busca de melhorias"/);
  for (const [aba,painel] of [["search","upgrade-search"],["preview","upgrade-preview"]]) {
    assert.ok(js.includes('role="tab" aria-selected="' + (aba === "search") + '" aria-controls="' + painel + '" data-upgrade-tab="' + aba + '"'));
    assert.ok(js.includes('id="' + painel + '"'));
  }
  assert.match(js,/\['ArrowLeft','ArrowRight','Home','End'\]/);
  assert.match(js,/controle\.tabIndex = ativa \? 0 : -1/);
  assert.match(js,/painel\.hidden = compacta\.matches && !ativa/);
  assert.match(js,/painel\.setAttribute\("role","tabpanel"\)/);
  assert.match(css,/\.upgrade-dialog \[hidden\] \{ display: none !important; \}/);
});

test("sugestões mostram imagem, preço e seleção sem prometer ganho de desempenho",() => {
  assert.match(js,/imagemPeca\(peca\)/);
  assert.match(js,/class="upgrade-real-candidate" data-upgrade-pick=/);
  assert.match(js,/aria-pressed="' \+ selecionada/);
  assert.match(js,/class="upgrade-real-candidate-price"/);
  assert.match(js,/ordenadas por preço, não por ganho de desempenho medido/);
  assert.doesNotMatch(js,/id="upgrade-real-order"/);
  assert.match(css,/\.upgrade-real-candidate-image img \{[^}]*object-fit: contain/);
});

test("prévia considera todas as peças antigas e distingue dicas, avisos e erros",() => {
  assert.match(js,/itens\.map\(item =>/);
  assert.match(js,/item\.quantidade > 1 \? item\.quantidade \+ " × "/);
  assert.match(js,/precosAntigos\.reduce\(/);
  assert.match(js,/verificacoes\("Conflitos encontrados",depois\.erros,"error"\)/);
  assert.match(js,/verificacoes\("Pontos de atenção",avisos,"warning"\)/);
  assert.match(js,/verificacoes\("Dicas e conferências",depois\.dicas,"info"\)/);
  assert.match(js,/gasto > limite/);
  assert.match(js,/await aoAplicar\(confirmada\.build\)/);
});

test("modal mantém áreas de rolagem próprias e adaptação para paisagem, teclado e texto grande",() => {
  assert.match(css,/\.upgrade-real-scroll \{[^}]*min-height: 0;[^}]*overflow-y: auto;/);
  assert.match(css,/\.upgrade-real-workspace \{[^}]*minmax\(0,1\.45fr\) minmax\(17rem,\.9fr\)/);
  assert.match(responsivo,/@media \(max-width: 900px\)/);
  assert.match(responsivo,/env\(safe-area-inset-bottom\)/);
  assert.match(responsivo,/@media \(max-height: 500px\)/);
  assert.match(responsivo,/\.upgrade-dialog\.upgrade-dialog-flow\[open\] \{[^}]*overflow-y: auto/);
  assert.match(responsivo,/\.upgrade-dialog-flow \.upgrade-real-tabs \{[^}]*flex-direction: column/);
  assert.ok(imports.indexOf('"./responsividades/r-melhorias.css"') > imports.indexOf('"./build/melhorias.css"'));
});

test("viewport móvel é acompanhado sem transição de posição e observadores são removidos",() => {
  assert.match(css,/\.upgrade-dialog\[open\] \{[^}]*transition: none;/);
  assert.match(js,/window\.visualViewport\?\.addEventListener\("resize",programarViewport\)/);
  assert.match(js,/window\.visualViewport\?\.addEventListener\("scroll",programarViewport\)/);
  assert.match(js,/observarViewport\?\.disconnect\(\); cancelAnimationFrame\(frameViewport\)/);
  assert.match(js,/compacta\.removeEventListener\("change",ajustarCompacta\)/);
  for (const evento of ["resize","scroll"]) assert.ok(js.includes('window.visualViewport?.removeEventListener("' + evento + '",programarViewport)'));
  assert.match(responsivo,/@media \(prefers-reduced-motion: reduce\)/);
});

test("rerender mantém foco na área visível e aplicação pendente não é descartada",() => {
  const capturar = js.indexOf("const focoNaPrevia = previa.contains(foco)");
  assert.ok(capturar > 0 && capturar < js.indexOf("renderizarResultados();",capturar));
  assert.match(js,/focoNaPrevia \? dialogo\.querySelector\("\.upgrade-real-preview-scroll"\)/);
  assert.match(js,/if \(!aplicando\) dialogo\.close\("cancelar"\)/);
  assert.match(js,/if \(aplicando && evento\.target === dialogo\) evento\.stopImmediatePropagation\(\)/);
  assert.match(js,/controle\.disabled = aplicando/);
  assert.match(js,/role="status" aria-live="polite" aria-atomic="true"/);
});

test("editor aguarda confirmação do salvamento e mantém base original para tentar novamente",() => {
  assert.match(editor,/abrirMelhorias\(build,catalogo,async proxima => \{\s*const anterior = build;/);
  assert.match(editor,/await filaSalvamento;\s*if \(falhaSalvamento\) \{ build = anterior; throw falhaSalvamento; \}/);
  assert.match(editor,/janela\.returnValue === "aplicar"\) main\.querySelector\("#improve-configuration"\)\?\.focus/);
});

test("aplicar melhorias pelo menu devolve o foco ao novo card depois da atualização",async () => {
  const lista = await ler("js/pages/builds-conta.js");
  assert.match(lista,/await atualizar\(build\.id,estadoParaConta\(proxima\)\)/);
  assert.match(lista,/janela\.returnValue !== "aplicar"\) return;/);
  assert.match(lista,/find\(card => card\.dataset\.id === build\.id\)\?\.querySelector\("\.build-menu-trigger"\)\?\.focus/);
  assert.match(lista,/lista\.innerHTML = salvas\.map\(card\)\.join\(""\);\s*\/\/[^\n]+\n\s*lista\.querySelectorAll\("\.build-menu"\)\.forEach/);
});

test("resumo sticky permite alcançar melhorias mesmo quando é maior que a tela",() => {
  assert.match(editorCss,/top: min\(88px,calc\(100dvh - var\(--summary-height,0px\) - 16px\)\)/);
  assert.match(editor,/new ResizeObserver\(entradas =>/);
  assert.match(editor,/function renderizar\(\) \{\s*observarResumo\?\.disconnect\(\)/);
  assert.match(editor,/observarResumo\?\.observe\(main\.querySelector\("\.build-sidebar"\)\)/);
  assert.match(editor,/"pagehide",\(\) => observarResumo\?\.disconnect\(\)/);
  assert.match(editor,/evento\.persisted && resumo\) observarResumo\?\.observe\(resumo\)/);
});
