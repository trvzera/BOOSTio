import test from "node:test";
import assert from "node:assert/strict";
import {mensagemFalhaBlender} from "../js/benchmark/blender.js";

test("erro identifica status da BOOSTio e da fonte sem confundir falta de dados com conexão",() => {
  assert.equal(mensagemFalhaBlender({message:"Sem resultados para essa peça.",status:422,codigo:"sem-dados"}),"Sem resultados para essa peça. Referência: HTTP 422 da BOOSTio · sem-dados.");
  const mensagem = mensagemFalhaBlender({message:"Consulta recusada.",status:503,codigo:"acesso-provedor",diagnostico:{httpProvedor:403}});
  assert.match(mensagem,/HTTP 503 da BOOSTio/); assert.match(mensagem,/Blender: HTTP 403/);
  assert.equal(mensagemFalhaBlender(new Error("Sem conexão.")),"Sem conexão.");
});
