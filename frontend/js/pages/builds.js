import "../header.js";
import "../auth/auth.js";
import { registrarAnimacao } from "../components/lottie-controller.js";
import { formatarDataHora } from "../utils/formatarData.js";
import { abrirBuild, buildsLocais, sincronizarRascunho, CHAVE_PERFIL_LOCAL, linkCompartilhado } from "../build/estado.js";
import { htmlSeguro, carregarCatalogo } from "../build/catalogo.js";
import { avaliarBuild } from "../build/compatibilidade.js";
import { indicadorBuild,iniciarIndicadores } from "../build/indicador.js";
import { iniciarIcones } from "../components/ui.js";
import { navegarPara } from "../components/page-loading.js";

const LIMITE_BUILDS = 3;

const STATUS_CLASS = {
  incompleta: "incomplete",
  completa: "complete",
  erro: "error",
  atencao: "warning",
};

const ROTULOS_PECA = {
  cpu: "Processador",
  gpu: "Placa de vídeo",
  ram: "Memória RAM",
  placaMae: "Placa-mãe",
  armazenamento: "Armazenamento",
  fonte: "Fonte",
  gabinete: "Gabinete",
  cooler: "Cooler",
};

let builds = [
  {
    id: "build-demo-1",
    titulo: "Setup Gamer 1440p",
    descricao:
      "Montagem focada em jogos em 1440p, com equilíbrio entre GPU e processador.",
    visibilidade: "publico",
    travada: false,
    status: "incompleta",
    criadoEm: "2026-08-15T14:32:00.000Z",
    pecas: {
      cpu: true,
      gpu: true,
      ram: true,
      placaMae: true,
      armazenamento: true,
      fonte: true,
      gabinete: false,
      cooler: false,
    },
  },
];

let idEdicao = null;
let idExclusao = null;

try {
  builds = localStorage.getItem(CHAVE_PERFIL_LOCAL) !== null
    ? buildsLocais()
    : builds.map((build) => ({
        ...abrirBuild(new URLSearchParams({ id: build.id })), ...build,
      }));
} catch { /* A lista de demonstração continua disponível sem armazenamento. */ }

