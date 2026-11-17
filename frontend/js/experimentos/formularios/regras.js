import {
  orcamentoValido,
  dividirOrcamento,
} from "../../build/orcamento-formulario.js";
import { normalizarAparencia } from "../../build/aparencia.js";
import { minimoUso, perfisUso } from "./objetivos.js";
import {
  marcasPreview,
  prioridadesPreview,
  criteriosUso,
  motivoMarcaNotebook,
} from "./preferencias.js";
import {
  percentualPreview,
  perifericosPreview,
  webcamSolicitada,
  precisaPerifericos,
  MINIMO_PERCENTUAL_PERIFERICOS,
  MAXIMO_PERCENTUAL_PERIFERICOS,
} from "./perifericos.js";
import { comprimentosDisponiveis } from "./catalogo.js";

export class ErroGeracaoFormulario extends Error {
  constructor(codigo, etapa, mensagem) {
    super(mensagem);
    this.name = "ErroGeracaoFormulario";
    this.codigo = codigo;
    this.etapa = etapa;
  }
}
export function avaliarOrcamentoPreview(tipo, respostas) {
  const percentual = percentualPreview(respostas, tipo),
    minimo = minimoUso(respostas.objetivo);
  if (
    precisaPerifericos(tipo, respostas) &&
    (!Number.isInteger(percentual) ||
      percentual < MINIMO_PERCENTUAL_PERIFERICOS ||
      percentual > MAXIMO_PERCENTUAL_PERIFERICOS)
  )
    return {
      valido: false,
      minimo,
      mensagem: `Escolha uma porcentagem inteira entre ${MINIMO_PERCENTUAL_PERIFERICOS}% e ${MAXIMO_PERCENTUAL_PERIFERICOS}% do orçamento total para os periféricos.`,
    };
  const d = dividirOrcamento(respostas.orcamento, percentual);
  if (!d)
    return {
      valido: false,
      mensagem: "Informe um orçamento válido para continuar.",
      minimo,
    };
  const minimoPerifericos =
    tipo === "pc" && precisaPerifericos(tipo, respostas) ? 500 : 0;
  const minimoTotal =
    Math.ceil(
      Math.max(
        (minimo * 100) / (100 - percentual),
        percentual ? (minimoPerifericos * 100) / percentual : 0,
      ) * 100,
    ) / 100;
  if (d.pc < minimo)
    return {
      valido: false,
      ...d,
      minimo,
      minimoTotal,
      mensagem: `Reserve pelo menos ${minimo.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} para ${perfisUso[respostas.objetivo]?.titulo.toLowerCase() || "o computador"}, depois dos acessórios.`,
    };
  if (d.perifericos < minimoPerifericos)
    return {
      valido: false,
      ...d,
      minimo,
      minimoTotal,
      mensagem:
        "Reserve pelo menos R$ 500 para os periféricos novos do desktop. O catálogo pode exigir mais.",
    };
  return { valido: true, ...d, minimo, minimoTotal };
}
export function validarEtapaPreview(tipo, pergunta, respostas, catalogo) {
  if (
    pergunta.tipo === "opcoes" &&
    !pergunta.opcoes.some(([v]) => v === respostas[pergunta.chave])
  )
    return "Escolha uma opção para continuar.";
  if (pergunta.tipo === "orcamento") {
    if (!orcamentoValido(respostas.orcamento))
      return "Informe um limite válido, maior que zero e de até R$ 1.000.000.";
    const d = avaliarOrcamentoPreview(tipo, respostas);
    if (!d.valido) return d.mensagem;
  }
  if (pergunta.tipo === "pecas") {
    if (!respostas.pecas?.length)
      return "Marque as peças que possui ou escolha “Ainda não tenho peças”.";
    if (
      respostas.pecas.some(
        (p) => p !== "nenhuma" && !respostas.pecasDetalhes?.[p]?.trim(),
      )
    )
      return "Informe o modelo de cada peça selecionada.";
  }
  if (pergunta.tipo === "perifericos") {
    if (!pergunta.opcoes.some(([v]) => v === respostas.perifericos))
      return "Escolha se deseja incluir acessórios.";
    if (
      tipo === "notebook" &&
      respostas.perifericos === "escolher-extras" &&
      !respostas.extrasNotebook.length
    )
      return "Selecione ao menos um acessório, ou escolha somente o notebook.";
    const d = avaliarOrcamentoPreview(tipo, respostas);
    if (!d.valido) return d.mensagem;
    if (
      tipo === "pc" &&
      respostas.perifericos === "alguns-perifericos" &&
      respostas.perifericosProprios.some(
        (p) => !respostas.pecasDetalhes?.[p]?.trim(),
      )
    )
      return "Informe o modelo dos periféricos que já possui.";
  }
  if (
    pergunta.tipo === "rede" &&
    ["cabo", "ambos"].includes(respostas.rede.tipo) &&
    respostas.rede.possuiAcessorio === false
  ) {
    if (!catalogo)
      return "Não conseguimos conferir os comprimentos de cabo. Recarregue a amostra ou escolha comprar o acessório separadamente.";
    if (
      !comprimentosDisponiveis(catalogo).includes(
        respostas.rede.comprimentoCaboM,
      )
    )
      return "Escolha um comprimento disponível na lista de cabos. Não aceitamos medidas personalizadas.";
  }
  return "";
}
export function validarRevisaoPreview(tipo, respostas) {
  if (!prioridadesPreview.some(([v]) => v === respostas.prioridade_montagem))
    return "Escolha a prioridade para concluir.";
  if (
    tipo === "pc" &&
    !marcasPreview.some(([v]) => v === respostas.preferencia_processador)
  )
    return "Escolha uma marca de processador ou deixe sem preferência.";
  if (tipo === "notebook")
    return motivoMarcaNotebook(
      respostas.marca_notebook,
      respostas,
      avaliarOrcamentoPreview(tipo, respostas).pc,
    );
  return "";
}
export function montarPlanoPreview(tipo, respostas) {
  if (!perfisUso[respostas.objetivo])
    throw new ErroGeracaoFormulario(
      "objetivo",
      "objetivo",
      "Escolha um tipo de uso válido para definir as prioridades.",
    );
  const d = avaliarOrcamentoPreview(tipo, respostas);
  if (!d.valido)
    throw new ErroGeracaoFormulario("orcamento", "orcamento", d.mensagem);
  const problema = validarRevisaoPreview(tipo, respostas);
  if (problema)
    throw new ErroGeracaoFormulario("preferencias", "revisao", problema);
  const extras =
    tipo === "pc"
      ? perifericosPreview
          .filter(
            ([v]) =>
              respostas.perifericos === "todos-perifericos" ||
              (respostas.perifericos === "alguns-perifericos" &&
                !respostas.perifericosProprios.includes(v)),
          )
          .map(([v]) => v)
      : respostas.perifericos === "escolher-extras"
        ? [...respostas.extrasNotebook]
        : [];
  if (webcamSolicitada(tipo, respostas) && !extras.includes("webcam"))
    extras.push("webcam");
  return {
    tipo,
    objetivo: respostas.objetivo,
    orcamentoTotal: respostas.orcamento,
    limiteComputador: d.pc,
    tetoPerifericos: d.perifericos,
    devolverSobraPerifericosAoPc: false,
    acessorios: extras,
    prioridadeMontagem: respostas.prioridade_montagem,
    criterios: criteriosUso(tipo, respostas, d.pc),
    ...(tipo === "pc"
      ? {
          aparencia: normalizarAparencia(respostas.aparencia),
          rede: structuredClone(respostas.rede),
        }
      : { telaPreferida: respostas.tela || "sem-preferencia" }),
    webcam: {
      solicitada: extras.includes("webcam"),
      preferirFullHd: true,
      cadastroCompraDisponivel: false,
    },
    instrucoes: [
      "Respeitar compatibilidade e os dois limites de gasto; não transferir a sobra dos periféricos ao computador.",
      tipo === "pc" && respostas.preferencia_processador !== "sem-preferencia"
        ? `O processador deve ser ${respostas.preferencia_processador.toUpperCase()}. Se inviável, devolver um erro identificado e não trocar a marca silenciosamente.`
        : "Escolher o processador conforme o objetivo e o orçamento.",
      "A aparência é flexível: tente cor, tamanho e estilo preferidos; se não houver combinação, use outra aparência compatível sem ultrapassar o orçamento.",
      ...(tipo === "notebook"
        ? [
            "O tamanho da tela é uma preferência flexível. Memória e SSD devem ser definidos pelo uso e pelo orçamento; não rejeitar um notebook adequado apenas pelo tamanho da tela.",
          ]
        : []),
      "Não omitir peças obrigatórias, não ignorar incompatibilidades e não inventar preço, estoque ou fichas para atender uma preferência.",
    ],
  };
}
export function validarResultadoGeracao(plano, resultado) {
  if (
    !resultado ||
    !orcamentoValido(resultado.precoComputador) ||
    !Number.isFinite(resultado.precoPerifericos) ||
    resultado.precoPerifericos < 0 ||
    !Array.isArray(resultado.errosCompatibilidade) ||
    !Array.isArray(resultado.pecasObrigatoriasAusentes)
  )
    throw new ErroGeracaoFormulario(
      "resposta-invalida",
      "revisao",
      "A geração não confirmou os custos da configuração. Nenhuma build pode ser aprovada.",
    );
  if (
    resultado.precoComputador > plano.limiteComputador ||
    resultado.precoPerifericos > plano.tetoPerifericos
  )
    throw new ErroGeracaoFormulario(
      "orcamento",
      "orcamento",
      "A configuração excedeu o limite do computador ou a reserva dos acessórios.",
    );
  if (plano.tipo === "pc" && !resultado.processador?.fabricante)
    throw new ErroGeracaoFormulario(
      "compatibilidade",
      "pecas",
      "A geração não identificou o processador da montagem.",
    );
  if (
    plano.tipo === "pc" &&
    plano.criterios.fabricanteCpuObrigatorio &&
    String(resultado.processador?.fabricante || "")
      .trim()
      .toLowerCase() !== plano.criterios.fabricanteCpuObrigatorio
  )
    throw new ErroGeracaoFormulario(
      "marca-processador",
      "revisao",
      "O processador retornado não é da marca escolhida. Revise a preferência ou tente uma nova geração.",
    );
  if (
    plano.tipo === "pc" &&
    plano.criterios.video === "dedicada" &&
    !resultado.placaVideo
  )
    throw new ErroGeracaoFormulario(
      "placa-video",
      "objetivo",
      "O uso escolhido exige placa de vídeo dedicada, mas a geração não a incluiu. A configuração não pode ser aprovada.",
    );
  if (
    resultado.errosCompatibilidade?.length ||
    resultado.pecasObrigatoriasAusentes?.length
  )
    throw new ErroGeracaoFormulario(
      "compatibilidade",
      "pecas",
      "A configuração tem peças obrigatórias ausentes ou conflitos confirmados. Não será salva.",
    );
  const avisos = [];
  if (
    plano.tipo === "notebook" &&
    plano.telaPreferida &&
    plano.telaPreferida !== "sem-preferencia" &&
    resultado.tela &&
    resultado.tela !== plano.telaPreferida
  )
    avisos.push(
      "O tamanho da tela foi adaptado para respeitar o uso e o orçamento. Não é uma incompatibilidade.",
    );
  if (
    plano.tipo === "notebook" &&
    String(resultado.fabricanteNotebook || "")
      .trim()
      .toLowerCase() === "apple"
  ) {
    const motivo = motivoMarcaNotebook(
      "apple",
      { objetivo: plano.objetivo },
      plano.limiteComputador,
    );
    if (motivo)
      throw new ErroGeracaoFormulario("marca-notebook", "revisao", motivo);
  }
  if (plano.aparencia) {
    const obtida = normalizarAparencia(resultado.aparencia);
    if (
      ["porte", "estilo", "cor"].some(
        (k) =>
          plano.aparencia[k] !== "sem-preferencia" &&
          plano.aparencia[k] !== obtida[k],
      )
    )
      avisos.push(
        "A aparência foi adaptada para respeitar orçamento e compatibilidade.",
      );
  }
  return { valido: true, avisos };
}
export async function gerarComPreferenciasFlexiveis(plano, gerar) {
  let resultado,
    adaptada = false;
  try {
    resultado = await gerar(structuredClone(plano));
  } catch (erro) {
    if (!["aparencia", "preferencias-esteticas"].includes(erro?.codigo))
      throw erro;
    const flexivel = structuredClone(plano);
    flexivel.aparencia = normalizarAparencia();
    adaptada = true;
    resultado = await gerar(flexivel);
  }
  const validacao = validarResultadoGeracao(plano, resultado);
  return {
    ...resultado,
    avisos: [
      ...validacao.avisos,
      ...(adaptada
        ? ["Foi necessário flexibilizar a aparência solicitada."]
        : []),
    ],
  };
}
export function identificarErroFormulario(erro) {
  if (erro instanceof ErroGeracaoFormulario) return erro;
  const etapas = {
    orcamento: "orcamento",
    perifericos: "perifericos",
    rede: "rede",
    "marca-processador": "revisao",
    compatibilidade: "pecas",
  };
  const etapa = etapas[erro?.codigo];
  return new ErroGeracaoFormulario(
    etapa ? erro.codigo : "servico",
    etapa || "revisao",
    etapa
      ? erro.message
      : "Não foi possível concluir a geração. O serviço não informou qual resposta causou a falha; nenhuma pergunta foi responsabilizada sem evidência.",
  );
}
export function resumoFormularioPreview(tipo, respostas) {
  return {
    previa: true,
    tipo,
    ...structuredClone(respostas),
    percentualPerifericos: percentualPreview(respostas, tipo),
    geracaoDisponivel: false,
  };
}
