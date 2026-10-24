import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const js = await readFile(new URL("../js/build/comparacao.js", import.meta.url), "utf8");
const css = await readFile(new URL("../styles/build/comparacao.css", import.meta.url), "utf8");

test("comparativo conta cabeçalho e especificações a cada atualização dos cards", () => {
  const resultados = js.slice(js.indexOf("function mostrarResultados()"), js.indexOf('dialogo.addEventListener("change"'));
  assert.match(resultados, /const colunas = conteudo\.querySelector\("\.compare-columns"\)/);
  assert.match(resultados, /Math\.max\(\.\.\.\[\.\.\.colunas\.querySelectorAll\("\.compare-card"\)\]\.map\(cartao =>\s*1 \+ cartao\.querySelectorAll\("\.compare-field"\)\.length\)\)/);
  assert.match(resultados, /colunas\.style\.setProperty\("--compare-row-count", String\(linhas\)\)/);
  assert.ok(resultados.indexOf('campo("Desempenho em jogos"') < resultados.indexOf("const linhas ="));
});

test("subgrid usa a mesma contagem na grade e no card, mantendo fallback sem subgrid", () => {
  assert.match(css, /\.compare-columns \{ grid-template-rows: repeat\(var\(--compare-row-count, 1\), auto\); \}/);
  assert.match(css, /\.compare-card \{ display: grid; grid-template-rows: subgrid; grid-row: span var\(--compare-row-count, 1\); row-gap: 0; \}/);
  assert.match(css, /\.compare-card \{\s*display: flex;\s*flex-direction: column;/);
  assert.match(css, /\.compare-specs \{ display: grid; margin: 0; \}/);
  assert.match(css, /@supports \(grid-template-rows: subgrid\)/);
  assert.doesNotMatch(css, /grid-template-rows: repeat\(\d+, auto\)|grid-row: span \d+/);
});
