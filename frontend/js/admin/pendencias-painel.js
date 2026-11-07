// Seção "Pendências" do dashboard de administração: lista, detalhe e decisão (aceitar ou rejeitar).
// Todo texto vindo da API entra por textContent; nada é montado com innerHTML.
import { listarPendencias, detalharPendencia, aceitarPendencia, rejeitarPendencia, descartarCandidato } from "../api/admin/pendencias.js";
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
    cabecalho.append(elemento("span", "admin-badge", rotuloLoja(pendencia.loja)),
      elemento("span", "admin-badge admin-badge-muted", rotuloCategoria(pendencia.categoria)));
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
      if (anexar) lista.append(...itens); else lista.replaceChildren(...itens);
      proximo = dados.proximo;
      maisBotao.hidden = proximo === null;
      mostrarResumo(dados.por_status);
      avisar(dados.total ? `${dados.total} pendência(s) neste filtro.` : "Nenhuma pendência neste filtro.");
    } catch (erro) {
      if (minha === requisicao) avisar(erro.message, true);
    }
  }

  function candidato(dados, grupo, pendenciaId) {
    const linha = elemento("div", "admin-candidate-row");
    const rotulo = elemento("label", "admin-candidate");
    const radio = elemento("input");
    radio.type = "radio"; radio.name = "candidato"; radio.value = dados.peca;
    radio.disabled = !candidatoSelecionavel(dados);
    const texto = elemento("span", "admin-candidate-text");
    texto.append(elemento("strong", "font-1-m", descreverCandidato(dados)),
      elemento("span", "font-2-s", `Pontuação ${dados.percentual ?? "—"}`));
    const {conflitos, pendencias} = textoRestricoes(dados);
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
    const aberta = ["em_revisao", "pendente"].includes(dados.status);
    if (!aberta) {
      detalhe.append(elemento("p", "admin-note font-2-s", `Esta pendência já foi decidida (${rotuloSituacao(dados.status)}).`));
      return;
    }
    const grupo = elemento("fieldset", "admin-candidates");
    grupo.append(elemento("legend", "font-1-m", "Peça correspondente"));
    if (!dados.candidatos.length) grupo.append(elemento("p", "font-2-s", "Sem candidatos: só é possível rejeitar."));
    dados.candidatos.forEach(c => candidato(c, grupo, dados.id));
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
      // Resultado incerto (rede) ou conflito: o administrador relê o estado antes de repetir.
      avisar(erro.message, true);
      aceitar.disabled = !detalhe.querySelector("input:checked");
      rejeitar.disabled = false;
    }
  }

  filtros.addEventListener("submit", evento => { evento.preventDefault(); detalhe.hidden = true; carregar(); });
  maisBotao.addEventListener("click", () => carregar({anexar: true}));
  carregar();
}
