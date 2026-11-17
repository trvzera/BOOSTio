import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  perguntasPc,
  perguntasNotebook,
  novasRespostasPreview,
  validarEtapaPreview,
  resumoFormularioPreview,
  percentualPreview,
} from "../js/experimentos/formularios.js";
import {
  perfisUso,
  minimoUso,
  orcamentoInicialUso,
  memoriaSugerida,
} from "../js/experimentos/formularios/objetivos.js";
import { comprimentosDisponiveis } from "../js/experimentos/formularios/catalogo.js";
import { motivoMarcaNotebook } from "../js/experimentos/formularios/preferencias.js";
import { webcamSolicitada } from "../js/experimentos/formularios/perifericos.js";
import {
  avaliarOrcamentoPreview,
  montarPlanoPreview,
  validarResultadoGeracao,
  gerarComPreferenciasFlexiveis,
  ErroGeracaoFormulario,
  identificarErroFormulario,
} from "../js/experimentos/formularios/regras.js";
import {
  camposHtml,
  revisaoHtml,
} from "../js/experimentos/formularios/campos.js";
const catalogo = JSON.parse(
  readFileSync(
    new URL("../data/previa-formularios-catalogo.json", import.meta.url),
  ),
);
const pc = (k) => perguntasPc.find((p) => p.chave === k);
const valido = (tipo = "pc", extras = {}) => ({
  ...novasRespostasPreview(tipo),
  objetivo: "jogos",
  orcamento: 5000,
  modoReserva: "percentual",
  pecas: ["nenhuma"],
  perifericos: "sem-perifericos",
  prioridade_montagem: "custo_beneficio",
  ...extras,
});
const resultado = (extras) => ({
  processador: { fabricante: "AMD" },
  placaVideo: { modelo: "GPU de teste" },
  precoComputador: 4000,
  precoPerifericos: 0,
  errosCompatibilidade: [],
  pecasObrigatoriasAusentes: [],
  ...extras,
});

