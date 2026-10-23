import { htmlSeguro as h, moeda, nomePeca, perifericos, acessoriosRede } from "./catalogo.js";
import { normalizarBuild, itensSelecionados } from "./estado.js";
import { avaliarBuild } from "./compatibilidade.js";
import { numeroConhecido } from "./hardware.js";
import { consultarRenderizacoes, classificarRenderizacoes, resumirConsultaRenderizacoes } from "./comparacao-renderizacao.js";

let sequencia = 0;
const numero = valor => ["number", "string"].includes(typeof valor) && String(valor).trim()
  ? numeroConhecido(valor) : null;
const modeloConhecido = peca => typeof peca?.modelo === "string" && Boolean(peca.modelo.trim());
const decimal = valor => new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(valor);

function resumirBuild(build, catalogo) {
  const avaliacao = avaliarBuild(build, catalogo);
  const itens = itensSelecionados(build, catalogo);
  const de = categoria => itens.filter(item => item.categoria === categoria);
  const primeira = categoria => de(categoria)[0]?.peca;
  const nome = ({ item, peca }) => modeloConhecido(peca) ? nomePeca(peca)
    : item.proprio || (peca ? "Modelo não informado" : "Modelo fora do catálogo");
  const modelos = lista => lista.map(entrada =>
    (entrada.item.quantidade > 1 ? entrada.item.quantidade + " × " : "") + nome(entrada)).join(" · ");
  const semModelo = itens.filter(({ peca }) => !modeloConhecido(peca)).length;
  const semPreco = itens.filter(({ peca }) => numero(peca?.preco) == null).length;
  const precos = itens.filter(({ peca }) => numero(peca?.preco) != null);
  const subtotal = precos.reduce((soma, { item, peca }) => soma + numero(peca.preco) * item.quantidade, 0);
  // Orçamento é um limite de planejamento, nunca o preço da build.
  const rede = build.rede;
  const redeDefinida = ["cabo", "wifi"].includes(rede?.tipo);
  const categoriaRede = rede?.tipo === "cabo" ? "cabo_rede" : "adaptador_wifi";
  const comprarRede = build.incluirRede && redeDefinida && rede.possuiAcessorio === false;
  const redeSemCotacao = comprarRede && !de(categoriaRede).some(({peca}) => peca && numero(peca.preco) != null);
  const redeAConfirmar = build.incluirRede && redeDefinida && rede.possuiAcessorio == null && !de(categoriaRede).length;
  const detalheRede = redeSemCotacao ? "Acessório de rede necessário, ainda sem cotação"
    : redeAConfirmar ? "Confirme se será necessário comprar um acessório de rede"
    : "";
  const preco = Math.round(subtotal * 100) / 100;
  const completa = !avaliacao.faltam.length && itens.length > 0 && semModelo === 0;
  const totalConfiavel = completa && semPreco === 0 && !redeSemCotacao && !redeAConfirmar && Number.isFinite(preco);
  // A fonte fornece energia; sua potência não é consumo. Periféricos ficam fora da estimativa do PC.
  const consumidores = itens.filter(({ categoria }) => ![...perifericos, ...acessoriosRede, "fonte"].includes(categoria));
  const consumos = consumidores.filter(({ peca }) => numero(peca?.consumo_energia) != null);
  const watts = Math.round(consumos.reduce((soma, { item, peca }) =>
    soma + numero(peca.consumo_energia) * item.quantidade, 0));
  const consumoCompleto = completa && consumidores.length > 0
    && consumos.length === consumidores.length && Number.isFinite(watts);
  const capacidade = lista => {
    const conhecidos = lista.filter(({ peca }) => numero(peca?.capacidade_gb) != null);
    const total = conhecidos.reduce((soma, { item, peca }) => soma + numero(peca.capacidade_gb) * item.quantidade, 0);
    return !conhecidos.length || !Number.isFinite(total) ? "Capacidade indisponível"
      : decimal(total) + " GB" + (conhecidos.length < lista.length ? " conhecidos · parcial" : "");
  };
  const cpu = primeira("processador"), gpu = primeira("placa_video");
  const ram = de("memoria_ram"), discos = [...de("ssd"), ...de("hd")];
  const pendenciasPreco = [
    avaliacao.faltam.length ? "Faltam: " + avaliacao.faltam.join(", ") : "",
    semModelo ? semModelo + " seleção(ões) sem modelo identificado" : "",
    semPreco ? semPreco + " seleção(ões) sem preço conhecido" : "",
    redeSemCotacao || redeAConfirmar ? detalheRede : "",
    !Number.isFinite(preco) ? "Total fora do intervalo calculável" : "",
  ].filter(Boolean).join(". ");
  return {
    build, avaliacao, completa, preco, totalConfiavel, consumoCompleto, watts, detalheRede,
    precoTexto: precos.length && Number.isFinite(preco) ? moeda(preco) : "Preço indisponível",
    wattsTexto: consumos.length && Number.isFinite(watts) ? decimal(watts) + " W" : "Consumo indisponível",
    pendenciasPreco,
    cpu: modelos(de("processador")) || "Não selecionado",
    cpuDetalhe: numero(cpu?.thread) != null ? decimal(numero(cpu.thread)) + " threads" : "",
    gpu: modelos(de("placa_video")) || (cpu?.videointegrado === true ? "Vídeo integrado ao processador" : "Não selecionada"),
    gpuDetalhe: numero(gpu?.memoria_gb) != null ? decimal(numero(gpu.memoria_gb)) + " GB de VRAM" : "",
    ram: capacidade(ram), ramDetalhe: modelos(ram) || "Nenhuma memória selecionada",
    discos: capacidade(discos), discosDetalhe: modelos(discos) || "Nenhum SSD ou HD selecionado",
  };
}

