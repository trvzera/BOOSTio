import { htmlSeguro as h, moeda } from "../../build/catalogo.js";
import { iconeAnimado } from "../../components/ui.js";
import { pecasPreview } from "./perguntas.js";
import { minimoUso, perfisUso } from "./objetivos.js";
import {
  prioridadesPreview,
  marcasPreview,
  marcasNotebook,
  motivoMarcaNotebook,
} from "./preferencias.js";
import {
  perifericosPreview,
  acessoriosNotebook,
  precisaPerifericos,
} from "./perifericos.js";
import { avaliarOrcamentoPreview } from "./regras.js";

export function opcoesHtml(
  chave,
  lista,
  ctx,
  { multipla = false, explicacao = false, bloqueio = () => "" } = {},
) {
  const { respostas: r, id } = ctx;
  const legenda =
    {
      objetivo: "Uso principal",
      pecas: "Peças que já possui",
      perifericos: "Incluir acessórios",
      perifericosProprios: "Periféricos que já possui",
      extrasNotebook: "Acessórios externos",
      marca_notebook: "Marca de notebook",
      preferencia_processador: "Marca do processador",
      prioridade_montagem: "Prioridade da montagem",
    }[chave] || chave;
  return (
    '<fieldset class="test-form-options"><legend class="sr-only">' +
    h(legenda) +
    "</legend>" +
    lista
      .map(([valor, titulo, descricao]) => {
        const selecionado = Array.isArray(r[chave])
            ? r[chave].includes(valor)
            : r[chave] === valor,
          motivo = bloqueio(valor);
        return (
          '<label class="test-form-choice ui-check"><input type="' +
          (multipla ? "checkbox" : "radio") +
          '" name="' +
          id(chave) +
          '" data-answer="' +
          h(chave) +
          '" value="' +
          h(valor) +
          '"' +
          (selecionado ? " checked" : "") +
          (motivo ? " disabled" : "") +
          ">" +
          iconeAnimado(multipla ? "checkbox" : "circledot") +
          "<span><strong>" +
          h(titulo) +
          "</strong>" +
          (descricao
            ? "<small" +
              (explicacao ? " data-knowledge-beginner" : "") +
              ">" +
              h(descricao) +
              "</small>"
            : "") +
          (motivo
            ? '<small class="test-form-restriction">' + h(motivo) + "</small>"
            : "") +
          "</span></label>"
        );
      })
      .join("") +
    "</fieldset>"
  );
}
export function selectHtml(
  chave,
  titulo,
  opcoes,
  ctx,
  { atributo = "data-select", valor = ctx.respostas[chave] } = {},
) {
  return (
    '<label class="test-form-field" for="' +
    ctx.id(chave) +
    '">' +
    h(titulo) +
    '<select id="' +
    ctx.id(chave) +
    '" ' +
    atributo +
    '="' +
    h(chave) +
    '">' +
    opcoes
      .map(
        ([v, t, disabled]) =>
          '<option value="' +
          h(String(v)) +
          '"' +
          (String(valor) === String(v) ? " selected" : "") +
          (disabled ? " disabled" : "") +
          ">" +
          h(t) +
          "</option>",
      )
      .join("") +
    "</select></label>"
  );
}
function detalhePeca(chave, titulo, ctx) {
  return (
    '<label class="test-form-field" for="' +
    ctx.id("model-" + chave) +
    '">Modelo de ' +
    h(titulo.toLowerCase()) +
    '<input id="' +
    ctx.id("model-" + chave) +
    '" data-model="' +
    h(chave) +
    '" type="text" maxlength="120" required autocomplete="off" value="' +
    h(ctx.respostas.pecasDetalhes[chave] || "") +
    '"></label>'
  );
}
export function orcamentoHtml(ctx) {
  const { respostas: r, id, tipo } = ctx,
    minimo = minimoUso(r.objetivo),
    d = avaliarOrcamentoPreview(tipo, r);
  return (
    '<div class="test-form-budget-presets">' +
    [minimo, 5000, 8000]
      .map(
        (v) =>
          '<button type="button" class="btn-secondary" data-budget="' +
          v +
          '" aria-pressed="' +
          (r.orcamento === v) +
          '" aria-label="Definir limite de ' +
          v +
          ' reais">Até ' +
          moeda(v) +
          "</button>",
      )
      .join("") +
    "</div>" +
    '<label class="test-form-field" for="' +
    id("budget") +
    '">Seu limite total em reais<input id="' +
    id("budget") +
    '" data-number="orcamento" type="number" inputmode="decimal" min="' +
    minimo +
    '" max="1000000" step="0.01" required value="' +
    h(r.orcamento ?? "") +
    '" aria-describedby="' +
    id("minimum") +
    '"></label>' +
    '<input class="test-form-budget-range" type="range" min="' +
    minimo +
    '" max="' +
    Math.max(20000, r.orcamento || 20000) +
    '" step="100" data-preview-budget-range aria-label="Ajustar limite de teste de cem em cem reais" value="' +
    h(r.orcamento || 5000) +
    '">' +
    '<p class="test-form-help" id="' +
    id("minimum") +
    '">Mínimo para ' +
    h(perfisUso[r.objetivo]?.titulo.toLowerCase() || "este uso") +
    ": " +
    moeda(minimo) +
    " somente para o computador, depois dos acessórios. Frete à parte.</p>" +
    '<p class="test-form-help" data-budget-split>' +
    (!d.valido
      ? h(d.mensagem)
      : "Até " +
        moeda(d.pc) +
        " para o computador e " +
        moeda(d.perifericos) +
        " para os acessórios.") +
    "</p>"
  );
}
export function redeHtml(ctx) {
  const rede = ctx.respostas.rede || {},
    campos = { ...ctx, respostas: rede };
  let html = selectHtml(
    "tipo",
    "Como você quer se conectar?",
    [
      ["indefinido", "Ainda não sei"],
      ["wifi", "Wi-Fi"],
      ["cabo", "Cabo de rede"],
      ["ambos", "Wi-Fi e cabo"],
    ],
    campos,
    { atributo: "data-network" },
  );
  if (rede.tipo === "indefinido")
    return html + '<p class="test-form-help">Você pode decidir depois.</p>';
  html += selectHtml(
    "possuiAcessorio",
    "Quer incluir os acessórios?",
    [
      ["confirmar", "Vou decidir depois"],
      ["false", "Sim, incluir"],
      ["true", "Não incluir; já tenho ou vou comprar separadamente"],
    ],
    campos,
    {
      atributo: "data-network",
      valor:
        rede.possuiAcessorio == null
          ? "confirmar"
          : String(rede.possuiAcessorio),
    },
  );
  if (["cabo", "ambos"].includes(rede.tipo) && rede.possuiAcessorio === false) {
    const cabos = ctx.catalogo?.cabos || [];
    html += selectHtml(
      "comprimentoCaboM",
      "Comprimento do cabo CAT6",
      [
        ["", "Escolha um comprimento"],
        ...cabos.map((c) => [
          c.metros,
          c.metros + " m" + (!c.disponivel ? " · sem oferta na amostra" : ""),
          !c.disponivel,
        ]),
      ],
      campos,
      { atributo: "data-network", valor: rede.comprimentoCaboM ?? "" },
    );
    html +=
      '<p class="test-form-help">Somente comprimentos cadastrados. Meça o caminho até o roteador; não encurtamos nem montamos cabos sob medida. A disponibilidade será conferida novamente ao integrar a geração.</p>';
  }
  return html;
}
function reservaHtml(ctx) {
  const { respostas: r, id, tipo } = ctx;
  if (!precisaPerifericos(tipo, r)) return "";
  return (
    '<label class="test-form-field" for="' +
    id("percent") +
    '">Porcentagem máxima para os acessórios novos<input id="' +
    id("percent") +
    '" data-number="percentualPerifericos" type="number" min="1" max="99" step="1" required value="' +
    h(r.percentualPerifericos) +
    '" aria-describedby="' +
    id("allocation") +
    '"></label>' +
    '<p class="test-form-help" id="' +
    id("allocation") +
    '" data-allocation></p><p class="test-form-help">Não precisamos gastar toda a reserva. O que sobrar fica com você e não aumenta o limite do computador.' +
    (tipo === "pc"
      ? " O mínimo atual para periféricos novos é R$ 500; o catálogo pode exigir mais."
      : " Escolha só os acessórios de que precisa.") +
    "</p>"
  );
}
function webcamHtml(ctx) {
  const r = ctx.respostas;
  if (!r.perifericos || r.perifericos === "sem-perifericos") return "";
  return (
    '<label class="test-form-choice ui-check"><input type="checkbox" data-webcam' +
    (r.incluirWebcam ? " checked" : "") +
    ">" +
    iconeAnimado("checkbox") +
    "<span><strong>Incluir uma webcam</strong><small>Para reuniões, sugerimos uma câmera Full HD. Você pode desmarcar. Ainda não há webcams para compra no catálogo desta prévia.</small></span></label>"
  );
}
export function perifericosHtml(ctx) {
  const { respostas: r, tipo } = ctx;
  if (tipo === "notebook")
    return (
      (r.perifericos === "escolher-extras"
        ? '<div class="test-form-group"><h4>Quais acessórios externos deseja?</h4>' +
          opcoesHtml("extrasNotebook", acessoriosNotebook, ctx, {
            multipla: true,
          }) +
          '<p class="test-form-help">A webcam externa é opcional; a câmera do próprio notebook será considerada na escolha do modelo.</p></div>'
        : "") + reservaHtml(ctx)
    );
  return (
    (r.perifericos === "alguns-perifericos"
      ? '<div class="test-form-group"><h4>Quais você já possui?</h4>' +
        opcoesHtml("perifericosProprios", perifericosPreview, ctx, {
          multipla: true,
        }) +
        perifericosPreview
          .filter(([v]) => r.perifericosProprios.includes(v))
          .map(([v, t]) => detalhePeca(v, t, ctx))
          .join("") +
        "</div>"
      : "") +
    webcamHtml(ctx) +
    reservaHtml(ctx)
  );
}
export function auditoriaPerifericosHtml(catalogo) {
  if (!catalogo)
    return '<p class="test-form-help">A amostra local de cabos e periféricos ainda não foi carregada.</p>';
  const titulos = {
    teclado: "Teclados",
    mouse: "Mouses",
    monitor: "Monitores",
    fone: "Fones",
  };
  return (
    '<details class="test-form-catalog"><summary>Ver a amostra de periféricos gamers</summary><p>' +
    h(catalogo.fonte) +
    " Conferência: " +
    h(catalogo.verificadoEm) +
    '.</p><div class="test-form-catalog-grid">' +
    Object.entries(catalogo.perifericos)
      .map(
        ([tipo, p]) =>
          "<article><h4>" +
          titulos[tipo] +
          "</h4><p>" +
          p.comPrecoEEstoque +
          " com preço e estoque locais." +
          (tipo === "teclado"
            ? " " + p.mecanicosComSwitch + " mecânicos com switch informado."
            : tipo === "mouse"
              ? " " + p.sensorInformado + " com sensor informado."
              : tipo === "monitor"
                ? " " + p.semPainel + " sem informação do painel."
                : "") +
          "</p><ul>" +
          p.exemplos
            .map(
              (e) =>
                "<li>" +
                h(
                  [
                    e.fabricante,
                    e.modelo,
                    e.switch || e.sensor || e.tipo_painel,
                  ]
                    .filter(Boolean)
                    .join(" · "),
                ) +
                (e.taxa_atualizacao_hz
                  ? " · " + e.taxa_atualizacao_hz + " Hz"
                  : "") +
                "</li>",
            )
            .join("") +
          "</ul></article>",
      )
      .join("") +
    "</div><p>Webcams: nenhum modelo integrado para compra.</p>" +
    catalogo.alertas
      .map(
        (a) =>
          "<p>" +
          h(a.mensagem) +
          (a.fonte
            ? ' <a href="' +
              h(a.fonte) +
              '" target="_blank" rel="noopener noreferrer" aria-label="Conferir classificação no fabricante em nova aba">Conferir no fabricante</a>'
            : "") +
          "</p>",
      )
      .join("") +
    "</details>"
  );
}
export function camposHtml(pergunta, ctx) {
  const { respostas: r, tipo } = ctx;
  if (pergunta.tipo === "orcamento") return orcamentoHtml(ctx);
  if (pergunta.tipo === "rede")
    return "<div data-preview-network>" + redeHtml(ctx) + "</div>";
  if (pergunta.tipo === "aparencia")
    return (
      '<p class="test-form-scroll-hint">' +
      iconeAnimado("arrow", "down") +
      "Role para ver todas as preferências.</p><div data-preview-appearance-form></div>"
    );
  if (pergunta.tipo === "preferencias")
    return (
      selectHtml(
        "armazenamento",
        "Espaço para arquivos e programas",
        [
          ["sem-preferencia", "Quero ajuda para escolher"],
          ["512-gb", "SSD de pelo menos 512 GB"],
          ["1-tb", "SSD de pelo menos 1 TB"],
        ],
        ctx,
      ) +
      selectHtml(
        "bateria",
        "Uso longe da tomada",
        [
          ["sem-preferencia", "Ainda não sei"],
          ["priorizar", "Quero priorizar a duração da bateria"],
          ["tomada", "Vou usar mais ligado à tomada"],
        ],
        ctx,
      )
    );
  return (
    (pergunta.chave === "objetivo"
      ? '<p class="test-form-scroll-hint">' +
        iconeAnimado("arrow", "down") +
        "Role nesta área para ver todos os usos.</p>"
      : "") +
    opcoesHtml(pergunta.chave, pergunta.opcoes, ctx, {
      multipla: pergunta.tipo === "pecas",
      explicacao: pergunta.tipo === "pecas",
    }) +
    (pergunta.tipo === "pecas"
      ? '<div class="test-form-group">' +
        pecasPreview
          .filter(([v]) => v !== "nenhuma" && r.pecas.includes(v))
          .map(([v, t]) => detalhePeca(v, t, ctx))
          .join("") +
        '<p class="test-form-help">Os modelos informados ainda precisam de confirmação no catálogo.</p></div>'
      : "") +
    (pergunta.tipo === "perifericos"
      ? perifericosHtml(ctx) + auditoriaPerifericosHtml(ctx.catalogo)
      : "")
  );
}
export function revisaoHtml(ctx) {
  const r = ctx.respostas,
    d = avaliarOrcamentoPreview(ctx.tipo, r);
  const marcas =
    ctx.tipo === "pc"
      ? '<h4>Marca obrigatória do processador</h4><p class="test-form-help">Se escolher Intel ou AMD, não trocaremos a marca para concluir a montagem. Se for inviável, pediremos para rever a escolha ou o orçamento.</p>' +
        opcoesHtml("preferencia_processador", marcasPreview, ctx)
      : '<h4>Tem preferência de marca do notebook?</h4><p class="test-form-help">A marca é uma preferência; cada modelo ainda precisa atender ao uso. Apple fica disponível nesta prévia a partir de R$ 6.000 para o notebook e sem foco em jogos. Isso não significa que Macs não executem jogos ou que exista oferta por esse preço.</p>' +
        opcoesHtml("marca_notebook", marcasNotebook, ctx, {
          bloqueio: (m) => motivoMarcaNotebook(m, r, d.pc),
        });
  return (
    marcas +
    "<h4>O que deseja priorizar?</h4>" +
    opcoesHtml("prioridade_montagem", prioridadesPreview, ctx) +
    '<p class="test-form-help">As preferências estéticas serão tentadas. Elas não podem aumentar o orçamento, impedir a montagem ou reduzir a compatibilidade.</p><details class="test-form-summary"><summary>Ver respostas e regras para a geração</summary><pre data-preview-answers></pre></details>'
  );
}