test("oito usos com prioridades distintas; orçamento inicial respeita o mínimo do perfil", () => {
  assert.deepEqual(Object.keys(perfisUso), [
    "jogos",
    "planilhas",
    "reunioes",
    "edicao-video",
    "modelagem-3d",
    "programacao",
    "estudos",
    "todos",
  ]);
  for (const u of ["jogos", "edicao-video", "modelagem-3d", "programacao"])
    assert.equal(minimoUso(u), 3500);
  for (const u of ["planilhas", "reunioes", "estudos", "todos"])
    assert.equal(minimoUso(u), 2500);
  assert.equal(novasRespostasPreview("pc").orcamento, 3000);
  assert.equal(novasRespostasPreview("notebook").orcamento, 3000);
  assert.equal(
    new Set(Object.values(perfisUso).map((p) => p.prioridade)).size,
    8,
  );
});
test("rascunhos e resumos são independentes; não geram recomendações reais", () => {
  const a = novasRespostasPreview("pc"),
    b = novasRespostasPreview("pc");
  a.pecas.push("ssd");
  assert.deepEqual(b.pecas, []);
  const r = resumoFormularioPreview("pc", a);
  r.pecas.push("hd");
  assert.deepEqual(a.pecas, ["ssd"]);
  assert.equal(r.geracaoDisponivel, false);
});
test("mínimo do computador é calculado depois da reserva e sobra não retorna ao PC", () => {
  let r = valido("pc", {
    orcamento: 4000,
    perifericos: "todos-perifericos",
    percentualPerifericos: 20,
  });
  assert.equal(avaliarOrcamentoPreview("pc", r).valido, false);
  r.orcamento = 5000;
  const d = avaliarOrcamentoPreview("pc", r);
  assert.equal(d.valido, true);
  assert.equal(d.pc, 4000);
  assert.equal(d.perifericos, 1000);
  assert.match(
    validarEtapaPreview("pc", pc("perifericos"), {
      ...r,
      orcamento: 4000,
      percentualPerifericos: 10,
    }),
    /500/,
  );
  assert.match(
    validarEtapaPreview("pc", pc("perifericos"), {
      ...r,
      percentualPerifericos: NaN,
    }),
    /porcentagem/,
  );
  const plano = montarPlanoPreview("pc", r);
  assert.equal(plano.devolverSobraPerifericosAoPc, false);
  assert.throws(
    () =>
      validarResultadoGeracao(
        plano,
        resultado({ precoComputador: 4500, precoPerifericos: 100 }),
      ),
    (e) => e.etapa === "orcamento",
  );
});
test("cabos só aceitam comprimentos CAT6 com disponibilidade na amostra", () => {
  assert.deepEqual(comprimentosDisponiveis(catalogo), [1, 5, 10]);
  for (const metros of [0, 1.2, 2, 3, 20, 999])
    assert.ok(
      validarEtapaPreview(
        "pc",
        pc("rede"),
        valido("pc", {
          rede: {
            tipo: "ambos",
            possuiAcessorio: false,
            comprimentoCaboM: metros,
          },
        }),
        catalogo,
      ),
    );
  for (const metros of [1, 5, 10])
    assert.equal(
      validarEtapaPreview(
        "pc",
        pc("rede"),
        valido("pc", {
          rede: {
            tipo: "ambos",
            possuiAcessorio: false,
            comprimentoCaboM: metros,
          },
        }),
        catalogo,
      ),
      "",
    );
  assert.ok(
    validarEtapaPreview(
      "pc",
      pc("rede"),
      valido("pc", { rede: { tipo: "cabo", possuiAcessorio: false } }),
    ),
  );
});
test("marca da CPU é obrigatória quando escolhida; preferência estética divergente só avisa", () => {
  const plano = montarPlanoPreview(
    "pc",
    valido("pc", {
      preferencia_processador: "amd",
      aparencia: { cor: "branco", porte: "full-tower", estilo: "panoramico" },
    }),
  );
  assert.equal(plano.criterios.fabricanteCpuObrigatorio, "amd");
  assert.throws(
    () =>
      validarResultadoGeracao(
        plano,
        resultado({ processador: { fabricante: "Intel" } }),
      ),
    (e) => e.codigo === "marca-processador" && e.etapa === "revisao",
  );
  assert.throws(
    () => validarResultadoGeracao(plano, resultado({ placaVideo: null })),
    (e) => e.codigo === "placa-video" && e.etapa === "objetivo",
  );
  const r = validarResultadoGeracao(
    plano,
    resultado({
      aparencia: { cor: "preto", porte: "mid-tower", estilo: "vidro" },
    }),
  );
  assert.equal(r.valido, true);
  assert.equal(r.avisos.length, 1);
});
test("aparência pode ser flexibilizada uma vez sem mudar marca, limite ou peças obrigatórias", async () => {
  const plano = montarPlanoPreview(
      "pc",
      valido("pc", {
        preferencia_processador: "amd",
        aparencia: { cor: "branco" },
      }),
    ),
    chamadas = [];
  const r = await gerarComPreferenciasFlexiveis(plano, async (p) => {
    chamadas.push(p);
    if (chamadas.length === 1)
      throw new ErroGeracaoFormulario("aparencia", "aparencia", "Sem a cor");
    return resultado();
  });
  assert.equal(chamadas.length, 2);
  assert.equal(chamadas[1].aparencia.cor, "sem-preferencia");
  assert.equal(chamadas[1].limiteComputador, 5000);
  assert.equal(chamadas[1].criterios.fabricanteCpuObrigatorio, "amd");
  assert.ok(r.avisos.length);
  assert.equal(plano.aparencia.cor, "branco");
  await assert.rejects(
    gerarComPreferenciasFlexiveis(plano, async () => {
      throw new ErroGeracaoFormulario("orcamento", "orcamento", "Sem verba");
    }),
    /Sem verba/,
  );
  await assert.rejects(
    gerarComPreferenciasFlexiveis(plano, async () =>
      resultado({ pecasObrigatoriasAusentes: ["placa_video"] }),
    ),
    (e) => e.etapa === "pecas",
  );
  assert.throws(
    () =>
      validarResultadoGeracao(plano, {
        precoComputador: 3000,
        precoPerifericos: 0,
      }),
    (e) => e.codigo === "resposta-invalida",
  );
});
test("Apple depende do uso e do valor reservado ao notebook, não do orçamento total", () => {
  assert.ok(
    motivoMarcaNotebook(
      "apple",
      { objetivo: "jogos", orcamento: 20000 },
      20000,
    ),
  );
  assert.ok(
    motivoMarcaNotebook(
      "apple",
      { objetivo: "estudos", orcamento: 7000 },
      5600,
    ),
  );
  assert.equal(
    motivoMarcaNotebook(
      "apple",
      { objetivo: "estudos", orcamento: 6000 },
      6000,
    ),
    "",
  );
  assert.equal(motivoMarcaNotebook("lenovo", { objetivo: "jogos" }, 5000), "");
});
test("notebook não pergunta RAM nem sistema; memória deriva do uso e dos recursos disponíveis", () => {
  const r = valido("notebook", { objetivo: "programacao", orcamento: 7000 });
  const plano = montarPlanoPreview("notebook", r);
  assert.equal(plano.criterios.memoriaSugeridaGb, 32);
  assert.equal(
    montarPlanoPreview("notebook", { ...r, orcamento: 4000 }).criterios
      .memoriaSugeridaGb,
    16,
  );
  assert.deepEqual(
    perguntasNotebook.map((p) => p.chave),
    ["objetivo", "orcamento", "tela", "perifericos"],
  );
  const html = perguntasNotebook
    .map((p) =>
      camposHtml(p, {
        respostas: r,
        tipo: "notebook",
        id: (k) => "n-" + k,
        catalogo,
      }),
    )
    .join("");
  assert.doesNotMatch(
    html,
    /data-(?:select|answer)="(?:memoria|sistema|armazenamento|bateria|mobilidade)"/,
  );
  assert.equal(plano.criterios.armazenamentoSugeridoGb, 1024);
  assert.equal(
    montarPlanoPreview("notebook", { ...r, orcamento: 4000 }).criterios
      .armazenamentoSugeridoGb,
    512,
  );
  assert.match(
    revisaoHtml({
      respostas: r,
      tipo: "notebook",
      id: (k) => "n-" + k,
      catalogo,
    }),
    /Apple/,
  );
  assert.ok(perguntasNotebook.some((p) => p.chave === "perifericos"));
});
test("extras de notebook são opcionais, independentes dos periféricos do desktop", () => {
  const r = valido("notebook", {
    perifericos: "escolher-extras",
    extrasNotebook: ["mouse"],
    percentualPerifericos: 10,
  });
  assert.equal(percentualPreview(r, "notebook"), 10);
  assert.deepEqual(montarPlanoPreview("notebook", r).acessorios, ["mouse"]);
  const q = perguntasNotebook.find((p) => p.chave === "perifericos");
  assert.ok(validarEtapaPreview("notebook", q, { ...r, extrasNotebook: [] }));
  assert.equal(
    montarPlanoPreview("notebook", { ...r, perifericos: "sem-perifericos" })
      .tetoPerifericos,
    0,
  );
});
test("webcam é respeitada como escolha opcional; não inventa disponibilidade no catálogo", () => {
  const r = valido("pc", {
    objetivo: "reunioes",
    incluirWebcam: true,
    perifericos: "todos-perifericos",
  });
  assert.equal(webcamSolicitada("pc", r), true);
  assert.ok(montarPlanoPreview("pc", r).acessorios.includes("webcam"));
  assert.equal(
    montarPlanoPreview("pc", r).webcam.cadastroCompraDisponivel,
    false,
  );
  assert.equal(
    webcamSolicitada("pc", { ...r, perifericos: "sem-perifericos" }),
    false,
  );
});
test("falhas identificam a pergunta; falha genérica não atribui causa inventada", () => {
  const e = identificarErroFormulario({
    codigo: "rede",
    message: "Sem cabo válido",
  });
  assert.equal(e.etapa, "rede");
  assert.equal(
    identificarErroFormulario(new Error("timeout")).codigo,
    "servico",
  );
  assert.match(
    identificarErroFormulario(new Error("timeout")).message,
    /não informou qual resposta/,
  );
});

