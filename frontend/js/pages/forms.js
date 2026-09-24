import "../header.js";
import "../auth/auth.js";
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
      "Escolha uma faixa ou ajuste livremente o valor no controle abaixo.",
    opcoes: [
      ["ate-3000", "Até R$ 3.000", "Configuração essencial e econômica."],
      [
        "3000-5000",
        "De R$ 3.000 a R$ 5.000",
        "Desempenho equilibrado para o dia a dia.",
      ],
      [
        "5000-8000",
        "De R$ 5.000 a R$ 8.000",
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
      ["cooler", "Cooler / Water cooler"],
      ["fans", "Fans"],
      ["monitor", "Monitor"],
      ["teclado", "Teclado"],
      ["mouse", "Mouse"],
      ["headset", "Headset / Fone"],
      ["webcam", "Webcam"],
      ["microfone", "Microfone"],
    ],
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
  fans: "Ex.: Kit 3 fans Rise Mode 120 mm",
  monitor: "Ex.: LG UltraGear 24GN60R-B",
  teclado: "Ex.: Redragon Kumara K552",
  mouse: "Ex.: Logitech G203",
  headset: "Ex.: HyperX Cloud II",
  webcam: "Ex.: Logitech C920",
  microfone: "Ex.: HyperX SoloCast",
};