const botao = (texto, classe, atributos = "", rotulo = texto) =>
  '<button type="button" class="compare-button ' + classe + '" aria-label="' + h(rotulo) + '" ' + atributos + '>' + h(texto) + '</button>';

function campo(rotulo, valor, detalhe = "", destaque = false) {
  return '<div class="compare-field' + (destaque ? ' compare-field-best' : '') + '"><dt class="compare-field-label">'
    + h(rotulo) + '</dt><dd class="compare-field-value">' + h(valor) + '</dd>'
    + (detalhe ? '<dd class="compare-field-detail">' + h(detalhe) + '</dd>' : '') + '</div>';
}

function compatibilidade({ avaliacao }) {
  const { erros, avisos, dicas, faltam } = avaliacao;
  const rotulo = erros.length ? "Incompatibilidades encontradas" : faltam.length ? "Build incompleta"
    : avisos.length ? "Conferência necessária" : "Sem conflitos identificados";
  const mensagens = [...erros, ...faltam.map(nome => "Falta: " + nome), ...avisos];
  const tom = erros.length ? "error" : mensagens.length ? "warning" : dicas.length ? "info" : "success";
  const lista = textos => '<ul class="compare-messages">'
    + textos.map(texto => '<li class="compare-message">' + h(texto) + '</li>').join("") + '</ul>';
  return '<div class="compare-field"><dt class="compare-field-label">Compatibilidade</dt>'
    + '<dd class="compare-field-value compare-status-' + tom + '">'
    + h(rotulo) + '</dd><dd class="compare-field-detail">'
    + (mensagens.length ? '<details class="compare-details"><summary class="compare-details-toggle">Ver '
      + mensagens.length + ' pendência(s)</summary>' + lista(mensagens) + '</details>' : '')
    + (dicas.length ? '<details class="compare-details compare-details-info"><summary class="compare-details-toggle">Dicas e conferências</summary>'
      + lista(dicas) + '</details>' : '')
    + (!mensagens.length && !dicas.length ? 'Verificação das regras disponíveis no catálogo; confirme os dados dos fabricantes.' : '') + '</dd></div>';
}