document.addEventListener("DOMContentLoaded", async () => {
  let catalogo = [];
  try { catalogo = await carregarCatalogo(); } catch { /* Exibe a lista mesmo se o catálogo falhar. */ }
  iniciarIcones();
  const lista = document.getElementById("builds-list");
  const vazio = document.getElementById("builds-empty");
  const quotaCount = document.getElementById("quota-count");
  const quotaFill = document.getElementById("quota-fill");
  const btnCriar = document.getElementById("btn-create-build");
  const btnImportar = document.getElementById("btn-import-build");
  const toast = document.getElementById("toast");
  const toastText = document.getElementById("toast-text");

  const modalEditar = document.getElementById("edit-build-modal");
  const inputTitulo = document.getElementById("edit-title");
  const inputDescricao = document.getElementById("edit-description");
  const modalDeletar = document.getElementById("delete-build-modal");

  function showToast(mensagem) {
    toastText.textContent = mensagem;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2600);
  }

  function calcularProgresso(pecas) {
    const chaves = Object.keys(pecas);
    if (!chaves.length) return 0;
    const preenchidas = chaves.filter((chave) => Boolean(pecas[chave])).length;
    return Math.round((preenchidas / chaves.length) * 100);
  }

  function resolverStatus(build) {
    if (build.status === "erro" || build.status === "atencao") {
      return build.status;
    }
    return (build.progresso ?? calcularProgresso(build.pecas || {})) === 100 ? "completa" : "incompleta";
  }

  function atualizarQuota() {
    const usadas = builds.length;
    quotaCount.textContent = `${usadas}/${LIMITE_BUILDS}`;
    quotaFill.style.width = `${(usadas / LIMITE_BUILDS) * 100}%`;
    btnCriar.disabled = usadas >= LIMITE_BUILDS;
    btnImportar.disabled = usadas >= LIMITE_BUILDS;
    btnCriar.dataset.disabledReason = btnImportar.dataset.disabledReason = "Limite de três builds atingido. Exclua uma build para liberar espaço.";
  }

  function fecharMenus() {
    lista.querySelectorAll(".build-menu-wrap.open").forEach((wrap) => {
      wrap.classList.remove("open");
      const trigger = wrap.querySelector(".build-menu-trigger");
      if (trigger) {
        trigger.setAttribute("aria-expanded", "false");
        trigger.setAttribute("aria-label", "Abrir menu da build " + trigger.dataset.buildTitle);
      }
    });
  }

  // Inicialização manual com validação de botões desabilitados
  async function iniciarAnimacoesDoCard(card, buildId) {
    // 1. Botão Trancar
    const btnTrancar = card.querySelector('[data-acao="trancar"]');
    if (btnTrancar) {
      const ltLock = await registrarAnimacao(
        `lottie-lock-${buildId}`,
        "../lottie/buildLock.json",
      );

      btnTrancar.addEventListener("mouseenter", () => {
        if (btnTrancar.disabled) return;
        if (ltLock) {
          ltLock.setDirection(1);
          ltLock.play();
        }
      });

      btnTrancar.addEventListener("mouseleave", () => {
        if (btnTrancar.disabled) return;
        if (ltLock) {
          ltLock.setDirection(-1);
          ltLock.play();
        }
      });
    }

    // 2. Botão Visibilidade (Público / Privado invertido: Público = Cadeado, Privado = Public)
    const btnVisibilidade = card.querySelector('[data-acao="visibilidade"]');
    if (btnVisibilidade) {
      const ltVisLock = await registrarAnimacao(
        `lottie-lock-vis-${buildId}`,
        "../lottie/buildLock.json",
      );
      const ltVisPublic = await registrarAnimacao(
        `lottie-public-vis-${buildId}`,
        "../lottie/buildPublic.json",
      );

      btnVisibilidade.addEventListener("mouseenter", () => {
        if (btnVisibilidade.disabled) return;
        if (ltVisLock) {
          ltVisLock.setDirection(1);
          ltVisLock.play();
        }
        if (ltVisPublic) {
          ltVisPublic.setDirection(1);
          ltVisPublic.play();
        }
      });

      btnVisibilidade.addEventListener("mouseleave", () => {
        if (btnVisibilidade.disabled) return;
        if (ltVisLock) {
          ltVisLock.setDirection(-1);
          ltVisLock.play();
        }
        if (ltVisPublic) {
          ltVisPublic.setDirection(-1);
          ltVisPublic.play();
        }
      });
    }

    // 3. Botão Editar
    const btnEditar = card.querySelector('[data-acao="editar"]');
    if (btnEditar) {
      const ltEditar = await registrarAnimacao(
        `lottie-edit-${buildId}`,
        "../lottie/buildPencil.json",
      );
      if (ltEditar) {
        btnEditar.addEventListener("mouseenter", () => {
          if (btnEditar.disabled) return;
          ltEditar.setDirection(1);
          ltEditar.play();
        });
        btnEditar.addEventListener("mouseleave", () => {
          if (btnEditar.disabled) return;
          ltEditar.setDirection(-1);
          ltEditar.play();
        });
      }
    }

    // 4. Botão Duplicar
    const btnDuplicar = card.querySelector('[data-acao="duplicar"]');
    if (btnDuplicar) {
      const ltClone = await registrarAnimacao(
        `lottie-clone-${buildId}`,
        "../lottie/buildClone.json",
      );
      if (ltClone) {
        btnDuplicar.addEventListener("mouseenter", () => {
          if (btnDuplicar.disabled) return;
          ltClone.setDirection(1);
          ltClone.play();
        });
        btnDuplicar.addEventListener("mouseleave", () => {
          if (btnDuplicar.disabled) return;
          ltClone.setDirection(-1);
          ltClone.play();
        });
      }
    }

    // 5. Botão Copiar Link
    const btnCopiar = card.querySelector('[data-acao="copiar-link"]');
    if (btnCopiar) {
      const ltCopy = await registrarAnimacao(
        `lottie-copy-${buildId}`,
        "../lottie/buildCopy.json",
      );
      if (ltCopy) {
        btnCopiar.addEventListener("mouseenter", () => {
          if (btnCopiar.disabled) return;
          ltCopy.setDirection(1);
          ltCopy.play();
        });
        btnCopiar.addEventListener("mouseleave", () => {
          if (btnCopiar.disabled) return;
          ltCopy.setDirection(-1);
          ltCopy.play();
        });
      }
    }

    // 6. Botão Baixar CSV
    const btnBaixarCsv = card.querySelector('[data-acao="baixar-csv"]');
    if (btnBaixarCsv) {
      const ltCsv = await registrarAnimacao(
        `lottie-csv-${buildId}`,
        "../lottie/buildDownload.json",
      );
      if (ltCsv) {
        btnBaixarCsv.addEventListener("mouseenter", () => {
          if (btnBaixarCsv.disabled) return;
          ltCsv.setDirection(1);
          ltCsv.play();
        });
        btnBaixarCsv.addEventListener("mouseleave", () => {
          if (btnBaixarCsv.disabled) return;
          ltCsv.setDirection(-1);
          ltCsv.play();
        });
      }
    }

    // 7. Botão Baixar JSON
    const btnBaixarJson = card.querySelector('[data-acao="baixar-json"]');
    if (btnBaixarJson) {
      const ltJson = await registrarAnimacao(
        `lottie-json-${buildId}`,
        "../lottie/buildDownload.json",
      );
      if (ltJson) {
        btnBaixarJson.addEventListener("mouseenter", () => {
          if (btnBaixarJson.disabled) return;
          ltJson.setDirection(1);
          ltJson.play();
        });
        btnBaixarJson.addEventListener("mouseleave", () => {
          if (btnBaixarJson.disabled) return;
          ltJson.setDirection(-1);
          ltJson.play();
        });
      }
    }

    // 8. Botão Deletar
    const btnDeletar = card.querySelector('[data-acao="deletar"]');
    if (btnDeletar) {
      const ltTrash = await registrarAnimacao(
        `lottie-trash-${buildId}`,
        "../lottie/buildTrash.json",
      );
      if (ltTrash) {
        btnDeletar.addEventListener("mouseenter", () => {
          if (btnDeletar.disabled) return;
          ltTrash.setDirection(1);
          ltTrash.play();
        });
        btnDeletar.addEventListener("mouseleave", () => {
          if (btnDeletar.disabled) return;
          ltTrash.setDirection(-1);
          ltTrash.play();
        });
      }
    }
  }

  function renderizarBuilds() {
    try {
      localStorage.setItem(CHAVE_PERFIL_LOCAL, JSON.stringify(builds));
      builds.forEach((build) => sincronizarRascunho(build));
    } catch { /* As ações da interface continuam disponíveis em memória. */ }
    fecharMenus();
    lista.innerHTML = "";
    vazio.hidden = builds.length > 0;
    atualizarQuota();

    builds.forEach((build) => {
      const cardCriado = criarCard(build);
      lista.appendChild(cardCriado);
      iniciarAnimacoesDoCard(cardCriado, build.id).catch((erro) =>
        console.warn("Não foi possível carregar os ícones do card:", erro));
    });
  }

  function criarCard(build) {
    const resultado = catalogo.length && build.componentes ? avaliarBuild(build,catalogo) : null;
    const progresso = resultado ? Math.round(resultado.preenchidos / resultado.total * 100) : build.progresso ?? calcularProgresso(build.pecas || {});
    const idHtml = htmlSeguro(build.id);
    const tituloSeguro = htmlSeguro(build.titulo);
    const status = resultado?.status || resolverStatus(build);
    const artigo = document.createElement("article");
    artigo.className = `build-card ${STATUS_CLASS[status]}`;
    if (build.travada) artigo.classList.add("locked");
    artigo.dataset.id = build.id;
    artigo.tabIndex = 0;
    artigo.setAttribute("aria-label", "Abrir " + build.titulo + (build.travada ? " (trancada)" : ""));
    artigo.addEventListener("keydown", (evento) => {
      if (evento.target !== artigo || !["Enter", " "].includes(evento.key)) return;
      evento.preventDefault();
      navegarPara("./configuracao-build.html?id=" + encodeURIComponent(build.id));
    });

    const textoVisibilidade =
      build.visibilidade === "publico" ? "Tornar privado" : "Tornar público";
    const textoTranca = build.travada ? "Destrancar build" : "Trancar build";

    // Lógica invertida: Se for público, exibe o cadeado; se for privado, exibe o public
    const isPublico = build.visibilidade === "publico";
    const displayLockVis = isPublico ? "" : 'style="display: none;"';
    const displayPublicVis = isPublico ? 'style="display: none;"' : "";

    artigo.innerHTML = `
      <div class="build-card-top">
        <div class="build-title-line">${indicadorBuild(resultado || {erros:status === "erro" ? ["Reabra a build para conferir as incompatibilidades."] : [],avisos:status === "atencao" ? ["Reabra a build para conferir os avisos."] : [],faltam:Object.entries(build.pecas || {}).filter(([,tem]) => !tem).map(([chave]) => ROTULOS_PECA[chave] || chave)},"build-details-" + build.id)}<h2 class="build-card-title font-1-m-b"></h2></div>
        <div class="build-menu-wrap">
          <button type="button" class="build-menu-trigger" aria-label="Abrir menu da build ${tituloSeguro}" aria-expanded="false" aria-haspopup="true">···</button>
          <div class="build-menu" role="menu">
            <button type="button" class="build-menu-item" data-acao="trancar" role="menuitem" aria-label="${textoTranca} de ${tituloSeguro}">
              <i id="lottie-lock-${idHtml}" class="lottie-build-page"></i>
              <span class="btn-text">${textoTranca}</span>
            </button>
            <span class="build-menu-divider"></span>
            <button type="button" class="build-menu-item" data-acao="visibilidade" role="menuitem" aria-label="${textoVisibilidade} de ${tituloSeguro}">
              <i id="lottie-lock-vis-${idHtml}" class="lottie-build-page" ${displayLockVis}></i>
              <i id="lottie-public-vis-${idHtml}" class="lottie-build-page" ${displayPublicVis}></i>
              <span class="btn-text">${textoVisibilidade}</span>
            </button>
            <button type="button" class="build-menu-item" data-acao="editar" role="menuitem" aria-label="Editar detalhes de ${tituloSeguro}">
              <i id="lottie-edit-${idHtml}" class="lottie-build-page"></i>Editar detalhes
            </button>
            <button type="button" class="build-menu-item" data-acao="duplicar" role="menuitem" aria-label="Duplicar build ${tituloSeguro}">
              <i id="lottie-clone-${idHtml}" class="lottie-build-page"></i>Duplicar build
            </button>
            <button type="button" class="build-menu-item" data-acao="copiar-link" role="menuitem" aria-label="Copiar link de ${tituloSeguro}">
              <i id="lottie-copy-${idHtml}" class="lottie-build-page"></i>Copiar link
            </button>
            <span class="build-menu-divider"></span>
            <button type="button" class="build-menu-item" data-acao="baixar-csv" role="menuitem" aria-label="Baixar build (CSV): ${tituloSeguro}">
              <i id="lottie-csv-${idHtml}" class="lottie-build-page"></i>Baixar build (CSV)
            </button>
            <button type="button" class="build-menu-item" data-acao="baixar-json" role="menuitem" aria-label="Baixar build (JSON): ${tituloSeguro}">
              <i id="lottie-json-${idHtml}" class="lottie-build-page"></i>Baixar build (JSON)
            </button>
            <span class="build-menu-divider"></span>
            <button type="button" class="build-menu-item danger-menu-item" data-acao="deletar" role="menuitem" aria-label="Deletar build ${tituloSeguro}" ${build.travada ? 'disabled data-disabled-reason="Destranque a build para deletar."' : ""}>
              <i id="lottie-trash-${idHtml}" class="lottie-build-page"></i>Deletar build
            </button>
          </div>
        </div>
      </div>
      <p class="build-card-desc font-2-xs"></p>
      <div class="build-card-meta">
        <p class="build-card-percent font-1-l" data-percent>${progresso}%</p>
        <div class="build-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progresso}" aria-label="Progresso da build">
          <div class="build-progress-fill" style="width: ${progresso}%"></div>
        </div>
        <div class="build-card-bottom">
          <span class="build-visibility ${isPublico ? "publico" : "privado"}">${isPublico ? "Pública" : "Privada"}</span>
          <time class="build-card-date font-2-xs"></time>
        </div>
      </div>
    `;

    const menuTrigger = artigo.querySelector(".build-menu-trigger");
    menuTrigger.dataset.buildTitle = build.titulo;

    const titulo = artigo.querySelector(".build-card-title");
    titulo.textContent = build.titulo;
    if (build.travada) {
      const cadeado = document.createElement("i");
      cadeado.className = "fa-solid fa-lock build-card-lock";
      cadeado.setAttribute("aria-hidden", "true");
      titulo.append(cadeado);
    }
    artigo.querySelector(".build-card-desc").textContent = build.descricao;
    artigo.querySelector(".build-card-date").textContent = formatarDataHora(
      build.criadoEm,
    );
    artigo.querySelector(".build-card-date").dateTime = build.criadoEm;
    iniciarIndicadores(artigo);

    if (build.travada) {
      artigo.querySelector('[data-acao="visibilidade"]').disabled = true;
      artigo.querySelector('[data-acao="editar"]').disabled = true;
    }

    if (build.visibilidade !== "publico") {
      artigo.querySelector('[data-acao="copiar-link"]').disabled = true;
    }

    if (builds.length >= LIMITE_BUILDS) {
      artigo.querySelector('[data-acao="duplicar"]').disabled = true;
    }

    return artigo;
  }

  function buscarBuild(id) {
    return builds.find((item) => item.id === id);
  }

  function slugify(texto) {
    return texto
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");
  }

  function baixarArquivo(nome, conteudo, tipo) {
    const blob = new Blob([conteudo], { type: tipo });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = nome;
    link.setAttribute("aria-label", "Baixar arquivo " + nome);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function montarCsv(build) {
    const linhas = [
      ["campo", "valor"],
      ["id", build.id],
      ["titulo", build.titulo],
      ["descricao", build.descricao],
      ["visibilidade", build.visibilidade],
      ["travada", build.travada],
      ["status", resolverStatus(build)],
      ["progresso", `${build.progresso ?? calcularProgresso(build.pecas)}%`],
      ["criadoEm", build.criadoEm],
      [],
      ["peca", "na_build"],
    ];

    Object.entries(build.pecas).forEach(([chave, valor]) => {
      linhas.push([ROTULOS_PECA[chave] || chave, valor ? "sim" : "nao"]);
    });

    return linhas
      .map((linha) =>
        linha
          .map((celula) => `"${String(celula).replace(/"/g, '""')}"`)
          .join(","),
      )
      .join("\n");
  }

  function abrirModal(modal) {
    modal.classList.add("open");
  }

  function fecharModal(modal) {
    modal.classList.remove("open");
  }

  lista.addEventListener("click", async (evento) => {
    if (evento.target.closest(".build-indicator")) return;
    if (!evento.target.closest(".build-menu-wrap")) {
      const selecionado = evento.target.closest(".build-card");
      if (selecionado) {
        navegarPara("./configuracao-build.html?id=" + encodeURIComponent(selecionado.dataset.id));
        return;
      }
    }
    const trigger = evento.target.closest(".build-menu-trigger");
    if (trigger) {
      const wrap = trigger.closest(".build-menu-wrap");
      const jaAberto = wrap.classList.contains("open");
      fecharMenus();
      if (!jaAberto) {
        wrap.classList.add("open");
        trigger.setAttribute("aria-expanded", "true");
        trigger.setAttribute("aria-label", "Fechar menu da build " + trigger.dataset.buildTitle);
      }
      return;
    }

    const botao = evento.target.closest("[data-acao]");
    if (!botao || botao.disabled) return;

    const card = botao.closest(".build-card");
    const build = buscarBuild(card.dataset.id);
    if (!build) return;

    const acao = botao.dataset.acao;
    fecharMenus();

    if (acao === "trancar") {
      build.travada = !build.travada;
      try { sincronizarRascunho(build, { travada: build.travada }); }
      catch { showToast("Não foi possível persistir a tranca neste navegador."); }
      renderizarBuilds();
      showToast(build.travada ? "Build trancada." : "Build destrancada.");
      return;
    }

    if (acao === "visibilidade") {
      if (build.travada) {
        showToast("Build trancada: a visibilidade não pode ser alterada.");
        return;
      }
      build.visibilidade =
        build.visibilidade === "publico" ? "privado" : "publico";
      try { sincronizarRascunho(build, { visibilidade: build.visibilidade }); }
      catch { showToast("Não foi possível persistir a visibilidade neste navegador."); }
      renderizarBuilds();
      showToast(
        build.visibilidade === "publico"
          ? "Build pública. O link pode ser compartilhado."
          : "Build privada. O link não pode ser compartilhado.",
      );
      return;
    }

    if (acao === "editar") {
      if (build.travada) {
        showToast("Build trancada: os detalhes não podem ser editados.");
        return;
      }
      idEdicao = build.id;
      inputTitulo.value = build.titulo;
      inputDescricao.value = build.descricao;
      abrirModal(modalEditar);
      return;
    }

    if (acao === "duplicar") {
      if (builds.length >= LIMITE_BUILDS) {
        showToast("Limite de 3 builds atingido.");
        return;
      }
      const copia = structuredClone(build);
      copia.id = `build-${Date.now()}`;
      copia.titulo = `${build.titulo} (cópia)`;
      copia.travada = false;
      copia.criadoEm = new Date().toISOString();
      builds.push(copia);
      renderizarBuilds();
      showToast("Build duplicada.");
      return;
    }

    if (acao === "copiar-link") {
      if (build.visibilidade !== "publico") {
        showToast("Builds privadas não podem ser compartilhadas.");
        return;
      }
      const url = linkCompartilhado(build);
      try {
        await navigator.clipboard.writeText(url);
        showToast("Link copiado.");
      } catch {
        showToast("Não foi possível copiar o link.");
      }
      return;
    }

    if (acao === "baixar-json") {
      baixarArquivo(
        `${slugify(build.titulo) || "build"}.json`,
        JSON.stringify(build, null, 2),
        "application/json",
      );
      showToast("Download do JSON iniciado.");
      return;
    }

    if (acao === "baixar-csv") {
      baixarArquivo(
        `${slugify(build.titulo) || "build"}.csv`,
        montarCsv(build),
        "text/csv;charset=utf-8",
      );
      showToast("Download do CSV iniciado.");
      return;
    }

    if (acao === "deletar") {
      if (build.travada) {
        showToast("Destranque a build para deletar.");
        return;
      }
      idExclusao = build.id;
      abrirModal(modalDeletar);
    }
  });

  document.addEventListener("click", (evento) => {
    if (!evento.target.closest(".build-menu-wrap")) {
      fecharMenus();
    }
  });

  btnCriar.addEventListener("click", () => {
    if (builds.length >= LIMITE_BUILDS) return;
    navegarPara("./configuracao-build.html");
  });

  btnImportar.addEventListener("click", () => {
    if (builds.length >= LIMITE_BUILDS) { showToast("Limite de 3 builds atingido."); return; }
    showToast("A importação de builds depende do backend.");
  });

  document
    .getElementById("cancel-build-edit")
    .addEventListener("click", () => {
      idEdicao = null;
      fecharModal(modalEditar);
    });

  document
    .getElementById("save-build-edit")
    .addEventListener("click", () => {
      const build = buscarBuild(idEdicao);
      if (!build || build.travada) {
        fecharModal(modalEditar);
        return;
      }
      const titulo = inputTitulo.value.trim();
      if (!titulo) {
        showToast("O título não pode ficar vazio.");
        return;
      }
      build.titulo = titulo;
      build.descricao = inputDescricao.value.trim();
      try { sincronizarRascunho(build, { titulo: build.titulo, descricao: build.descricao }); }
      catch { showToast("Não foi possível persistir os detalhes neste navegador."); }
      idEdicao = null;
      fecharModal(modalEditar);
      renderizarBuilds();
      showToast("Detalhes atualizados.");
    });

  document
    .getElementById("cancel-build-delete")
    .addEventListener("click", () => {
      idExclusao = null;
      fecharModal(modalDeletar);
    });

  document
    .getElementById("confirm-build-delete")
    .addEventListener("click", () => {
      const build = buscarBuild(idExclusao);
      if (!build || build.travada) {
        idExclusao = null;
        fecharModal(modalDeletar);
        showToast("Destranque a build para deletar.");
        return;
      }
      builds = builds.filter((item) => item.id !== idExclusao);
      idExclusao = null;
      fecharModal(modalDeletar);
      renderizarBuilds();
      showToast("Build removida.");
    });

  modalEditar.addEventListener("click", (evento) => {
    if (evento.target === modalEditar) fecharModal(modalEditar);
  });

  modalDeletar.addEventListener("click", (evento) => {
    if (evento.target === modalDeletar) fecharModal(modalDeletar);
  });

  renderizarBuilds();
});
