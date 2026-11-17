import test from "node:test";
import assert from "node:assert/strict";
import { perguntas } from "../js/build/perguntas-formulario.js";
import { perfisUso } from "../js/build/perfis-uso.js";
import { avaliarOrcamentoGeracao } from "../js/build/orcamento-formulario.js";
import {
  comprimentosCabosCatalogo,
  validarCaboFormulario,
} from "../js/build/cabos-formulario.js";
import { camposRede } from "../js/build/rede.js";
import { orientacaoGeracaoSegura } from "../js/api/_shared/fetchComErro.js";

test("oficial oferece os oito usos aprovados, sem fluxo de notebook", () => {
  assert.equal(perguntas[0].opcoes.length, 8);
  assert.deepEqual(
    perguntas[0].opcoes.map((o) => o[0]),
    Object.keys(perfisUso),
  );
  assert.deepEqual(
    perguntas.map((p) => p.chave),
    ["objetivo", "orcamento", "pecas", "perifericos", "rede", "aparencia"],
  );
  for (const uso of ["jogos", "edicao-video", "modelagem-3d", "programacao"]) {
    assert.equal(avaliarOrcamentoGeracao(3499, 0, uso).valido, false);
    assert.equal(avaliarOrcamentoGeracao(3500, 0, uso).valido, true);
  }
  for (const uso of ["planilhas", "reunioes", "estudos", "todos"]) {
    assert.equal(avaliarOrcamentoGeracao(2499, 0, uso).valido, false);
    assert.equal(avaliarOrcamentoGeracao(2500, 0, uso).valido, true);
  }
  assert.equal(avaliarOrcamentoGeracao(4000, 20, "jogos").valido, false);
  for (const pct of [1, 9, 41, 99])
    assert.equal(avaliarOrcamentoGeracao(10000, pct, "estudos").valido, false);
});
test("cabos do formulário usam somente comprimentos CAT6 realmente à venda", () => {
  const base = {
    categoria: "cabo_rede",
    modelo: "CAT6",
    esgotado: false,
    preco: 30,
  };
  const dados = [
    { ...base, comprimento_m: 5 },
    { ...base, comprimento_m: 10 },
    { ...base, comprimento_m: 5 },
    { ...base, comprimento_m: 2, esgotado: true },
    { ...base, comprimento_m: 3, preco: 0 },
    { ...base, comprimento_m: 20, modelo: "CAT5" },
    { ...base, comprimento_m: null },
  ];
  const metros = comprimentosCabosCatalogo(dados);
  assert.deepEqual(metros, [5, 10]);
  const rede = { tipo: "ambos", possuiAcessorio: false, comprimentoCaboM: 5 };
  assert.equal(validarCaboFormulario(rede, metros), "");
  assert.ok(validarCaboFormulario({ ...rede, comprimentoCaboM: 1.25 }, metros));
  assert.equal(
    validarCaboFormulario({ ...rede, possuiAcessorio: true }, []),
    "",
  );
  const html = camposRede(rede, { comprimentosCabo: metros });
  assert.match(html, /<select[^>]*data-network="comprimentoCaboM"/);
  assert.doesNotMatch(html, /<input[^>]*data-network="comprimentoCaboM"/);
  assert.match(html, /value="5" selected/);
});
test("falha de marca preserva orientação para revisar a preferência sem expor dados extras", () => {
  assert.deepEqual(
    orientacaoGeracaoSegura({
      motivo: "marca-processador",
      etapa: "preferencias",
      titulo: "Revise a marca",
      segredo: "nao",
    }),
    {
      motivo: "marca-processador",
      etapa: "preferencias",
      titulo: "Revise a marca",
    },
  );
});