test("reserva é sempre porcentagem do total, sem modo em reais", () => {
  const r = {
    ...novasRespostasPreview("pc"),
    objetivo: "estudos",
    perifericos: "todos-perifericos",
    prioridade_montagem: "custo_beneficio",
  };
  assert.equal(percentualPreview(r, "pc"), 20);
  assert.equal(avaliarOrcamentoPreview("pc", r).valido, false);
  const d = avaliarOrcamentoPreview("pc", { ...r, orcamento: 3125 });
  assert.equal(d.valido, true);
  assert.equal(d.pc, 2500);
  assert.equal(d.perifericos, 625);
  assert.equal(d.minimoTotal, 3125);
  for (const percentual of [NaN, Infinity, -1, 0, 100, 16.67])
    assert.equal(
      avaliarOrcamentoPreview("pc", {
        ...r,
        orcamento: 5000,
        percentualPerifericos: percentual,
      }).valido,
      false,
    );
  const legado = avaliarOrcamentoPreview("pc", {
    ...r,
    orcamento: 5000,
    modoReserva: "valor",
    reservaPerifericosReais: 500,
  });
  assert.equal(legado.perifericos, 1000);
  const html = camposHtml(pc("perifericos"), {
    tipo: "pc",
    respostas: r,
    id: (k) => "r-" + k,
    catalogo,
  });
  assert.match(html, /data-number="percentualPerifericos"/);
  assert.doesNotMatch(
    html,
    /data-(?:select|number)="(?:modoReserva|reservaPerifericosReais)"/,
  );
  assert.equal(
    montarPlanoPreview("pc", { ...r, orcamento: 3125 })
      .devolverSobraPerifericosAoPc,
    false,
  );
});
test("mínimos não criam atalhos extras de orçamento por objetivo", () => {
  for (const objetivo of Object.keys(perfisUso)) {
    const html = camposHtml(pc("orcamento"), {
      tipo: "pc",
      respostas: valido("pc", { objetivo }),
      id: (k) => k,
      catalogo,
    });
    const valores = [...html.matchAll(/data-budget="(\d+)"/g)].map((m) =>
      Number(m[1]),
    );
    assert.deepEqual(
      valores,
      minimoUso(objetivo) > 3000 ? [5000, 8000] : [3000, 5000, 8000],
    );
  }
  assert.equal(orcamentoInicialUso("reunioes"), 3000);
});
test("tela de notebook é preferência flexível; orçamento continua obrigatório", () => {
  const plano = montarPlanoPreview(
    "notebook",
    valido("notebook", { objetivo: "edicao-video", tela: "grande" }),
  );
  assert.equal(plano.criterios.telaFlexivel, true);
  assert.equal(plano.telaPreferida, "grande");
  const adaptado = validarResultadoGeracao(
    plano,
    resultado({ tela: "equilibrada" }),
  );
  assert.equal(adaptado.valido, true);
  assert.match(adaptado.avisos.join(" "), /tela foi adaptado/);
  assert.throws(
    () =>
      validarResultadoGeracao(
        plano,
        resultado({ tela: "grande", precoComputador: 5001 }),
      ),
    (e) => e.codigo === "orcamento",
  );
});
test("edição de vídeos e imagens é uma opção única e prioriza 32 GB de RAM", () => {
  assert.equal(perfisUso["edicao-video"].titulo, "Edição de vídeos e imagens");
  assert.equal(perfisUso["edicao-imagens"], undefined);
  for (const orcamento of [3500, 5000, 7000]) {
    assert.equal(memoriaSugerida("edicao-video", orcamento), 32);
    const plano = montarPlanoPreview(
      "pc",
      valido("pc", { objetivo: "edicao-video", orcamento }),
    );
    assert.equal(plano.criterios.memoriaSugeridaGb, 32);
  }
  for (const uso of ["edicao-video", "modelagem-3d"]) {
    const plano = montarPlanoPreview("pc", valido("pc", { objetivo: uso }));
    assert.throws(
      () => validarResultadoGeracao(plano, resultado({ placaVideo: null })),
      (e) => e.codigo === "placa-video",
    );
  }
});