document.addEventListener("DOMContentLoaded", () => {
  const conteudo = document.querySelector("#question-content");
  const painel = document.querySelector("#question-info");
  const respostas = {};
  let indiceAtual = 0;
  let geracaoPergunta = 0;
  const animacoesCheckbox = new Map();
  const estadosCheckbox = new Map();
  const paginaConfiguracaoBuild = "./configuracao-build.html";
  const moeda = new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
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
      item.disabled = indice > 0 && !respostas[perguntas[indice - 1].chave];
      item.querySelector(".form-step-number").innerHTML =
        indice < indiceAtual
          ? '<i class="fa-solid fa-check"></i>'
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
    painel.innerHTML = `<div class="question-intro"><span class="question-tag font-1-xs">Montagem inteligente · ${pergunta.tag}</span><h1 class="font-1-xl">${pergunta.titulo}</h1><p class="font-2-s">${pergunta.descricao}</p></div><div class="manual-build"><h2 class="font-1-m-b">Deseja montar manualmente?</h2><p class="font-2-s">Escolha cada peça da sua build por conta própria quando a montagem manual estiver disponível.</p><button type="button" class="btn-primary-form" disabled aria-label="Montagem manual em breve">Montar manualmente · Em breve</button></div>`;
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
    const valor = respostas.orcamentoPersonalizado || 5000;
    const isActive = respostas.orcamento === "personalizado" ? "active" : "";
    return `<div class="budget-range ${isActive}"><div><span class="font-1-m-b">Orçamento personalizado</span><strong class="font-2-xs" id="budget-value">${moeda.format(valor)}</strong></div><input type="range" id="budget-range" min="1500" max="20000" step="500" value="${valor}" style="--range-progress: ${progressoRange(valor)}%" aria-label="Valor do orçamento personalizado"><div class="range-labels"><span class="font-2-xs">R$ 1.500</span><span class="font-2-xs">R$ 20.000+</span></div></div>`;
  }

  function progressoRange(valor) {
    return ((valor - 1500) / (20000 - 1500)) * 100;
  }

  function renderizarPergunta() {
    limparCheckboxesLottie();
    const geracao = geracaoPergunta;
    const pergunta = perguntas[indiceAtual];
    renderizarPainel(pergunta);
    conteudo.classList.remove("question-enter");
    void conteudo.offsetWidth;
    conteudo.classList.add("question-enter");
    conteudo.classList.toggle("pieces-question-content", pergunta.chave === "pecas");
    conteudo.innerHTML = `<div class="options-heading"><p class="font-1-m-b">${pergunta.multipla ? "Selecione as opções aplicáveis" : "Escolha uma opção"}</p><span class="font-2-xs">${indiceAtual + 1} de ${perguntas.length}</span></div><fieldset class="question-options ${pergunta.multipla ? "pieces-grid" : ""}"><legend class="sr-only">${pergunta.titulo}</legend>${opcoesHtml(pergunta)}</fieldset>${pergunta.chave === "orcamento" ? rangeHtml() : ""}<div id="form-navigation"><button type="button" class="btn-ghost" ${indiceAtual === 0 ? "disabled" : ""}><i class="fa-solid fa-arrow-left"></i> Voltar</button><button type="button" class="btn-primary-form" id="next-question" ${podeAvancar() ? "" : "disabled"}>${indiceAtual === perguntas.length - 1 ? "Gerar configuração" : "Avançar"} <i class="fa-solid fa-arrow-right"></i></button></div>`;
    conteudo
      .querySelector(".btn-ghost")
      .addEventListener("click", () => navegarPara(indiceAtual - 1));
    conteudo
      .querySelectorAll(`.question-options input[name="${pergunta.chave}"]`)
      .forEach((input) =>
        input.addEventListener("change", () => tratarSelecao(pergunta, input)),
      );
    conteudo
      .querySelector("#budget-range")
      ?.addEventListener("input", atualizarRange);
    conteudo.querySelector("#next-question").addEventListener("click", avancar);
    if (pergunta.multipla) {
      vincularCamposDetalhesPecas();
      iniciarCheckboxesLottie(geracao);
    }
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

  function podeAvancar() {
    if (perguntas[indiceAtual].chave === "orcamento")
      return Boolean(respostas.orcamento);
    const resposta = respostas[perguntas[indiceAtual].chave];
    if (!Array.isArray(resposta)) return Boolean(resposta);
    if (resposta.length === 0) return false;
    if (resposta.includes("nenhuma")) return true;

    return resposta.every(
      (peca) => respostas.pecasDetalhes?.[peca]?.trim().length > 0,
    );
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
      const budgetRange = conteudo.querySelector(".budget-range");
      if (budgetRange) budgetRange.classList.remove("active");
    }
    conteudo.querySelector("#next-question").disabled = !podeAvancar();
    atualizarMenu();
  }

  function atualizarRange(evento) {
    respostas.orcamentoPersonalizado = Number(evento.target.value);
    respostas.orcamento = "personalizado";
    conteudo.querySelector("#budget-value").textContent = moeda.format(
      respostas.orcamentoPersonalizado,
    );
    evento.target.style.setProperty(
      "--range-progress",
      `${progressoRange(respostas.orcamentoPersonalizado)}%`,
    );
    conteudo.querySelectorAll('input[name="orcamento"]').forEach((input) => {
      input.checked = false;
    });
    const budgetRange = conteudo.querySelector(".budget-range");
    if (budgetRange) budgetRange.classList.add("active");
    conteudo.querySelector("#next-question").disabled = false;
    atualizarMenu();
  }

  function avancar() {
    if (!podeAvancar()) return;
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

  function mostrarGerando() {
    limparCheckboxesLottie();
    atualizarMenu();
    sessionStorage.setItem(
      "boostio:respostas-formulario",
      JSON.stringify(respostas),
    );
    painel.innerHTML = `<div class="question-intro"><span class="question-tag font-1-xs">Última etapa</span><h1 class="font-1-xl">Estamos montando sua configuração ideal.</h1><p class="font-2-s">Analisando suas escolhas, orçamento e peças que já possui.</p></div>`;
    conteudo.innerHTML = `<div class="build-loading" role="status"><span class="build-loader" aria-hidden="true"></span><h2 class="font-1-l">Criando a sua build</h2><p class="font-2-s">Isso leva apenas alguns instantes.</p><div class="loading-steps"><span class="active font-1-xs">Analisando preferências</span><span class="font-1-xs">Verificando compatibilidade</span><span class="font-1-xs">Preparando a configuração</span></div></div>`;
    window.setTimeout(() => {
      window.location.href = paginaConfiguracaoBuild;
    }, 2600);
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
