import test from "node:test";
import assert from "node:assert/strict";
import { dashboardBenchmarkHtml } from "../js/benchmark/dashboard.js";
import { painelBlenderHtml } from "../js/benchmark/blender.js";

test("dashboard abre em FPS e associa cada aba ao painel correto", () => {
  const html = dashboardBenchmarkHtml({prefixo:"teste",titulo:"PC",dispositivos:{cpu:"CPU",gpu:"GPU"}});
  assert.match(html,/<button[^>]*data-benchmark-type="games"[^>]*aria-controls="teste-panel-games"[^>]*aria-selected="true"[^>]*tabindex="0"/);
  assert.match(html,/<button[^>]*data-benchmark-type="blender"[^>]*aria-controls="teste-panel-blender"[^>]*aria-selected="false"[^>]*tabindex="-1"/);
  assert.match(html,/<section[^>]*id="teste-panel-blender"[^>]*hidden>/);
  assert.match(html,/id="teste-fps-game"/);
  assert.match(html,/for="teste-blender-device"/);
});

test("prévia e modal podem coexistir sem IDs duplicados ou nomes de peças interpretados como HTML", () => {
  const entrada = {titulo:'<img src=x onerror="alert(1)">',cpu:'<script>CPU</script>',gpu:"GPU",dispositivos:{cpu:'<img src=x>'}};
  const html = dashboardBenchmarkHtml({...entrada,prefixo:"preview"}) + dashboardBenchmarkHtml({...entrada,prefixo:"oficial"});
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(new Set(ids).size,ids.length);
  assert.doesNotMatch(html,/<img src=x|<script>/);
  assert.match(html,/&lt;img/);
});

test("Blender preserva IDs antigos por padrão e oferece um namespace para cada painel", () => {
  assert.match(painelBlenderHtml({cpu:"CPU"}),/id="blender-form"/);
  const html = painelBlenderHtml({gpu:"GPU"},{prefixo:"oficial-blender"});
  assert.match(html,/id="oficial-blender-form"/);
  assert.match(html,/for="oficial-blender-device"/);
  assert.match(html,/id="oficial-blender-result"/);
});
