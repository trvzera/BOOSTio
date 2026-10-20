import test from "node:test";
import assert from "node:assert/strict";
import { pecasPropriasFormulario } from "../js/build/pecas-proprias.js";
import { normalizarBuild } from "../js/build/estado.js";
import { estadoParaConta } from "../js/build/conta.js";

test("converte as peças do formulário para as categorias enviadas ao backend", () => {
  assert.deepEqual(pecasPropriasFormulario({
    pecas:["processador","placa-mae","water-cooler","webcam"],
    pecasDetalhes:{processador:" AMD Ryzen 5 5600G ","placa-mae":"ASUS B550M","water-cooler":"Corsair H100i",webcam:"Logitech C920"},
  }),{
    processador:"AMD Ryzen 5 5600G",placa_mae:"ASUS B550M",
    water_cooler:"Corsair H100i",webcam:"Logitech C920",
  });
  assert.deepEqual(pecasPropriasFormulario({pecas:["nenhuma"]}),{});
});

test("peças adicionais próprias permanecem no JSON de salvamento", () => {
  const build = normalizarBuild({id:"s-1",pecasExtras:{webcam:"Logitech C920"},percentualPerifericos:20,
    componentes:{processador:{proprio:"AMD Ryzen 5 5600G",quantidade:1}}});
  const estado = estadoParaConta(build);
  assert.deepEqual(estado.pecasExtras,{webcam:"Logitech C920"});
  assert.equal(estado.percentualPerifericos,20);
  assert.deepEqual(estado.componentes.processador,{proprio:"AMD Ryzen 5 5600G",quantidade:1});
});
