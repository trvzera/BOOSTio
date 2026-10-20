import "../header.js";
import "../auth/auth.js";
import { normalizarRede, vincularRede } from "../build/rede.js";
import { planejamentoLocal } from "../build/planejamento.js";
import { orcamentoValido, dividirOrcamento } from "../build/orcamento-formulario.js";
import { carregarPerfil } from "../conta/perfil.js";
import { acompanharCarregamento } from "../components/page-loading.js";
import { criarBuild, verificarEspacoBuild } from "../api/build/builds.js";
import { pecasPropriasFormulario } from "../build/pecas-proprias.js";
import { buscarUsuarioLogado } from "../api/usuario/buscarUsuarioLogado.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";
import { iniciarControlesNumericos } from "../components/number-stepper.js";
import {
  registrarAnimacao,
  destruirAnimacao,
} from "../components/lottie-controller.js";

const perguntas = [
  {
    chave: "objetivo",
    etapa: "Objetivo",
    tag: "Etapa 01",
    titulo: "Para que você vai usar o computador?",
    descricao:
      "Escolha a utilização principal para equilibrarmos desempenho e custo-benefício.",
    opcoes: [
      [
        "estudos",
        "Estudos",
        "Navegação, Office, faculdade e tarefas escolares.",
      ],
      ["jogos", "Jogos", "FPS, AAA e jogos competitivos."],
      [
        "trabalho-casual",
        "Trabalho casual",
        "Planilhas, reuniões, e-mails e videoconferências.",
      ],
      [
        "trabalho-pesado",
        "Trabalho pesado",
        "Edição de vídeo, 3D, programação e renderização.",
      ],
      [
        "todos",
        "Um pouco de tudo",
        "Equilíbrio entre jogos, estudos e trabalho.",
      ],
    ],
  },
  {
    chave: "orcamento",
    etapa: "Orçamento",
    tag: "Etapa 02",
    titulo: "Quanto pretende investir na sua build?",
    descricao:
      "Escolha um teto de orçamento, ajuste pelo controle ou digite o valor exato.",
    opcoes: [
      ["ate-3000", "Até R$ 3.000", "Configuração essencial e econômica."],
      [
        "3000-5000",
        "Até R$ 5.000",
        "Desempenho equilibrado para o dia a dia.",
      ],
      [
        "5000-8000",
        "Até R$ 8.000",
        "Mais potência para jogos e tarefas exigentes.",
      ],
    ],
  },
  {
    chave: "pecas",
    etapa: "Suas peças",
    tag: "Etapa 03",
    titulo: "O que você já possui?",
    descricao:
      "Marque todas as peças e periféricos que pretende reaproveitar e informe o modelo de cada item. Se estiver começando do zero, marque a primeira opção.",
    multipla: true,
    opcoes: [
      ["nenhuma", "Ainda não tenho peças"],
      ["processador", "Processador"],
      ["placa-mae", "Placa-mãe"],
      ["placa-video", "Placa de vídeo"],
      ["memoria", "Memória RAM"],
      ["ssd", "SSD"],
      ["hd", "HD"],
      ["fonte", "Fonte"],
      ["gabinete", "Gabinete"],
      ["cooler", "Air cooler"],
      ["water-cooler", "Water cooler"],
      ["fans", "Fans"],
      ["monitor", "Monitor"],
      ["teclado", "Teclado"],
      ["mouse", "Mouse"],
      ["headset", "Headset / Fone"],
      ["webcam", "Webcam"],
      ["microfone", "Microfone"],
    ],
  },
  {
    chave:"rede",etapa:"Conexão",tag:"Etapa 04",
    titulo:"Como seu PC vai se conectar à internet?",
    descricao:"Informe se usará cabo de rede ou Wi-Fi e se já possui o necessário. Você poderá adicionar o acessório pelo catálogo da build quando houver produtos cadastrados.",
    opcoes:[],
  },
];

