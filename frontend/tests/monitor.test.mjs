import test from "node:test";
import assert from "node:assert/strict";
import { resumoMonitor } from "../js/build/monitor.js";

test("resumo do monitor mostra Hz e resolução cadastrados", () => {
  assert.equal(resumoMonitor({taxa_atualizacao_hz:144,resolucao:"1920x1080"}),"144 Hz · 1920 × 1080");
  assert.equal(resumoMonitor({taxa_atualizacao_hz:165,resolucao:"2560 × 1440"}),"165 Hz · 2560 × 1440");
});
test("resumo não inventa Hz ou resolução quando faltam dados", () => {
  assert.equal(resumoMonitor({}),"Hz não informados · Resolução não informada");
  assert.equal(resumoMonitor({taxa_atualizacao_hz:0,resolucao:"Full HD"}),"Hz não informados · Full HD");
  assert.equal(resumoMonitor(null),"");
});
