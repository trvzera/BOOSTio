import "../header.js";
import "../auth/auth.js";
import { listarBuilds, criarBuildManual, atualizarBuild, duplicarBuild, excluirBuild, definirSetupAtual, LIMITE_BUILDS, verificarEspacoBuild } from "../api/build/builds.js";
import { carregarCatalogoConta, buildDaConta, estadoParaConta, linkBuildConta } from "../build/conta.js";
import { htmlSeguro as h, moeda } from "../build/catalogo.js";
import { avaliarBuild } from "../build/compatibilidade.js";
import { abrirBenchmark, abrirDialogoBuild, motivoBenchmark } from "../build/acoes-build.js";
import { abrirComparacao } from "../build/comparacao.js";
import { abrirMelhorias } from "../build/melhorias.js";
import { exportarCsv, exportarJson, importarBuild } from "../build/arquivos.js";
import { planejamentoLocal, salvarPlanejamento } from "../build/planejamento.js";
import { formatarDataHora } from "../utils/formatarData.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";
import { indicadorBuild, iniciarIndicadores } from "../build/indicador.js";
import { navegarPara } from "../components/page-loading.js";

document.addEventListener("DOMContentLoaded", async () => {
  const lista = document.querySelector("#builds-account-list");
  const status = document.querySelector("#builds-account-status");
  const toast = document.querySelector("#toast");
  const modalEditar = document.querySelector("#edit-build-modal");
  const modalExcluir = document.querySelector("#delete-build-modal");
  const inputTitulo = document.querySelector("#edit-title");
  const inputDescricao = document.querySelector("#edit-description");
  let salvas = [], catalogo = [], idEdicao = null, idExclusao = null;
  let carregadas = false, criando = false;
  const lotado = () => salvas.length >= LIMITE_BUILDS;
  for (const id of ["#btn-create-build","#btn-import-build"]) {
    const botao = document.querySelector(id);
    botao.disabled = true;
    botao.dataset.disabledReason = "Aguarde o carregamento das suas builds.";
  }

  function avisar(mensagem) {
    document.querySelector("#toast-text").textContent = mensagem;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3000);
  }
  const encontrar = id => salvas.find(item => item.id === id);
  const local = dados => buildDaConta(dados);
  const url = dados => "./configuracao-build.html?" + new URLSearchParams({build_id:dados.id});

  function baixar(nome, conteudo, tipo) {
    const endereco = URL.createObjectURL(new Blob([conteudo], {type:tipo}));
    const link = document.createElement("a");
    link.href = endereco; link.download = nome; document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(endereco), 1000);
  }

  async function carregar() {
    try {
      const [resposta, pecas] = await Promise.all([listarBuilds(), carregarCatalogoConta()]);
      salvas = resposta.builds || []; catalogo = pecas; carregadas = true;
      renderizar();
    } catch (erro) { status.hidden = false; status.textContent = erro.message; }
  }

  function card(dados) {
    const build = local(dados), avaliacao = avaliarBuild(build, catalogo);
    const progresso = Math.round(avaliacao.preenchidos / avaliacao.total * 100);
    const trancada = build.travada, setup = Boolean(dados.estado?.setupAtual);
    const classe = avaliacao.erros.length ? "error" : avaliacao.avisos.length ? "warning" : progresso === 100 ? "complete" : "incomplete";
    const icones = {benchmark:"magic",melhorias:"magnifying","setup-atual":"circledot",trancar:"lock",visibilidade:"visibility",editar:"pencil",duplicar:"clone","copiar-link":"copy","baixar-csv":"download","baixar-json":"download",deletar:"trash"};
    const opcao = (acao, texto, desabilitada = false, motivo = "") => `<button type="button" class="build-menu-item${acao === "deletar" ? " danger-menu-item" : ""}" data-acao="${acao}" aria-label="${h(texto)}: ${h(build.titulo)}" ${desabilitada ? `disabled data-disabled-reason="${h(motivo || (trancada ? "Destranque a build para usar esta opção." : "Torne a build pública para compartilhar o link."))}"` : ""}>${iconeAnimado(icones[acao],"internal",{invertido:acao === "setup-atual" && setup})}<span>${h(texto)}</span></button>`;
    const menuId = "build-options-" + encodeURIComponent(build.id);
    return `<article class="build-card build-account-card ${classe} ${trancada ? "locked" : ""}" data-id="${h(build.id)}">
      <div class="build-card-top"><div class="build-title-line">${indicadorBuild(avaliacao,"compatibility-" + encodeURIComponent(build.id))}<h2 class="build-card-title font-1-m-b"><a href="${url(build)}" aria-label="Abrir configuração de ${h(build.titulo)}">${h(build.titulo)}</a></h2>${trancada ? '<i class="fa-solid fa-lock build-card-lock" aria-hidden="true"></i>' : ""}${setup ? '<span class="build-card-current">Setup atual</span>' : ""}</div>
      <div class="build-menu-wrap"><button type="button" class="build-menu-trigger" aria-label="Abrir menu da build ${h(build.titulo)}" aria-expanded="false" aria-controls="${menuId}">${iconeAnimado("dots")}</button><div class="build-menu" id="${menuId}" role="group" aria-label="Opções da build ${h(build.titulo)}" aria-hidden="true" inert>
        ${opcao("benchmark","Testar build",Boolean(motivoBenchmark(build,catalogo)),motivoBenchmark(build,catalogo))}
        ${opcao("melhorias","Buscar melhorias",trancada)}
        ${opcao("setup-atual",setup ? "Remover como setup atual" : "Definir como setup atual")}
        <span class="build-menu-divider"></span>${opcao("trancar",trancada ? "Destrancar build" : "Trancar build")}
        ${opcao("visibilidade",build.visibilidade === "publico" ? "Tornar privado" : "Tornar público",trancada)}
        ${opcao("editar","Editar detalhes",trancada)}${opcao("duplicar","Duplicar build",lotado(),"Limite de três builds atingido. Exclua uma para duplicar.")}
        ${opcao("copiar-link","Copiar link",build.visibilidade !== "publico")}
        <span class="build-menu-divider"></span>${opcao("baixar-csv","Baixar build (CSV)")}${opcao("baixar-json","Baixar build (JSON)")}
        <span class="build-menu-divider"></span>${opcao("deletar","Deletar build",trancada)}
      </div></div></div>
      <p class="build-card-desc font-2-xs">${h(build.descricao || `${dados.componentes.length} peças · ${moeda(dados.preco_total)}`)}</p>
      <div class="build-card-meta"><p class="build-card-percent font-1-l">${progresso}%</p><div class="build-progress" role="progressbar" aria-label="Preenchimento de ${h(build.titulo)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progresso}"><div class="build-progress-fill" style="width:${progresso}%"></div></div>
      <div class="build-card-bottom"><span class="build-visibility ${build.visibilidade}">${build.visibilidade === "publico" ? "Pública" : "Privada"}</span><time class="build-card-date font-2-xs" datetime="${h(dados.criado_em)}">${h(formatarDataHora(dados.criado_em))}</time></div></div></article>`;
  }

  function renderizar() {
    status.hidden = salvas.length > 0;
    status.textContent = salvas.length ? "" : "Você ainda não tem builds salvas na conta.";
    lista.innerHTML = salvas.map(card).join("");
    document.querySelector("#quota-count").textContent = `${salvas.length} / ${LIMITE_BUILDS}`;
    document.querySelector("#quota-progress").setAttribute("aria-valuenow",String(Math.min(LIMITE_BUILDS,salvas.length)));
    document.querySelector("#quota-fill").style.width = `${Math.min(100,salvas.length / LIMITE_BUILDS * 100)}%`;
    document.querySelector("#quota-help").textContent = lotado() ? "Limite atingido. Exclua uma build para liberar espaço." : "Até três builds salvas na sua conta";
    for (const id of ["#btn-create-build","#btn-import-build"]) {
      const botao = document.querySelector(id);
      botao.disabled = lotado();
      botao.dataset.disabledReason = "Limite de três builds atingido. Exclua uma para liberar espaço.";
    }
    document.querySelector("#btn-compare-builds").disabled = salvas.length < 2;
    iniciarIcones(lista);
    iniciarIndicadores(lista);
  }
  async function atualizar(id, estado) { await atualizarBuild(id, estado); await carregar(); }

  function alternarMenu(wrap, aberto) {
    wrap.classList.toggle("open",aberto);
    const botao = wrap.querySelector(".build-menu-trigger"), menu = wrap.querySelector(".build-menu");
    botao.setAttribute("aria-expanded",String(aberto));
    menu.inert = !aberto; menu.setAttribute("aria-hidden",String(!aberto));
    if (typeof menu.showPopover === "function") {
      menu.popover = "manual";
      if (aberto) {
        menu.showPopover();
        const r = botao.getBoundingClientRect();
        const topo = Math.min(r.bottom + 8,innerHeight - 172);
        menu.style.top = Math.max(12,topo) + "px";
        menu.style.left = Math.max(12,Math.min(r.right - menu.offsetWidth,innerWidth - menu.offsetWidth - 12)) + "px";
        menu.style.maxHeight = Math.max(160,innerHeight - topo - 12) + "px";
      } else if (menu.matches(":popover-open")) menu.hidePopover();
    }
    if (aberto) iniciarIcones(menu);
  }

  lista.addEventListener("click", async evento => {
    const trigger = evento.target.closest(".build-menu-trigger");
    if (trigger) {
      const wrap = trigger.closest(".build-menu-wrap"), abrir = !wrap.classList.contains("open");
      lista.querySelectorAll(".build-menu-wrap.open").forEach(item => alternarMenu(item,false));
      alternarMenu(wrap,abrir); return;
    }
    const botao = evento.target.closest("[data-acao]");
    if (!botao || botao.disabled) {
      if (!evento.target.closest("a,.build-menu-wrap,.build-indicator")) {
        const artigo = evento.target.closest(".build-account-card");
        if (artigo) navegarPara(url(encontrar(artigo.dataset.id)));
      }
      return;
    }
    const dados = encontrar(botao.closest(".build-card").dataset.id);
    if (!dados) return;
    const build = local(dados), acao = botao.dataset.acao;
    const wrap = botao.closest(".build-menu-wrap");
    alternarMenu(wrap,false); wrap.querySelector(".build-menu-trigger").focus({preventScroll:true});
    try {
      if (acao === "benchmark") abrirBenchmark(build,catalogo);
      else if (acao === "melhorias") abrirMelhorias(build,catalogo,async proxima => {
        await atualizar(build.id,estadoParaConta(proxima));
        avisar("Melhorias salvas na conta.");
      });
      else if (acao === "setup-atual") {
        const remover = Boolean(dados.estado?.setupAtual);
        await definirSetupAtual(build.id);
        salvarPlanejamento({setupAtualId:remover ? null : build.id});
        await carregar();
      } else if (acao === "trancar") {
        if (build.travada) await atualizar(build.id,{travada:false});
        else { build.travada = true; await atualizar(build.id,estadoParaConta(build)); }
      } else if (acao === "visibilidade") {
        build.visibilidade = build.visibilidade === "publico" ? "privado" : "publico";
        await atualizar(build.id,estadoParaConta(build));
      } else if (acao === "editar") {
        idEdicao = build.id; inputTitulo.value = build.titulo; inputDescricao.value = build.descricao;
        modalEditar.classList.add("open");
      } else if (acao === "duplicar") {
        await duplicarBuild(build.id); await carregar(); avisar("Build duplicada.");
      } else if (acao === "copiar-link") {
        await navigator.clipboard.writeText(linkBuildConta(build.id)); avisar("Link copiado.");
      } else if (acao === "baixar-json") baixar("build-" + build.id + ".json",exportarJson(build),"application/json");
      else if (acao === "baixar-csv") baixar("build-" + build.id + ".csv",exportarCsv(build,catalogo),"text/csv");
      else if (acao === "deletar") { idExclusao = build.id; modalExcluir.classList.add("open"); }
    } catch (erro) { avisar(erro.message); }
  });
  lista.addEventListener("keydown", evento => {
    if (!["Enter"," "].includes(evento.key) || !evento.target.matches(".build-account-card")) return;
    evento.preventDefault(); navegarPara(url(encontrar(evento.target.dataset.id)));
  });
  document.addEventListener("click", evento => {
    if (!lista.contains(evento.target)) lista.querySelectorAll(".build-menu-wrap.open").forEach(item => alternarMenu(item,false));
  });
  const fecharMenus = () => lista.querySelectorAll(".build-menu-wrap.open").forEach(item => alternarMenu(item,false));
  window.addEventListener("resize",fecharMenus);
  window.addEventListener("scroll",fecharMenus,{passive:true});
  document.addEventListener("keydown", evento => {
    if (evento.key !== "Escape") return;
    lista.querySelectorAll(".build-menu-wrap.open").forEach(wrap => {
      alternarMenu(wrap,false); wrap.querySelector(".build-menu-trigger").focus();
    });
  });

  document.querySelector("#btn-create-build").onclick = async () => {
    if (!carregadas || lotado() || criando) return;
    try { await verificarEspacoBuild(); } catch (erro) { avisar(erro.message); return; }
    const dialogo = abrirDialogoBuild("Como você quer criar sua build?",'<div class="build-create-options"><a class="build-create-option build-create-option-primary" href="./formulario.html" aria-label="Criar build pelo formulário inteligente">' + iconeAnimado("handsparkle") + '<strong>Formulário inteligente</strong><span>Informe objetivo e orçamento para gerar a build.</span></a><button type="button" class="build-create-option" data-criar="manual" aria-label="Criar build manualmente">' + iconeAnimado("normalhand") + '<strong>Montagem manual</strong><span>Escolha peça por peça do catálogo.</span></button></div>');
    dialogo.querySelector('[data-criar="manual"]').onclick = async evento => {
      if (criando) return;
      criando = true; evento.currentTarget.disabled = true;
      try {
        await verificarEspacoBuild();
        const {build} = await criarBuildManual(estadoParaConta({titulo:"Minha build",descricao:"",visibilidade:"privado",travada:false,incluirPerifericos:false,incluirRede:false,rede:{},componentes:{}}));
        navegarPara(url(build));
      } catch (erro) { avisar(erro.message); criando = false; dialogo.close(); await carregar(); }
    };
  };
  document.querySelector("#btn-import-build").onclick = () => {
    if (!carregadas || lotado() || criando) return;
    const dialogo = abrirDialogoBuild("Importar build",'<p class="planning-help">Selecione um JSON ou CSV de build (até 1 MB).</p><input type="file" id="build-import-file" accept=".json,.csv" aria-label="Arquivo da build"><p id="build-import-status" role="status"></p><button type="button" class="btn-primary" id="build-import-confirm" aria-label="Importar build selecionada" disabled>Importar build</button>');
    let candidata;
    const feedback = dialogo.querySelector("#build-import-status"), confirmar = dialogo.querySelector("#build-import-confirm");
    dialogo.querySelector("#build-import-file").onchange = async evento => {
      try {
        const arquivo = evento.target.files[0];
        candidata = importarBuild(await arquivo.text(),arquivo.name.split(".").at(-1),catalogo);
        feedback.textContent = candidata.titulo + " · arquivo validado"; confirmar.disabled = false;
      } catch (erro) { candidata = null; confirmar.disabled = true; feedback.textContent = erro.message; }
    };
    confirmar.onclick = async () => {
      if (criando || !candidata) return;
      criando = true; confirmar.disabled = true;
      try { await verificarEspacoBuild(); await criarBuildManual(estadoParaConta(candidata)); dialogo.close(); await carregar(); avisar("Build importada na conta."); }
      catch (erro) { feedback.textContent = erro.message; }
      finally { criando = false; confirmar.disabled = !candidata; }
    };
  };
  document.querySelector("#btn-compare-builds").onclick = () => {
    try { abrirComparacao(salvas.map(local),catalogo); } catch (erro) { avisar(erro.message); }
  };
  document.querySelector("#cancel-build-edit").onclick = () => { idEdicao = null; modalEditar.classList.remove("open"); };
  document.querySelector("#save-build-edit").onclick = async () => {
    const dados = encontrar(idEdicao);
    if (!dados) return;
    const build = local(dados);
    build.titulo = inputTitulo.value.trim(); build.descricao = inputDescricao.value.trim();
    try { await atualizar(build.id,estadoParaConta(build)); modalEditar.classList.remove("open"); idEdicao = null; avisar("Detalhes atualizados."); }
    catch (erro) { avisar(erro.message); }
  };
  document.querySelector("#cancel-build-delete").onclick = () => { idExclusao = null; modalExcluir.classList.remove("open"); };
  document.querySelector("#confirm-build-delete").onclick = async () => {
    try {
      await excluirBuild(idExclusao);
      if (planejamentoLocal().setupAtualId === idExclusao) salvarPlanejamento({setupAtualId:null});
      idExclusao = null; modalExcluir.classList.remove("open"); await carregar(); avisar("Build removida.");
    } catch (erro) { avisar(erro.message); }
  };
  for (const modal of [modalEditar,modalExcluir]) modal.addEventListener("click",evento => { if (evento.target === modal) modal.classList.remove("open"); });
  iniciarIcones();
  await carregar();
  const parametros = new URLSearchParams(location.search);
  if (parametros.has("aviso")) avisar(parametros.get("aviso"));
  if (parametros.has("criar") && carregadas) {
    if (lotado()) avisar("Você atingiu o limite de três builds. Exclua uma para liberar espaço.");
    else document.querySelector("#btn-create-build").click();
  }
});
