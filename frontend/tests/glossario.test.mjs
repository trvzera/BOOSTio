import test from "node:test";
import assert from "node:assert/strict";
import { termosNoTexto, glossarioHtml } from "../js/build/glossario.js";

test("glossário identifica unidades com e sem espaço e não confunde RGB",()=>{
  assert.deepEqual(termosNoTexto("16GB DDR4 · 3200MHz · 1 TB"),["GB","TB","MHz","DDR"]);
  assert.deepEqual(termosNoTexto("RGB — Modelo completo"),[]);
  assert.deepEqual(termosNoTexto("M.2 NVMe · 650W · 120 mm · 144 Hz"),["Hz","W","mm","NVMe","M.2"]);
  assert.deepEqual(termosNoTexto("2 slots, socket AM4"),["socket","slot"]);
});
test("glossário explica termos reais sem repetir a função da categoria ou aceitar HTML",()=>{
  const html=glossarioHtml(["GB","GB","MHz","<script>","__proto__"]);
  assert.match(html,/Gigabyte/);assert.match(html,/Megahertz/);
  assert.doesNotMatch(html,/<script>|__proto__|Para que serve/);
  assert.equal((html.match(/<dt>/g)||[]).length,2);
  assert.equal(glossarioHtml([]),"");
});
