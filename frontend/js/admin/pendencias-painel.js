

import { listarPendencias, detalharPendencia, aceitarPendencia, rejeitarPendencia, descartarCandidato, enviarPendenciasParaIA, listarIdsParaIA } from "../api/admin/pendencias.js";
import { processarEnvioIA } from "./envio-ia.js";
import {
  rotuloLoja, rotuloSituacao, rotuloCategoria, formatarFaixaPreco, linkSeguro,
  candidatoSelecionavel, descreverCandidato, textoRestricoes,
} from "./pendencias-apresentacao.js";

const elemento = (tag, classe, texto) => {
  const no = document.createElement(tag);
  if (classe) no.className = classe;
  if (texto !== undefined) no.textContent = texto;
  return no;
};

function opcoes(select, itens, rotulo, todas) {
  select.replaceChildren(new Option(todas, ""), ...itens.map(valor => new Option(rotulo(valor), valor)));
}

export function iniciarPendencias(raiz) {
  const filtros = raiz.querySelector("[data-pendencias-filtros]");
  const lista = raiz.querySelector("[data-pendencias-lista]");
  const detalhe = raiz.querySelector("[data-pendencias-detalhe]");
  const resumo = raiz.querySelector("[data-pendencias-resumo]");
  const status = raiz.querySelector("[data-pendencias-status]");
  const maisBotao = raiz.querySelector("[data-pendencias-mais]");
  const lote = raiz.querySelector("[data-pendencias-lote]");
  const todas = raiz.querySelector("[data-pendencias-todas]");
  const enviarIA = raiz.querySelector("[data-pendencias-enviar-ia]");
  const vinte = raiz.querySelector("[data-pendencias-vinte]");
  const pararEnvio = raiz.querySelector("[data-pendencias-parar]");
  const decidirIA = raiz.querySelector("[data-pendencias-ia-decidir]");
  const selects = {
    status: filtros.elements.status, loja: filtros.elements.loja, categoria: filtros.elements.categoria,
  };
  let proximo = null, selecionada = null, requisicao = 0;

  const avisar = (mensagem, erro = false) => {
    status.textContent = mensagem;
    status.dataset.estado = erro ? "erro" : "ok";
  };
  const filtrosAtuais = () => ({status: selects.status.value, loja: selects.loja.value, categoria: selects.categoria.value});

  function cartao(pendencia) {
    const item = elemento("li", "admin-pending-item");
    if (pendencia.id === selecionada) item.dataset.selected = "";
    const cabecalho = elemento("div", "admin-pending-head");
    const marcar = elemento("input", "admin-pending-check");
    marcar.type = "checkbox"; marcar.value = String(pendencia.id);
    marcar.setAttribute("aria-label", `Selecionar para a IA: ${pendencia.titulo}`);
    marcar.checked = todasSelecionadas;
    marcar.addEventListener("change", () => { todasSelecionadas = false; atualizarLote(); });
    cabecalho.append(marcar);
    cabecalho.append(elemento("span", "admin-badge", rotuloLoja(pendencia.loja)),
      elemento("span", "admin-badge admin-badge-muted", rotuloCategoria(pendencia.categoria)));
    if (pendencia.sugestao_ia) {
      cabecalho.append(elemento("span", "admin-badge admin-badge-ia", textoSugestao(pendencia.sugestao_ia)));
    }
    const titulo = elemento("h3", "admin-pending-title font-1-m", pendencia.titulo);
    const meta = elemento("p", "admin-pending-meta font-2-s",
      `${formatarFaixaPreco(pendencia.preco)} · ${pendencia.total_candidatos} candidato(s) · ${rotuloSituacao(pendencia.status)}`);
    const botao = elemento("button", "btn-ghost admin-pending-open", "Analisar");
    botao.type = "button";
    botao.setAttribute("aria-label", `Analisar pendência: ${pendencia.titulo}`);
    botao.addEventListener("click", () => abrir(pendencia.id));
    item.append(cabecalho, titulo, meta, botao);
    return item;
  }

  const marcadas = () => [...lista.querySelectorAll(".admin-pending-check:checked")];


  let todasSelecionadas = false, idsTodas = [];
  const TAMANHO_SELECAO = 20;

  function atualizarLote() {
    const caixas = lista.querySelectorAll(".admin-pending-check");
    const marcadasAgora = marcadas().length;
    const n = todasSelecionadas ? idsTodas.length : marcadasAgora;
    lote.hidden = selects.status.value === "rejeitado" || selects.status.value === "importado" || caixas.length === 0;
    todas.checked = todasSelecionadas;
    vinte.checked = !todasSelecionadas && marcadasAgora > 0 && marcadasAgora === Math.min(TAMANHO_SELECAO, caixas.length);
    enviarIA.disabled = n === 0;
    enviarIA.textContent = n ? `Enviar para a IA (${n})` : "Enviar para a IA";
  }

  async function selecionarTodas() {
    if (!todas.checked) {
      todasSelecionadas = false;
      lista.querySelectorAll(".admin-pending-check").forEach(c => { c.checked = false; });
      return atualizarLote();
    }
    todas.disabled = true;
    avisar("Buscando todas as pendências do filtro…");
    try {
      idsTodas = (await listarIdsParaIA(filtrosAtuais())).ids;
      todasSelecionadas = idsTodas.length > 0;
      lista.querySelectorAll(".admin-pending-check").forEach(c => { c.checked = todasSelecionadas; });
      avisar(idsTodas.length ? `${idsTodas.length} pendência(s) selecionada(s).`
        : "Nenhuma pendência do filtro pode ser analisada (faltam candidatas aprovadas).");
    } catch (erro) { avisar(erro.message, true); }
    todas.disabled = false;
    atualizarLote();
  }

  function selecionarVinte() {
    todasSelecionadas = false;
    [...lista.querySelectorAll(".admin-pending-check")].forEach((c, i) => { c.checked = vinte.checked && i < TAMANHO_SELECAO; });
    atualizarLote();
  }


  let parar = false, enviando = false;

  function textoResultado(r, decidir) {
    const partes = [`${r.sugeridas} com sugestão`, `${r.sem_sugestao} sem correspondência segura`];
    if (decidir) partes.push(`${r.aceitas} aceitas`, `${r.rejeitadas} rejeitadas`);
    if (r.falharam.length || r.decisoes_falhas) partes.push(`${r.falharam.length + r.decisoes_falhas} com falha (tente de novo)`);
    return partes.join(", ") + (r.parado ? ". Envio interrompido" : "") + ".";
  }

  async function enviarParaIA(ids, {decidir, refazer}) {
    if (enviando || !ids.length) return;
    if (decidir && !window.confirm(`A IA vai aceitar ou rejeitar até ${ids.length} pendência(s) com alta confiança. Rejeições não podem ser desfeitas. Continuar?`)) return;
    enviando = true; parar = false;
    enviarIA.disabled = todas.disabled = vinte.disabled = decidirIA.disabled = true;
    pararEnvio.hidden = false;
    try {
      const r = await processarEnvioIA({
        ids, parou: () => parar,
        enviar: lote => enviarPendenciasParaIA(lote, {decidir, refazer}),
        aoProgredir: p => avisar(p.aguardandoMs
          ? `A IA não respondeu a alguns itens. Aguardando ${Math.round(p.aguardandoMs / 1000)}s para tentar de novo (tentativa ${p.tentativa})…`
          : `Enviando para a IA… ${p.feitos} de ${ids.length}`),
      });
      await carregar();
      avisar(`IA processou ${r.feitos} de ${ids.length}: ${textoResultado(r, decidir)}`, r.falharam.length > 0 || r.decisoes_falhas > 0);
    } catch (erro) {
      avisar(erro.message, true);
    } finally {
      enviando = false;
      pararEnvio.hidden = true;
      todas.disabled = vinte.disabled = decidirIA.disabled = false;
      atualizarLote();
    }
  }


  const enviarSelecionadasParaIA = () => todasSelecionadas
    ? enviarParaIA(idsTodas, {decidir: decidirIA.checked, refazer: false})
    : enviarParaIA(marcadas().map(c => Number(c.value)), {decidir: decidirIA.checked, refazer: true});

  function mostrarResumo(porStatus) {
    resumo.replaceChildren(...Object.entries(porStatus || {}).map(([situacao, total]) =>
      elemento("li", "admin-count", `${rotuloSituacao(situacao)}: ${total}`)));
  }

  async function carregar({anexar = false} = {}) {
    const minha = ++requisicao;
    avisar("Carregando…");
    try {
      const dados = await listarPendencias({...filtrosAtuais(), depoisId: anexar ? proximo : 0});
      if (minha !== requisicao) return;
      if (selects.loja.options.length <= 1) {
        opcoes(selects.loja, dados.lojas, rotuloLoja, "Todas as lojas");
        opcoes(selects.categoria, dados.categorias, rotuloCategoria, "Todas as categorias");
      }
      const itens = dados.pendencias.map(cartao);
      if (!anexar) todasSelecionadas = false;
      if (anexar) lista.append(...itens); else lista.replaceChildren(...itens);
      proximo = dados.proximo;
      maisBotao.hidden = proximo === null;
      mostrarResumo(dados.por_status);
      atualizarLote();
      avisar(dados.total ? `${dados.total} pendência(s) neste filtro.` : "Nenhuma pendência neste filtro.");
    } catch (erro) {
      if (minha === requisicao) avisar(erro.message, true);
    }
  }

  function textoSugestao(sugestao) {
    return sugestao.peca ? `IA sugere (${sugestao.confianca}%)` : "IA: sem correspondência segura";
  }

  function candidato(dados, grupo, pendenciaId, sugestao) {
    const linha = elemento("div", "admin-candidate-row");
    const rotulo = elemento("label", "admin-candidate");
    const radio = elemento("input");
    radio.type = "radio"; radio.name = "candidato"; radio.value = dados.peca;
    radio.disabled = !candidatoSelecionavel(dados);
    const texto = elemento("span", "admin-candidate-text");
    texto.append(elemento("strong", "font-1-m", descreverCandidato(dados)),
      elemento("span", "font-2-s", `Pontuação ${dados.percentual ?? "—"}`));
    const {conflitos, pendencias} = textoRestricoes(dados);
    if (sugestao?.peca && sugestao.peca === dados.peca) {
      texto.append(elemento("span", "admin-ia font-2-s", `Sugerida pela IA (${sugestao.confianca}%)${sugestao.justificativa ? ": " + sugestao.justificativa : ""}`));
    }
    if (dados.vinculada_a_outro_catalogo) {
      texto.append(elemento("span", "admin-alert font-2-s",
        `Já vinculada a outro catálogo do Mercado Livre (${dados.vinculada_a_outro_catalogo}): escolha outra peça ou rejeite a pendência.`));
    }
    if (conflitos.length) texto.append(elemento("span", "admin-alert font-2-s", "Conflito: " + conflitos.join(", ")));
    if (pendencias.length) texto.append(elemento("span", "admin-note font-2-s", "Falta comprovar: " + pendencias.join(", ")));
    rotulo.append(radio, texto);
    const tirar = elemento("button", "admin-candidate-remove", "×");
    tirar.type = "button";
    tirar.setAttribute("aria-label", `Tirar da lista: ${descreverCandidato(dados)}`);
    tirar.addEventListener("click", () => tirarCandidato(pendenciaId, dados.peca, tirar));
    linha.append(rotulo, tirar);
    linha.dataset.peca = dados.peca;
    grupo.append(linha);
  }

  async function tirarCandidato(pendenciaId, peca, botao) {
    botao.disabled = true;
    avisar("Tirando peça da lista…");
    try {
      desenharDetalhe(await descartarCandidato(pendenciaId, peca));
      await carregar();
      avisar("Peça tirada da lista.");
    } catch (erro) {
      botao.disabled = false;
      avisar(erro.message, true);
    }
  }

  async function abrir(id) {
    selecionada = id;
    avisar("Carregando detalhes…");
    try {
      const dados = await detalharPendencia(id);
      desenharDetalhe(dados);
      lista.querySelectorAll(".admin-pending-item").forEach(i => i.removeAttribute("data-selected"));
      avisar("");
    } catch (erro) { avisar(erro.message, true); }
  }

  function desenharDetalhe(dados) {
    detalhe.hidden = false;
    detalhe.replaceChildren();
    const titulo = elemento("h2", "admin-detail-title font-1-m", dados.titulo);
    titulo.id = "admin-detalhe-titulo";
    detalhe.setAttribute("aria-labelledby", titulo.id);
    const link = linkSeguro(dados.url);
    const origem = link ? elemento("a", "admin-link font-2-s", "Abrir anúncio na loja") : elemento("span", "font-2-s", "Link indisponível");
    if (link) { origem.href = link; origem.target = "_blank"; origem.rel = "noopener noreferrer"; }
    detalhe.append(titulo,
      elemento("p", "font-2-s", `${rotuloLoja(dados.loja)} · ${rotuloCategoria(dados.categoria)} · ${formatarFaixaPreco(dados.preco)}`),
      origem);
    if (dados.motivo) detalhe.append(elemento("p", "admin-note font-2-s", dados.motivo));
    if (dados.sugestao_ia && !dados.sugestao_ia.peca) {
      detalhe.append(elemento("p", "admin-ia font-2-s", `IA não encontrou correspondência segura${dados.sugestao_ia.justificativa ? ": " + dados.sugestao_ia.justificativa : "."}`));
    }
    const aberta = ["em_revisao", "pendente"].includes(dados.status);
    if (!aberta) {
      detalhe.append(elemento("p", "admin-note font-2-s", `Esta pendência já foi decidida (${rotuloSituacao(dados.status)}).`));
      return;
    }
    const grupo = elemento("fieldset", "admin-candidates");
    grupo.append(elemento("legend", "font-1-m", "Peça correspondente"));
    if (!dados.candidatos.length) grupo.append(elemento("p", "font-2-s", "Sem candidatos: só é possível rejeitar."));
    dados.candidatos.forEach(c => candidato(c, grupo, dados.id, dados.sugestao_ia));
    const motivo = elemento("input", "admin-reason");
    motivo.type = "text"; motivo.maxLength = 200; motivo.placeholder = "Motivo da rejeição (opcional)";
    motivo.setAttribute("aria-label", "Motivo da rejeição");
    const aceitar = elemento("button", "btn-primary", "Aceitar peça selecionada");
    const rejeitar = elemento("button", "btn-ghost", "Rejeitar anúncio");
    aceitar.type = rejeitar.type = "button";
    aceitar.disabled = true;
    grupo.addEventListener("change", () => { aceitar.disabled = !grupo.querySelector("input:checked"); });
    aceitar.addEventListener("click", () => decidir(aceitar, rejeitar, () => aceitarPendencia(dados.id, grupo.querySelector("input:checked").value), "Pendência aceita: oferta criada."));
    rejeitar.addEventListener("click", () => decidir(aceitar, rejeitar, () => rejeitarPendencia(dados.id, motivo.value), "Pendência rejeitada."));
    const acoes = elemento("div", "admin-actions");
    acoes.append(aceitar, rejeitar);
    detalhe.append(grupo, motivo, acoes);
  }

  async function decidir(aceitar, rejeitar, acao, sucesso) {
    aceitar.disabled = rejeitar.disabled = true;
    avisar("Salvando decisão…");
    try {
      await acao();
      detalhe.hidden = true;
      selecionada = null;
      await carregar();
      avisar(sucesso);
    } catch (erro) {

      avisar(erro.message, true);
      aceitar.disabled = !detalhe.querySelector("input:checked");
      rejeitar.disabled = false;
    }
  }

  filtros.addEventListener("submit", evento => { evento.preventDefault(); detalhe.hidden = true; carregar(); });
  todas.addEventListener("change", selecionarTodas);
  vinte.addEventListener("change", selecionarVinte);
  enviarIA.addEventListener("click", enviarSelecionadasParaIA);
  pararEnvio.addEventListener("click", () => { parar = true; avisar("Parando depois do lote atual…"); });
  maisBotao.addEventListener("click", () => carregar({anexar: true}));
  carregar();
}