/**
 * Abre um dialog nativo, sem buscar dados nem gravar builds/storage.
 * @param {Array<object>} builds Builds no formato de estado.js; IDs repetidos contam uma vez.
 * @param {Array<object>} catalogo Peças já carregadas, no formato de catalogo.js.
 * @returns {HTMLDialogElement} Dialog aberto; pode ser fechado com .close(). É removido ao fechar.
 * @throws {TypeError|RangeError} Entradas inválidas ou menos de duas builds distintas.
 * Requer comparacao.css e os tokens/fontes do site carregados pela página consumidora.
 */
export function abrirComparacao(builds, catalogo) {
  if (!Array.isArray(builds) || builds.some(build => !build || typeof build !== "object" || Array.isArray(build)))
    throw new TypeError("Informe uma lista de builds válidas para comparar.");
  if (!Array.isArray(catalogo) || catalogo.some(peca => !peca || typeof peca !== "object" || Array.isArray(peca)))
    throw new TypeError("Informe o catálogo de peças já carregado.");
  const unicas = new Map();
  for (const valor of builds) {
    const build = normalizarBuild(valor);
    if (!unicas.has(build.id)) unicas.set(build.id, build);
  }
  if (unicas.size < 2) throw new RangeError("São necessárias pelo menos duas builds distintas para comparar.");
  if (!document.body) throw new Error("Abra a comparação depois que o documento estiver pronto.");
  const dados = [...unicas.values()].map(build => resumirBuild(build, catalogo));
  const selecionadas = new Set(dados.length === 2 ? [0, 1] : []);
  const cacheRender = new Map();
  let consultaRender, tipoRender = "cpu", pausaRenderAte = 0, timerRender;
  const origem = document.activeElement;
  const dialogo = document.createElement("dialog");
  if (typeof dialogo.showModal !== "function") throw new Error("Este navegador precisa oferecer suporte a dialog nativo.");
  let prefixo;
  do { prefixo = "compare-dialog-" + ++sequencia; }
  while (["title", "description", "feedback", "picker"].some(sufixo => document.getElementById(prefixo + "-" + sufixo)));
  dialogo.className = "compare-dialog";
  dialogo.setAttribute("aria-labelledby", prefixo + "-title");
  dialogo.setAttribute("aria-describedby", prefixo + "-description");
  dialogo.setAttribute("aria-modal", "true");
  dialogo.setAttribute("closedby", "closerequest");
  dialogo.innerHTML = '<header class="compare-dialog-head"><div class="compare-heading-copy">'
    + '<p class="compare-eyebrow">Suas configurações, lado a lado</p>'
    + '<h2 class="compare-title" id="' + prefixo + '-title">Compare suas builds</h2>'
    + '<p class="compare-description" id="' + prefixo + '-description">Compare duas ou três configurações com os dados disponíveis no catálogo.</p></div>'
    + botao("Fechar", "compare-button-close", 'data-compare-action="close"', "Fechar comparação") + '</header>'
    + '<div class="compare-content"></div><p class="compare-feedback" id="' + prefixo + '-feedback" role="status" aria-live="polite" aria-atomic="true"></p>';
  const conteudo = dialogo.querySelector(".compare-content");
  const feedback = dialogo.querySelector(".compare-feedback");
  const anunciar = mensagem => { feedback.textContent = mensagem; };
  const focarTitulo = () => conteudo.querySelector(".compare-section-title")?.focus({ preventScroll: true });
  const cabecalho = item => '<strong class="compare-choice-title">' + h(item.build.titulo)
    + '</strong><span class="compare-choice-specs">' + h(item.cpu + " · " + item.gpu)
    + '</span><span class="compare-choice-price">' + h(item.precoTexto)
    + (item.totalConfiavel ? ' · total cadastrado' : ' · parcial / indisponível') + '</span>';

  function atualizarSelecao() {
    conteudo.querySelectorAll(".compare-checkbox").forEach(caixa => {
      caixa.checked = selecionadas.has(Number(caixa.value));
    });
    conteudo.querySelector('[data-compare-action="confirm"]').disabled = selecionadas.size < 2;
    anunciar(selecionadas.size + " de 3 builds selecionadas. " + (selecionadas.size < 2
      ? "Selecione pelo menos duas para comparar." : "Você já pode ver a comparação."));
  }

  function mostrarSelecao() {
    conteudo.innerHTML = '<section class="compare-selection"><h3 class="compare-section-title" tabindex="-1">Escolha suas builds</h3>'
      + '<p class="compare-help">Selecione duas ou três builds. Depois, você pode adicionar uma terceira ou remover uma das três nos resultados.</p>'
      + '<fieldset class="compare-options" aria-describedby="' + prefixo + '-feedback"><legend class="compare-legend">Builds disponíveis para comparação</legend>'
      + dados.map((item, indice) => '<label class="compare-choice"><input class="compare-checkbox" type="checkbox" value="' + indice
        + '"><span class="compare-choice-copy">' + cabecalho(item) + '</span></label>').join("") + '</fieldset>'
      + '<div class="compare-actions">' + botao("Ver comparação", "compare-button-primary", 'data-compare-action="confirm" disabled') + '</div></section>';
    atualizarSelecao();
  }

  function resumo(rotulo, elegiveis, valor, unidade) {
    const vencedoras = elegiveis.filter(item => item[unidade] === valor);
    const texto = !vencedoras.length ? "Indisponível" : vencedoras.length > 1 ? "Empate entre " + vencedoras.length + " builds" : vencedoras[0].build.titulo;
    const detalhe = !vencedoras.length ? "Nenhum total completo conhecido" : (unidade === "preco" ? moeda(valor) : decimal(valor) + " W estimados")
      + (vencedoras.length > 1 ? " · " + vencedoras.map(item => item.build.titulo).join(", ") : "");
    return '<div class="compare-summary-item"><dt class="compare-summary-label">' + h(rotulo)
      + '</dt><dd class="compare-summary-value">' + h(texto) + '</dd><dd class="compare-summary-detail">' + h(detalhe) + '</dd></div>';
  }

  function mostrarResultados() {
    if (selecionadas.size < 2 || selecionadas.size > 3) return;
    consultaRender?.abort();
    const itens = [...selecionadas].map(indice => dados[indice]);
    const precos = itens.filter(item => item.totalConfiavel), consumos = itens.filter(item => item.consumoCompleto);
    const menorPreco = precos.length ? Math.min(...precos.map(item => item.preco)) : null;
    const menorConsumo = consumos.length ? Math.min(...consumos.map(item => item.watts)) : null;
    const restantes = dados.map((item, indice) => ({ item, indice })).filter(({ indice }) => !selecionadas.has(indice));
    const podeAdicionar = itens.length === 2 && restantes.length > 0;
    conteudo.innerHTML = '<section class="compare-results"><div class="compare-results-head">'
      + '<h3 class="compare-section-title" tabindex="-1">O que muda entre elas</h3>'
      + (podeAdicionar ? botao("Adicionar terceira build", "compare-button-secondary", 'data-compare-action="picker" aria-expanded="false" aria-controls="' + prefixo + '-picker"') : '') + '</div>'
      + (podeAdicionar ? '<section class="compare-picker" id="' + prefixo + '-picker" aria-label="Escolha a terceira build" hidden>'
        + '<p class="compare-help">Escolha a terceira build para adicionar à comparação.</p><div class="compare-candidates">'
        + restantes.map(({ item, indice }) => '<div class="compare-candidate"><div class="compare-choice-copy">' + cabecalho(item) + '</div>'
          + botao("Adicionar build", "compare-button-secondary", 'data-compare-action="add" data-compare-index="' + indice + '"', "Adicionar build " + item.build.titulo + " à comparação") + '</div>').join("")
        + '</div></section>' : '')
      + '<dl class="compare-summary" aria-label="Destaques da comparação">'
      + resumo("Menor preço", precos, menorPreco, "preco") + resumo("Menor consumo estimado", consumos, menorConsumo, "watts")
      + '<div class="compare-summary-item" data-render-summary><dt class="compare-summary-label">Melhor renderização · Blender</dt><dd class="compare-summary-value">Ainda não consultado</dd>'
      + '<dd class="compare-summary-detail">Compare a CPU ou GPU abaixo.</dd></div></dl>'
      + '<p class="compare-help">Destaques de preço e consumo consideram apenas totais completos conhecidos. Preços parciais ficam fora dessa classificação.</p>'
      + '<section class="compare-render-controls" aria-label="Comparar desempenho em renderização"><div><h4 class="compare-section-title">Renderização no Blender</h4><p class="compare-help">Resultados públicos por componente; não é um teste da máquina completa.</p></div><div class="compare-render-actions"><label for="' + prefixo + '-render-type">Componente<select id="' + prefixo + '-render-type" data-render-type><option value="cpu"' + (tipoRender === "cpu" ? ' selected' : '') + '>Processador · CPU</option><option value="gpu"' + (tipoRender === "gpu" ? ' selected' : '') + '>Placa de vídeo · GPU</option></select></label>'
      + botao("Comparar renderização","compare-button-primary",'data-compare-action="render"') + '</div><p class="compare-help compare-render-feedback" data-render-feedback role="status" aria-live="polite">A consulta só é feita ao clicar. CPU e GPU são avaliadas separadamente.</p></section>'
      + '<p class="compare-scroll-hint">Deslize as colunas ou use as setas do teclado para ver todas as builds.</p>'
      + '<div class="compare-columns" role="group" tabindex="0" aria-label="Builds comparadas lado a lado. Use as setas para rolar horizontalmente.">'
      + itens.map((item, ordem) => {
        const melhorPreco = item.totalConfiavel && item.preco === menorPreco;
        const melhorConsumo = item.consumoCompleto && item.watts === menorConsumo;
        const indice = dados.indexOf(item);
        return '<article class="compare-card" aria-label="Comparação da build ' + h(item.build.titulo) + '"><header class="compare-card-head">'
          + '<p class="compare-eyebrow">Build ' + String(ordem + 1).padStart(2, "0") + '</p><h4 class="compare-card-title">' + h(item.build.titulo) + '</h4>'
          + '<p class="compare-card-description">' + h(item.build.descricao || "Configuração sem descrição") + '</p><div class="compare-tags">'
          + (!item.completa ? '<span class="compare-tag compare-tag-warning">Build parcial</span>' : '')
          + (item.completa && !item.totalConfiavel ? '<span class="compare-tag compare-tag-warning">Preço parcial</span>' : '')
          + (melhorPreco ? '<span class="compare-tag">Menor preço</span>' : '')
          + (melhorConsumo ? '<span class="compare-tag">Menor consumo estimado</span>' : '') + '</div>'
          + (itens.length === 3 ? botao("Remover build", "compare-button-remove", 'data-compare-action="remove" data-compare-index="' + indice + '"', "Remover build " + item.build.titulo + " da comparação") : '') + '</header>'
          + '<dl class="compare-specs">'
          + campo(item.totalConfiavel ? "Preço total cadastrado" : "Preço parcial / indisponível", item.precoTexto,
            item.totalConfiavel ? (melhorPreco ? "Menor preço entre os totais completos exibidos." : "+" + moeda(item.preco - menorPreco) + " frente ao menor total completo.")
              + (item.detalheRede ? " " + item.detalheRede + "." : "") : item.pendenciasPreco, melhorPreco)
          + '<div class="compare-field" data-render-build="' + h(item.build.id) + '"><dt class="compare-field-label">Renderização · Blender</dt><dd class="compare-field-value">Ainda não consultado</dd><dd class="compare-field-detail">Selecione CPU ou GPU e compare a renderização.</dd></div>'
          + campo("Consumo estimado do PC", item.wattsTexto, item.consumoCompleto
            ? (melhorConsumo ? "Menor estimativa completa exibida." : "+" + decimal(item.watts - menorConsumo) + " W frente à menor estimativa completa.")
            : "Estimativa parcial / indisponível: faltam peças, modelos ou dados de consumo.", melhorConsumo)
          + campo("Processador · CPU", item.cpu, item.cpuDetalhe)
          + campo("Placa de vídeo · GPU", item.gpu, item.gpuDetalhe)
          + campo("Memória RAM", item.ram, item.ramDetalhe)
          + campo("Armazenamento · SSD / HD", item.discos, item.discosDetalhe)
          + compatibilidade(item)
          + campo("Desempenho em jogos", "Indisponível", "Aguardando benchmarks comparáveis da API. Sem estimativa de FPS.")
          + '</dl></article>';
      }).join("") + '</div><p class="compare-footnote">Valores cadastrados no catálogo podem ser demonstrativos; não são cotações em tempo real. '
      + 'Orçamento não entra no preço. Acessório de rede a confirmar ou sem cotação deixa o total parcial. '
      + 'O consumo é uma estimativa dos componentes do PC, sem fonte, periféricos e acessórios de rede; não é uma medição na tomada.</p></section>';
    anunciar("Comparando " + selecionadas.size + " builds.");
    atualizarPausaRender();
    dialogo.scrollTop = 0;
    if (dialogo.open) focarTitulo();
  }

  dialogo.addEventListener("change", evento => {
    if (evento.target.matches("[data-render-type]")) { tipoRender = evento.target.value; mostrarResultados(); return; }
    const caixa = evento.target.closest(".compare-checkbox");
    if (!caixa) return;
    const indice = Number(caixa.value);
    if (caixa.checked && selecionadas.size === 3) {
      caixa.checked = false;
      anunciar("Limite de três builds. Desmarque uma antes de selecionar outra.");
      return;
    }
    if (caixa.checked) selecionadas.add(indice);
    else selecionadas.delete(indice);
    atualizarSelecao();
  });
  dialogo.addEventListener("click", evento => {
    const controle = evento.target.closest("button[data-compare-action]");
    if (!controle || controle.disabled) return;
    const acao = controle.dataset.compareAction, indice = Number(controle.dataset.compareIndex);
    if (acao === "close") dialogo.close("fechar");
    else if (acao === "render") compararRenderizacao(controle);
    else if (acao === "confirm") mostrarResultados();
    else if (acao === "picker") {
      const painel = conteudo.querySelector(".compare-picker");
      painel.hidden = !painel.hidden;
      controle.setAttribute("aria-expanded", String(!painel.hidden));
      if (!painel.hidden) painel.querySelector("button")?.focus({ preventScroll: true });
    } else if (acao === "add" && selecionadas.size === 2 && dados[indice]) {
      selecionadas.add(indice);
      mostrarResultados();
    } else if (acao === "remove" && selecionadas.size === 3) {
      selecionadas.delete(indice);
      mostrarResultados();
    }
    // Padding e backdrop não disparam nenhuma ação de fechamento.
  });
  dialogo.addEventListener("cancel", evento => {
    evento.preventDefault();
    dialogo.close("cancelar");
  });
  dialogo.addEventListener("close", () => {
    consultaRender?.abort();
    clearInterval(timerRender);
    const ativo = document.activeElement;
    const restaurar = !ativo || ativo === document.body || dialogo.contains(ativo) || ativo === origem;
    dialogo.remove();
    if (restaurar && origem?.isConnected && typeof origem.focus === "function") origem.focus({ preventScroll: true });
  }, { once: true });
  if (dados.length === 2) mostrarResultados();
  else mostrarSelecao();
  document.body.append(dialogo);
  try {
    dialogo.showModal();
    focarTitulo();
  } catch (erro) {
    dialogo.remove();
    throw erro;
  }
  return dialogo;

  async function compararRenderizacao(controle) {
    if (Date.now() < pausaRenderAte) { atualizarPausaRender(); return; }
    consultaRender?.abort();
    const atual = consultaRender = new AbortController();
    const exibidas = [...selecionadas].map(indice => dados[indice].build);
    controle.disabled = true;
    controle.dataset.disabledReason = "Aguarde a consulta de renderização.";
    const retorno = conteudo.querySelector("[data-render-feedback]");
    retorno.textContent = "Consultando resultados públicos do Blender…";
    retorno.dataset.tone = "info";
    conteudo.querySelectorAll("[data-render-build]").forEach(campo => campo.setAttribute("aria-busy","true"));
    try {
      const resultados = await consultarRenderizacoes(exibidas,catalogo,{tipo:tipoRender,signal:atual.signal,cache:cacheRender});
      if (atual.signal.aborted || !dialogo.open) return;
      const classificacao = classificarRenderizacoes(resultados);
      conteudo.querySelectorAll("[data-render-build]").forEach(campo => {
        const resultado = resultados.find(item => item.id === campo.dataset.renderBuild), valor = resultado?.dados;
        campo.classList.toggle("compare-field-best",classificacao.melhores.includes(resultado?.id));
        campo.innerHTML = '<dt class="compare-field-label">Renderização · ' + tipoRender.toUpperCase() + '</dt><dd class="compare-field-value">' + (valor ? h(decimal(valor.score)) + ' amostras/min' : 'Indisponível') + '</dd><dd class="compare-field-detail">' + (valor
          ? h(resultado.dispositivo + " · Blender " + valor.versao + " · " + valor.metodo + " · " + valor.quantidade + " resultado(s)") + '<br><a href="' + h(valor.url) + '" target="_blank" rel="noopener noreferrer" aria-label="Ver fonte do Blender para ' + h(resultado.dispositivo) + '">Ver fonte dos dados</a>'
          : h(resultado?.erro || "Sem dados disponíveis.")) + '</dd>';
      });
      const nomes = exibidas.filter(build => classificacao.melhores.includes(build.id)).map(build => build.titulo);
      conteudo.querySelector("[data-render-summary]").innerHTML = '<dt class="compare-summary-label">Melhor renderização · ' + tipoRender.toUpperCase() + '</dt><dd class="compare-summary-value">' + h(classificacao.comparavel ? nomes.length > 1 ? "Empate entre " + nomes.length + " builds" : nomes[0] : "Sem classificação") + '</dd><dd class="compare-summary-detail">' + h(classificacao.comparavel ? decimal(classificacao.score) + " amostras/min · mesma versão e método" : classificacao.motivo) + '</dd>';
      const resumo = resumirConsultaRenderizacoes(resultados);
      retorno.textContent = resumo.mensagem; retorno.dataset.tone = resumo.tom;
      if (resumo.espera > 0) {
        pausaRenderAte = Date.now() + resumo.espera * 1000;
        clearInterval(timerRender); timerRender = setInterval(atualizarPausaRender,1000);
      }
    } catch (erro) { if (!atual.signal.aborted) { retorno.textContent = erro.message; retorno.dataset.tone = "error"; } }
    finally {
      if (!atual.signal.aborted) {
        conteudo.querySelectorAll("[data-render-build]").forEach(campo => campo.setAttribute("aria-busy","false"));
        controle.disabled = false; delete controle.dataset.disabledReason;
        atualizarPausaRender();
      }
    }
  }

  function atualizarPausaRender() {
    const espera = Math.max(0,Math.ceil((pausaRenderAte-Date.now())/1000));
    const botao = conteudo.querySelector('[data-compare-action="render"]');
    if (espera) {
      if (botao) {
        botao.disabled = true;
        botao.dataset.disabledReason = "O Blender solicitou uma pausa. Aguarde " + espera + " s.";
      }
    } else {
      clearInterval(timerRender);
      if (botao) { botao.disabled = false; delete botao.dataset.disabledReason; }
    }
  }
}