const exemplosPecas = {
  processador: "Ex.: AMD Ryzen 5 5600",
  "placa-mae": "Ex.: ASUS TUF Gaming B550M-Plus",
  "placa-video": "Ex.: GeForce RTX 4060 8 GB",
  memoria: "Ex.: Kingston Fury 16 GB DDR4 3200 MHz",
  ssd: "Ex.: Kingston NV2 1 TB NVMe",
  hd: "Ex.: Seagate Barracuda 2 TB",
  fonte: "Ex.: Corsair CV650 650 W",
  gabinete: "Ex.: Montech Air 100",
  cooler: "Ex.: DeepCool AK400",
  "water-cooler": "Ex.: Corsair H100i",
  fans: "Ex.: Kit 3 fans Rise Mode 120 mm",
  monitor: "Ex.: LG UltraGear 24GN60R-B",
  teclado: "Ex.: Redragon Kumara K552",
  mouse: "Ex.: Logitech G203",
  headset: "Ex.: HyperX Cloud II",
  webcam: "Ex.: Logitech C920",
  microfone: "Ex.: HyperX SoloCast",
};

document.addEventListener("DOMContentLoaded", async () => {
  const conteudo = document.querySelector("#question-content");
  const painel = document.querySelector("#question-info");
  await acompanharCarregamento(carregarPerfil().catch(() => null));
  const planejamento = planejamentoLocal();
  const respostas = {rede:normalizarRede()};
  if (planejamento.usarBudget && planejamento.budget != null) {
    respostas.orcamento = "personalizado";
    respostas.orcamentoPersonalizado = planejamento.budget;
  }
  let indiceAtual = 0;
  let geracaoPergunta = 0;
  const animacoesCheckbox = new Map();
  const estadosCheckbox = new Map();
  const paginaConfiguracaoBuild = "./configuracao-build.html";
  const moeda = new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 2,
  });

  function escaparHtml(valor = "") {
    return String(valor)
      .replaceAll("&", "&amp;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function atualizarMenu() {
    document.querySelectorAll(".form-step").forEach((item, indice) => {
      item.classList.toggle("active", indice === indiceAtual);
      item.classList.toggle("completed", indice < indiceAtual);
      item.disabled = perguntas.slice(0,indice).some((_,i) => !etapaRespondida(i));
      item.querySelector(".form-step-number").innerHTML =
        indice < indiceAtual
          ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>'
          : String(indice + 1).padStart(2, "0");
    });
    document
      .querySelectorAll(".form-bar")
      .forEach((bar, indice) =>
        bar.classList.toggle("completed", indice < indiceAtual),
      );
  }

  function renderizarPainel(pergunta) {
    painel.classList.remove("question-enter");
    void painel.offsetWidth;
    painel.classList.add("question-enter");
    painel.innerHTML = `<div class="question-intro"><span class="question-tag font-1-xs">Montagem inteligente · ${pergunta.tag}</span><h1 class="font-1-xl">${pergunta.titulo}</h1><p class="font-2-s">${pergunta.descricao}</p></div><div class="manual-build"><h2 class="font-1-m-b">Deseja montar manualmente?</h2><p class="font-2-s">Escolha os componentes da sua build por conta própria no editor.</p><a href="./configuracao-build.html" class="btn-primary-form" aria-label="Montar manualmente no editor de build">Montar manualmente</a></div>`;
  }

  function opcoesHtml(pergunta) {
    const selecionadas = pergunta.multipla
      ? respostas.pecas || []
      : [respostas[pergunta.chave]];
    const tipo = pergunta.multipla ? "checkbox" : "radio";
    return pergunta.opcoes
      .map(([valor, titulo, descricao]) => {
        const selecionada = selecionadas.includes(valor);
        const atributosPeca = pergunta.chave === "pecas"
          ? ` data-piece="${valor}"`
          : "";
        const detalhe = pergunta.chave === "pecas" && selecionada
          ? detalhePecaHtml(valor, titulo)
          : "";

        return `<div class="option-card${detalhe ? " has-piece-detail" : ""}"${atributosPeca}><input type="${tipo}" name="${pergunta.chave}" id="${valor}" value="${valor}" ${selecionada ? "checked" : ""}><label for="${valor}"><span class="choice-control ${pergunta.multipla ? "choice-control-lottie" : ""}" ${pergunta.multipla ? `id="check-${valor}"` : ""} aria-hidden="true"></span><span><span class="option-title font-1-m-b">${titulo}</span>${descricao ? `<span class="option-desc font-2-xs">${descricao}</span>` : ""}</span></label>${detalhe}</div>`;
      })
      .join("");
  }

  function detalhePecaHtml(valor, titulo, visivel = true) {
    if (valor === "nenhuma") return "";

    const detalhe = respostas.pecasDetalhes?.[valor] || "";
    const placeholder = exemplosPecas[valor] || "Informe a marca e o modelo";

    return `<div class="piece-detail${visivel ? " is-visible" : ""}"><label class="font-1-xs" for="detalhe-${valor}">Qual ${titulo.toLowerCase()} você possui?</label><input class="piece-model-input font-2-xs" type="text" id="detalhe-${valor}" data-piece-detail="${valor}" value="${escaparHtml(detalhe)}" placeholder="${placeholder}" maxlength="120" autocomplete="off" required aria-describedby="ajuda-${valor}"><span class="piece-detail-help font-2-xs" id="ajuda-${valor}">Informe marca e modelo para verificarmos a compatibilidade.</span></div>`;
  }

  function rangeHtml() {
    const recebido = respostas.orcamentoPersonalizado ?? 5000;
    const valor = Number.isFinite(recebido) ? recebido : "";
    const maximo = Math.max(20000,valor);
    const isActive = respostas.orcamento === "personalizado" ? "active" : "";
    return `<div class="budget-range ${isActive}"><div><label class="font-1-m-b" for="budget-input">Orçamento personalizado (R$)</label><strong class="font-2-xs" id="budget-value">${valor === "" ? "Informe um valor" : moeda.format(valor)}</strong></div><input id="budget-input" type="number" inputmode="decimal" min="0.01" max="1000000" step="0.01" data-number-step="100" value="${valor}" aria-describedby="budget-help"><input type="range" id="budget-range" min="0" max="${Math.ceil(maximo / 100) * 100}" step="100" value="${Math.round(valor / 100) * 100}" style="--range-progress: ${progressoRange(valor)}%" aria-label="Ajustar orçamento de cem em cem reais"><p id="budget-help" class="font-2-xs">Controle e setas de R$ 100 em R$ 100. Digite para usar outro valor.</p></div>
      <fieldset class="peripheral-budget"><legend class="font-1-xs">Quer incluir periféricos nesse valor?</legend><label class="peripheral-budget-toggle ui-check"><input type="checkbox" id="budget-peripherals" ${respostas.incluirPerifericos ? "checked" : ""}>${iconeAnimado("checkbox")}<span class="peripheral-budget-label">Reservar parte do total para monitor, teclado, mouse e headset</span></label><div id="peripheral-allocation" ${respostas.incluirPerifericos ? "" : "hidden"}><label for="peripheral-percent">Porcentagem para periféricos</label><div class="peripheral-percent-field"><input type="number" id="peripheral-percent" min="1" max="99" step="1" inputmode="numeric" value="${respostas.percentualPerifericos ?? 20}"><span aria-hidden="true">%</span></div><p id="peripheral-budget-summary" class="font-2-xs" aria-live="polite"></p></div></fieldset>`;
  }

  const faixas = {"ate-3000":3000,"3000-5000":5000,"5000-8000":8000};
  const valorOrcamento = () => respostas.orcamento === "personalizado" ? respostas.orcamentoPersonalizado : faixas[respostas.orcamento];
  function atualizarReserva() {
    const valor = valorOrcamento() || 0;
    const percentual = respostas.incluirPerifericos ? respostas.percentualPerifericos ?? 20 : 0;
    const divisao = dividirOrcamento(valor,percentual);
    const resumo = conteudo.querySelector("#peripheral-budget-summary");
    if (resumo) resumo.textContent = divisao
      ? `${moeda.format(divisao.perifericos)} para periféricos · ${moeda.format(divisao.pc)} para o PC. O total não aumenta.` : "Informe um orçamento válido e uma porcentagem inteira de 1 a 99.";
    conteudo.querySelector("#next-question").disabled = !podeAvancar();
  }

  function progressoRange(valor) {
    return Number.isFinite(valor) ? Math.min(100,Math.max(0,valor / Math.max(20000,respostas.orcamentoPersonalizado || 0) * 100)) : 0;
  }

  function renderizarPergunta() {
    limparCheckboxesLottie();
    const geracao = geracaoPergunta;
    const pergunta = perguntas[indiceAtual];
    delete document.querySelector("#questions").dataset.formState;
    conteudo.dataset.question = pergunta.chave;
    renderizarPainel(pergunta);
    conteudo.classList.remove("question-enter");
    void conteudo.offsetWidth;
    conteudo.classList.add("question-enter");
    conteudo.classList.toggle("pieces-question-content", pergunta.chave === "pecas");
    const rotuloAvancar = indiceAtual === perguntas.length - 1 ? "Gerar build" : "Avançar";
    const campos = pergunta.chave === "rede" ? '<div id="form-network"></div>' : `<fieldset class="question-options ${pergunta.multipla ? "pieces-grid" : ""}"><legend class="sr-only">${pergunta.titulo}</legend>${opcoesHtml(pergunta)}</fieldset>`;
    conteudo.innerHTML = `
      <div class="options-heading">
        <p class="font-1-m-b">${pergunta.chave === "rede" ? "Planeje sua conexão" : pergunta.multipla ? "Selecione as opções aplicáveis" : "Escolha uma opção"}</p>
        <span class="font-2-xs">${indiceAtual + 1} de ${perguntas.length}</span>
      </div>
      ${pergunta.chave === "orcamento" ? `<div class="budget-fields">${campos}${rangeHtml()}</div>` : campos}
      <div id="form-navigation">
        <button type="button" class="btn-ghost" id="previous-question" aria-label="Etapa anterior" ${indiceAtual === 0 ? 'disabled data-disabled-reason="Você está na primeira etapa do formulário."' : ""}>${iconeAnimado("arrow","back")}<span>Voltar</span></button>
        <button type="button" class="btn-primary-form" id="next-question" aria-label="${rotuloAvancar}" ${podeAvancar() ? "" : "disabled"}><span>${rotuloAvancar}</span>${iconeAnimado("arrow")}</button>
      </div>`;
    if (pergunta.chave === "rede") vincularRede(conteudo.querySelector("#form-network"),respostas.rede,{prefixo:"form-rede",aoRenderizar:iniciarControlesNumericos,aoAlterar:rede => {
      respostas.rede = rede;
      conteudo.querySelector("#next-question").disabled = !podeAvancar();
    }});
    conteudo
      .querySelector("#previous-question")
      .addEventListener("click", () => navegarPara(indiceAtual - 1));
    conteudo
      .querySelectorAll(`.question-options input[name="${pergunta.chave}"]`)
      .forEach((input) =>
        input.addEventListener("change", () => tratarSelecao(pergunta, input)),
      );
    conteudo
      .querySelector("#budget-range")
      ?.addEventListener("input", atualizarRange);
    conteudo.querySelector("#budget-input")?.addEventListener("input", atualizarRange);
    conteudo.querySelector("#budget-peripherals")?.addEventListener("change", evento => {
      respostas.incluirPerifericos = evento.target.checked;
      respostas.percentualPerifericos ??= 20;
      conteudo.querySelector("#peripheral-allocation").hidden = !evento.target.checked;
      atualizarReserva(); atualizarMenu();
    });
    conteudo.querySelector("#peripheral-percent")?.addEventListener("input", evento => {
      respostas.percentualPerifericos = evento.target.valueAsNumber;
      atualizarReserva(); atualizarMenu();
    });
    conteudo.querySelector("#next-question").addEventListener("click", avancar);
    if (pergunta.chave === "orcamento") atualizarReserva();
    if (pergunta.multipla) {
      vincularCamposDetalhesPecas();
      iniciarCheckboxesLottie(geracao).catch(() => {});
    }
    iniciarControlesNumericos(conteudo);
    iniciarIcones(conteudo);
  }

  function vincularCamposDetalhesPecas() {
    conteudo.querySelectorAll(".piece-model-input").forEach((input) => {
      if (input.dataset.listener === "true") return;
      input.dataset.listener = "true";
      input.addEventListener("input", () => {
        respostas.pecasDetalhes ??= {};
        respostas.pecasDetalhes[input.dataset.pieceDetail] = input.value;
        input.classList.toggle("invalid", input.value.trim().length === 0);
        conteudo.querySelector("#next-question").disabled = !podeAvancar();
      });
    });
  }

  function sincronizarCamposDetalhesPecas() {
    const escolhidas = new Set(respostas.pecas || []);

    conteudo.querySelectorAll(".option-card[data-piece]").forEach((card) => {
      const valor = card.dataset.piece;
      const deveExibir = valor !== "nenhuma" && escolhidas.has(valor);
      const detalheAtual = card.querySelector(".piece-detail");

      if (deveExibir && !detalheAtual) {
        const titulo = card.querySelector(".option-title").textContent;
        card.insertAdjacentHTML(
          "beforeend",
          detalhePecaHtml(valor, titulo, false),
        );
        card.classList.add("has-piece-detail");
        const novoDetalhe = card.querySelector(".piece-detail");
        requestAnimationFrame(() => novoDetalhe.classList.add("is-visible"));
      } else if (deveExibir && detalheAtual) {
        detalheAtual.classList.add("is-visible");
        card.classList.add("has-piece-detail");
      } else if (!deveExibir && detalheAtual) {
        detalheAtual.classList.remove("is-visible");
        const removerDepoisDaTransicao = (evento) => {
          if (evento.propertyName !== "max-height") return;
          detalheAtual.removeEventListener(
            "transitionend",
            removerDepoisDaTransicao,
          );
          const checkbox = card.querySelector(':scope > input[name="pecas"]');
          if (checkbox?.checked) return;
          detalheAtual.remove();
          card.classList.remove("has-piece-detail");
        };
        detalheAtual.addEventListener(
          "transitionend",
          removerDepoisDaTransicao,
        );
      }
    });

    vincularCamposDetalhesPecas();
  }

  function limparCheckboxesLottie() {
    geracaoPergunta += 1;
    animacoesCheckbox.forEach((animacao, id) => destruirAnimacao(id, animacao));
    animacoesCheckbox.clear();
    estadosCheckbox.clear();
  }

  async function iniciarCheckboxesLottie(geracao) {
    for (const input of conteudo.querySelectorAll('input[name="pecas"]')) {
      if (geracao !== geracaoPergunta) return;
      const id = `check-${input.value}`;
      estadosCheckbox.set(id, input.checked);
      const animacao = await registrarAnimacao(id, "../lottie/checkbox.json");
      if (!animacao) continue;
      if (geracao !== geracaoPergunta) {
        destruirAnimacao(id, animacao);
        return;
      }
      animacoesCheckbox.set(id, animacao);
      animacao.addEventListener("DOMLoaded", () => {
        animacao.goToAndStop(input.checked ? animacao.totalFrames - 1 : 0, true);
        input.nextElementSibling.querySelector(".choice-control").classList.add("lottie-ready");
      });
    }
  }

  function sincronizarCheckboxesLottie() {
    conteudo.querySelectorAll('input[name="pecas"]').forEach((input) => {
      const id = `check-${input.value}`;
      if (estadosCheckbox.get(id) === input.checked) return;
      estadosCheckbox.set(id, input.checked);
      const animacao = animacoesCheckbox.get(id);
      if (!animacao || !animacao.isLoaded) return;
      if (input.checked) {
        animacao.goToAndStop(0, true);
        animacao.setDirection(1);
      } else {
        animacao.goToAndStop(animacao.totalFrames - 1, true);
        animacao.setDirection(-1);
      }
      animacao.play();
    });
  }

  function etapaRespondida(indice) {
    if (perguntas[indice].chave === "rede") return true;
    if (perguntas[indice].chave === "orcamento")
      return orcamentoValido(valorOrcamento()) &&
        (!respostas.incluirPerifericos || Number.isInteger(respostas.percentualPerifericos) && respostas.percentualPerifericos > 0 && respostas.percentualPerifericos < 100);
    const resposta = respostas[perguntas[indice].chave];
    if (!Array.isArray(resposta)) return Boolean(resposta);
    if (resposta.length === 0) return false;
    if (resposta.includes("nenhuma")) return true;

    return resposta.every(
      (peca) => respostas.pecasDetalhes?.[peca]?.trim().length > 0,
    );
  }
  function podeAvancar() {
    return etapaRespondida(indiceAtual) && ![...conteudo.querySelectorAll("#form-network input")].some(input => !input.checkValidity());
  }

  function tratarSelecao(pergunta, input) {
    if (!pergunta.multipla && input.checked)
      respostas[pergunta.chave] = input.value;
    else if (pergunta.multipla) {
      const escolhidas = new Set(respostas.pecas || []);
      if (input.value === "nenhuma") {
        escolhidas.clear();
        if (input.checked) {
          escolhidas.add("nenhuma");
          respostas.pecasDetalhes = {};
        }
      } else {
        escolhidas.delete("nenhuma");
        if (input.checked) {
          escolhidas.add(input.value);
        } else {
          escolhidas.delete(input.value);
          delete respostas.pecasDetalhes?.[input.value];
        }
      }
      respostas.pecas = [...escolhidas];
      conteudo.querySelectorAll('input[name="pecas"]').forEach((item) => {
        item.checked = escolhidas.has(item.value);
      });
      sincronizarCheckboxesLottie();
      sincronizarCamposDetalhesPecas();
    }
    if (pergunta.chave === "orcamento") {
      const valor = faixas[input.value];
      respostas.orcamentoPersonalizado = valor;
      conteudo.querySelector("#budget-input").value = valor;
      conteudo.querySelector("#budget-input").dispatchEvent(new Event("change",{bubbles:true}));
      conteudo.querySelector("#budget-range").value = valor;
      conteudo.querySelector("#budget-value").textContent = moeda.format(valor);
      const budgetRange = conteudo.querySelector(".budget-range");
      if (budgetRange) budgetRange.classList.remove("active");
      atualizarReserva();
    }
    conteudo.querySelector("#next-question").disabled = !podeAvancar();
    atualizarMenu();
  }

  function atualizarRange(evento) {
    respostas.orcamentoPersonalizado = evento.target.valueAsNumber;
    respostas.orcamento = "personalizado";
    conteudo.querySelector("#budget-value").textContent = Number.isFinite(respostas.orcamentoPersonalizado) ? moeda.format(respostas.orcamentoPersonalizado) : "Informe um valor";
    evento.target.setAttribute("aria-invalid",String(!orcamentoValido(respostas.orcamentoPersonalizado)));
    const slider = conteudo.querySelector("#budget-range"), numero = conteudo.querySelector("#budget-input");
    if (evento.target === slider) {
      numero.value = slider.value;
      numero.dispatchEvent(new Event("change",{bubbles:true}));
    }
    else if (orcamentoValido(respostas.orcamentoPersonalizado)) {
      slider.max = Math.ceil(Math.max(20000,respostas.orcamentoPersonalizado) / 100) * 100;
      slider.value = Math.round(respostas.orcamentoPersonalizado / 100) * 100;
    }
    slider.style.setProperty(
      "--range-progress",
      `${progressoRange(respostas.orcamentoPersonalizado)}%`,
    );
    conteudo.querySelectorAll('input[name="orcamento"]').forEach((input) => {
      input.checked = false;
    });
    const budgetRange = conteudo.querySelector(".budget-range");
    if (budgetRange) budgetRange.classList.add("active");
    atualizarReserva();
    atualizarMenu();
  }

  let gerando = false;
  let mensagensGeracao;
  const pararMensagens = () => clearInterval(mensagensGeracao);
  window.addEventListener("pagehide",pararMensagens);
  function avancar() {
    if (gerando || !podeAvancar()) return;
    if (indiceAtual === perguntas.length - 1) {
      mostrarGerando();
      return;
    }
    navegarPara(indiceAtual + 1);
  }

  function navegarPara(indice) {
    indiceAtual = indice;
    atualizarMenu();
    renderizarPergunta();
    if (window.matchMedia("(max-width: 850px)").matches) {
      window.scrollTo({ top: 0, behavior: "instant" });
    }
  }

  async function mostrarGerando() {
    if (gerando) return;
    gerando = true;
    document.querySelector("#questions").dataset.formState = "loading";
    conteudo.querySelectorAll("#form-navigation button, #tentar-gerar-build").forEach(botao => botao.disabled = true);
    document.querySelectorAll(".form-step").forEach(botao => botao.disabled = true);
    limparCheckboxesLottie();
    try {
      const sessao = await buscarUsuarioLogado();
      if (!sessao.auth) throw Object.assign(new Error("Entre na sua conta para salvar a build."),{status:401});
      await verificarEspacoBuild();
      painel.innerHTML = `<div class="question-intro"><span class="question-tag font-1-xs">Última etapa</span><h1 class="font-1-xl">Gerando sua build</h1><p class="font-2-s">Vamos selecionar peças compatíveis dentro do seu orçamento.</p></div>`;
      conteudo.innerHTML = `<div class="build-loading"><span class="build-loader" aria-hidden="true"></span><h2 class="font-1-m" role="status" id="generation-message">Analisando seu perfil</h2><p class="font-2-xs">A seleção pode levar alguns instantes. Aguarde nesta página.</p></div>`;
      const frases = ["Analisando seu perfil", "Buscando peças para o seu orçamento", "Pensando no equilíbrio da configuração", "Escolhendo as melhores peças para o seu uso"];
      let frase = 0;
      pararMensagens();
      mensagensGeracao = setInterval(() => {
        const mensagem = conteudo.querySelector("#generation-message");
        if (!mensagem) return pararMensagens();
        mensagem.textContent = frases[++frase % frases.length];
      },4000);
      const orcamento = respostas.orcamento === "personalizado"
        ? respostas.orcamentoPersonalizado : faixas[respostas.orcamento];
      const utilidade = perguntas[0].opcoes.find(opcao => opcao[0] === respostas.objetivo)?.[1] || respostas.objetivo;

      const resposta = await criarBuild({nome: `PC para ${utilidade}`, descricao: `Montagem para ${utilidade}.`, utilidade, orcamento,
        percentual_perifericos:respostas.incluirPerifericos ? respostas.percentualPerifericos : 0,
        pecas_proprias:pecasPropriasFormulario(respostas),rede:respostas.rede});
      window.location.href = `${paginaConfiguracaoBuild}?build_id=${encodeURIComponent(resposta.build.id)}`;
    } catch (erro) {
      gerando = false;
      document.querySelector("#questions").dataset.formState = "error";
      atualizarMenu();
      const semEspaco = erro.codigo === "limite-builds";
      conteudo.innerHTML = `<div class="build-generation-error"><h2 class="font-1-m" tabindex="-1">${semEspaco ? "Suas três vagas estão ocupadas" : "Não foi possível gerar sua build"}</h2><p id="erro-gerar-build" class="font-2-s" role="alert"></p><div class="generation-actions">${semEspaco ? '<a href="./builds.html" class="btn-primary" aria-label="Gerenciar minhas builds">Minhas builds</a>' : '<button type="button" id="tentar-gerar-build" class="btn-primary" aria-label="Tentar gerar build novamente">Tentar novamente</button>'}<button type="button" id="revisar-orcamento" class="btn-secondary" aria-label="Revisar orçamento">Revisar orçamento</button>${erro.status === 401 ? '<a href="./login.html" class="btn-ghost" aria-label="Entrar na conta">Entrar na conta</a>' : ""}</div></div>`;
      conteudo.querySelector("#erro-gerar-build").textContent = erro.message;
      conteudo.querySelector("#tentar-gerar-build")?.addEventListener("click", mostrarGerando);
      conteudo.querySelector("#revisar-orcamento").addEventListener("click",() => navegarPara(1));
      conteudo.querySelector("h2").focus({preventScroll:true});
    } finally { pararMensagens(); }
  }

  document
    .querySelectorAll(".form-step")
    .forEach((botao) =>
      botao.addEventListener("click", () =>
        navegarPara(Number(botao.dataset.step)),
      ),
    );
  atualizarMenu();
  renderizarPergunta();
});