test("periféricos aceitam apenas 10% a 40%, inclusive nos planos de geração", () => {
  for (const tipo of ["pc", "notebook"]) {
    const r = valido(tipo, {
      orcamento: 10000,
      perifericos: tipo === "pc" ? "todos-perifericos" : "escolher-extras",
      extrasNotebook: ["mouse"],
    });
    for (const percentualPerifericos of [10, 20, 40]) {
      const dados = { ...r, percentualPerifericos };
      assert.equal(avaliarOrcamentoPreview(tipo, dados).valido, true);
      assert.equal(
        montarPlanoPreview(tipo, dados).tetoPerifericos,
        (10000 * percentualPerifericos) / 100,
      );
    }
    for (const percentualPerifericos of [
      0,
      1,
      9,
      9.5,
      40.5,
      41,
      99,
      NaN,
      Infinity,
    ]) {
      const dados = { ...r, percentualPerifericos };
      assert.match(avaliarOrcamentoPreview(tipo, dados).mensagem, /10% e 40%/);
      assert.throws(
        () => montarPlanoPreview(tipo, dados),
        (e) => e.codigo === "orcamento",
      );
    }
    const q = (tipo === "pc" ? perguntasPc : perguntasNotebook).find(
      (p) => p.chave === "perifericos",
    );
    const html = camposHtml(q, { tipo, respostas: r, id: (k) => k, catalogo });
    assert.match(html, /min="10" max="40"/);
    assert.equal(
      avaliarOrcamentoPreview(tipo, {
        ...r,
        perifericos: "sem-perifericos",
        percentualPerifericos: 99,
      }).perifericos,
      0,
    );
  }
});
