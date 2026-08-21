import "../header.js";
import "../auth/auth.js";
import { registrarAnimacao } from "../components/lottie-controller.js";
import { formatarDataHora } from "../utils/formatarData.js";

const LIMITE_BUILDS = 3;

const STATUS_LABEL = {
  incompleta: "Incompleta",
  completa: "Completa",
  erro: "Com erro",
  atencao: "Com atenção",
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

document.addEventListener("DOMContentLoaded", () => {
  const lista = document.getElementById("builds-lista");
  const vazio = document.getElementById("builds-vazio");
  const quotaCount = document.getElementById("quota-count");
  const quotaFill = document.getElementById("quota-fill");
  const btnCriar = document.getElementById("btn-criar-build");
  const btnImportar = document.getElementById("btn-importar-build");
  const toast = document.getElementById("toast");
  const toastText = document.getElementById("toast-text");

  const modalEditar = document.getElementById("editar-build-modal");
  const inputTitulo = document.getElementById("editar-titulo");
  const inputDescricao = document.getElementById("editar-descricao");
  const modalDeletar = document.getElementById("deletar-build-modal");

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
    return calcularProgresso(build.pecas) === 100 ? "completa" : "incompleta";
  }

  function atualizarQuota() {
    const usadas = builds.length;
    quotaCount.textContent = `${usadas}/${LIMITE_BUILDS}`;
    quotaFill.style.width = `${(usadas / LIMITE_BUILDS) * 100}%`;
    btnCriar.disabled = usadas >= LIMITE_BUILDS;
  }

  function fecharMenus() {
    lista.querySelectorAll(".build-menu-wrap.aberto").forEach((wrap) => {
      wrap.classList.remove("aberto");
      const trigger = wrap.querySelector(".build-menu-trigger");
      if (trigger) trigger.setAttribute("aria-expanded", "false");
    });
  }

  // Inicialização manual com validação de botões desabilitados
  async function iniciarAnimacoesDoCard(card, buildId) {
    // 1. Botão Trancar
    const btnTrancar = card.querySelector('[data-acao="trancar"]');
    if (btnTrancar) {
      const ltLock = await registrarAnimacao(
        `lt-lock-${buildId}`,
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
        `lt-lock-vis-${buildId}`,
        "../lottie/buildLock.json",
      );
      const ltVisPublic = await registrarAnimacao(
        `lt-public-vis-${buildId}`,
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
        `lt-edit-${buildId}`,
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
        `lt-clone-${buildId}`,
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
        `lt-copy-${buildId}`,
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
        `lt-csv-${buildId}`,
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
        `lt-json-${buildId}`,
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
        `lt-trash-${buildId}`,
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
    fecharMenus();
    lista.innerHTML = "";
    vazio.hidden = builds.length > 0;
    atualizarQuota();

    builds.forEach((build) => {
      const cardCriado = criarCard(build);
      lista.appendChild(cardCriado);
      iniciarAnimacoesDoCard(cardCriado, build.id);
    });
  }

  function criarCard(build) {
    const progresso = calcularProgresso(build.pecas);
    const status = resolverStatus(build);
    const artigo = document.createElement("article");
    artigo.className = `build-card ${status}`;
    if (build.travada) artigo.classList.add("travada");
    artigo.dataset.id = build.id;

    const textoVisibilidade =
      build.visibilidade === "publico" ? "Tornar privado" : "Tornar público";
    const textoTranca = build.travada ? "Destrancar build" : "Trancar build";

    // Lógica invertida: Se for público, exibe o cadeado; se for privado, exibe o public
    const isPublico = build.visibilidade === "publico";
    const displayLockVis = isPublico ? "" : 'style="display: none;"';
    const displayPublicVis = isPublico ? 'style="display: none;"' : "";

    artigo.innerHTML = `
      <div class="build-card-top">
        <h2 class="build-card-title font-1-m-b"></h2>
        <div class="build-menu-wrap">
          <button type="button" class="build-menu-trigger" aria-label="Abrir menu da build" aria-expanded="false" aria-haspopup="true">···</button>
          <div class="build-menu" role="menu">
            <button type="button" class="build-menu-item" data-acao="trancar" role="menuitem">
              <i id="lt-lock-${build.id}" class="lottie-build-page"></i>
              <span class="btn-text">${textoTranca}</span>
            </button>
            <span class="build-menu-divider"></span>
            <button type="button" class="build-menu-item" data-acao="visibilidade" role="menuitem">
              <i id="lt-lock-vis-${build.id}" class="lottie-build-page" ${displayLockVis}></i>
              <i id="lt-public-vis-${build.id}" class="lottie-build-page" ${displayPublicVis}></i>
              <span class="btn-text">${textoVisibilidade}</span>
            </button>
            <button type="button" class="build-menu-item" data-acao="editar" role="menuitem">
              <i id="lt-edit-${build.id}" class="lottie-build-page"></i>Editar detalhes
            </button>
            <button type="button" class="build-menu-item" data-acao="duplicar" role="menuitem">
              <i id="lt-clone-${build.id}" class="lottie-build-page"></i>Duplicar build
            </button>
            <button type="button" class="build-menu-item" data-acao="copiar-link" role="menuitem">
              <i id="lt-copy-${build.id}" class="lottie-build-page"></i>Copiar link
            </button>
            <span class="build-menu-divider"></span>
            <button type="button" class="build-menu-item" data-acao="baixar-csv" role="menuitem">
              <i id="lt-csv-${build.id}" class="lottie-build-page"></i>Baixar build (CSV)
            </button>
            <button type="button" class="build-menu-item" data-acao="baixar-json" role="menuitem">
              <i id="lt-json-${build.id}" class="lottie-build-page"></i>Baixar build (JSON)
            </button>
            <span class="build-menu-divider"></span>
            <button type="button" class="build-menu-item perigo" data-acao="deletar" role="menuitem">
              <i id="lt-trash-${build.id}" class="lottie-build-page"></i>Deletar build
            </button>
          </div>
        </div>
      </div>
      <p class="build-card-desc font-2-xs"></p>
      <p class="build-card-percent font-1-l" data-percent>${progresso}%</p>
      <div class="build-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progresso}" aria-label="Progresso da build">
        <div class="build-progress-fill" style="width: ${progresso}%"></div>
      </div>
      <div class="build-card-bottom">
        <span class="build-status ${status} font-1-xs">${STATUS_LABEL[status]}</span>
        <time class="build-card-date font-2-xs" datetime="${build.criadoEm}"></time>
      </div>
    `;

    artigo.querySelector(".build-card-title").textContent = build.titulo;
    artigo.querySelector(".build-card-desc").textContent = build.descricao;
    artigo.querySelector(".build-card-date").textContent = formatarDataHora(
      build.criadoEm,
    );

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
      ["progresso", `${calcularProgresso(build.pecas)}%`],
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
    const trigger = evento.target.closest(".build-menu-trigger");
    if (trigger) {
      const wrap = trigger.closest(".build-menu-wrap");
      const jaAberto = wrap.classList.contains("aberto");
      fecharMenus();
      if (!jaAberto) {
        wrap.classList.add("aberto");
        trigger.setAttribute("aria-expanded", "true");
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
      const url = `${window.location.origin}${window.location.pathname}?id=${encodeURIComponent(build.id)}`;
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
    showToast("A criação de builds depende do backend.");
  });

  btnImportar.addEventListener("click", () => {
    showToast("A importação de builds depende do backend.");
  });

  document
    .getElementById("cancelar-editar-build")
    .addEventListener("click", () => {
      idEdicao = null;
      fecharModal(modalEditar);
    });

  document
    .getElementById("salvar-editar-build")
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
      idEdicao = null;
      fecharModal(modalEditar);
      renderizarBuilds();
      showToast("Detalhes atualizados.");
    });

  document
    .getElementById("cancelar-deletar-build")
    .addEventListener("click", () => {
      idExclusao = null;
      fecharModal(modalDeletar);
    });

  document
    .getElementById("confirmar-deletar-build")
    .addEventListener("click", () => {
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
