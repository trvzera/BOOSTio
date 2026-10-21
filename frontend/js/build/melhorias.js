import { htmlSeguro as h, moeda, nomePeca, imagemPeca, categorias as categoriasCatalogo, perifericos, acessoriosRede } from "./catalogo.js";
import { itensCategoria } from "./estado.js";
import { avaliarBuild, selecionarPecaCompativel } from "./compatibilidade.js";
import { planejamentoLocal } from "./planejamento.js";
import { abrirDialogoBuild } from "./acoes-build.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";
import { iniciarDetalhesAnimados } from "../components/animated-details.js";
import { avaliarTrocaMelhoria, exigirTrocaMelhoria } from "./validar-melhoria.js";

const CATEGORIAS = categoriasCatalogo;
const MOTIVO_TRAVA = "Destranque a build para buscar e aplicar melhorias.";
const MOTIVO_BUDGET = "Informe um budget entre R$ 0,01 e R$ 1.000.000 para as novas peças.";
const centavos = valor => valor == null || String(valor).trim() === "" || !["number","string"].includes(typeof valor)
  || !Number.isFinite(Number(valor)) || Number(valor) < 0 ? null : Math.round(Number(valor) * 100);
const valorMonetario = valor => moeda(valor / 100);

// A busca e a prévia são locais; somente o callback recebe a build confirmada.
export function abrirMelhorias(build,catalogo,aoAplicar) {
  if (build?.travada) throw new Error(MOTIVO_TRAVA);
  if (!build?.componentes || !Array.isArray(catalogo) || typeof aoAplicar !== "function")
    throw new Error("Informe uma build, o catálogo e o callback para aplicar as alterações.");

  const original = structuredClone(build);
  const categorias = new Set(["processador","placa_video"]);
  let trocas = new Map(), aplicando = false, aplicada = false, totalExibido;
  const budgetInicial = planejamentoLocal().budget ?? build.orcamento;
  const dialogo = abrirDialogoBuild("Buscar melhorias",'<div class="upgrade-real-panel">'
    + '<div class="upgrade-real-tabs" role="tablist" aria-label="Etapas da busca de melhorias" hidden>'
    + '<button type="button" id="upgrade-tab-search" role="tab" aria-selected="true" aria-controls="upgrade-search" data-upgrade-tab="search" aria-label="Escolher peças para trocar">Escolher peças</button>'
    + '<button type="button" id="upgrade-tab-preview" role="tab" aria-selected="false" aria-controls="upgrade-preview" data-upgrade-tab="preview" tabindex="-1" aria-label="Revisar trocas selecionadas">Revisar trocas <span id="upgrade-real-count">0</span></button></div>'
    + '<div class="upgrade-real-workspace"><section class="upgrade-real-browser" id="upgrade-search" aria-label="Escolher peças para trocar">'
    + '<div class="upgrade-real-pane-heading"><h3>Peças disponíveis</h3><span>Menor preço primeiro</span></div>'
    + '<div class="upgrade-real-browser-scroll upgrade-real-scroll" tabindex="0" role="region" aria-label="Orçamento, categorias e peças sugeridas">'
    + '<label class="planning-field upgrade-real-budget" for="upgrade-real-budget"><span>Quanto deseja investir nas trocas?</span>'
    + '<input id="upgrade-real-budget" type="number" min="0.01" max="1000000" step="0.01" inputmode="decimal" value="'
    + h(budgetInicial ?? "") + '" placeholder="Ex.: 1500" aria-label="Orçamento para novas peças em reais" aria-describedby="upgrade-real-budget-help"><small id="upgrade-real-budget-help">Valor para as peças novas, sem descontar as antigas e sem frete.</small></label>'
    + '<details class="upgrade-real-filters" data-animated-details><summary><span>Peças que deseja trocar</span><strong id="upgrade-real-category-count">2 selecionadas</strong><span class="upgrade-real-chevron" aria-hidden="true"></span></summary>'
    + '<fieldset class="upgrade-real-categories"><legend class="sr-only">Selecione uma ou mais categorias</legend>'
    + CATEGORIAS.map(categoria => '<label><input type="checkbox" name="upgrade-real-category" value="' + categoria.id
      + '" ' + (categorias.has(categoria.id) ? 'checked' : '') + '><span>' + categoria.nome + '</span></label>').join("") + '</fieldset></details>'
    + '<details class="upgrade-real-help" data-animated-details><summary>O que considerar antes de trocar<span class="upgrade-real-chevron" aria-hidden="true"></span></summary><p class="planning-help">As sugestões são ordenadas por preço, não por ganho de desempenho medido. Trocas inferiores nos dados comparados ou sem dados suficientes ficam bloqueadas. RAM e discos substituem a categoria por uma unidade/kit; o total atual é considerado para não perder capacidade. CPU/GPU e outras categorias aguardam critérios de desempenho comparáveis.</p></details>'
    + '<div class="upgrade-real-results" id="upgrade-real-results"></div></div></section>'
    + '<section class="upgrade-real-preview" id="upgrade-preview" aria-labelledby="upgrade-real-preview-title"><div class="upgrade-real-pane-heading"><h3 id="upgrade-real-preview-title" tabindex="-1">Sua prévia</h3><span>Antes de salvar</span></div>'
    + '<div class="upgrade-real-preview-scroll upgrade-real-scroll" tabindex="0" role="region" aria-label="Revisão das trocas e dos valores"><div id="upgrade-real-differences"></div><p class="planning-help" id="upgrade-real-apply-reason"></p></div></section></div>'
    + '<div class="upgrade-real-footer" role="group" aria-label="Confirmar trocas"><div class="upgrade-real-selection"><span id="upgrade-real-selection-label">Nenhuma troca selecionada</span><strong id="upgrade-real-selection-total">Escolha uma peça para começar</strong></div>'
    + '<div class="build-action-actions"><button type="button" class="upgrade-real-button" data-upgrade-action="cancelar" aria-label="Cancelar alterações e fechar">Cancelar</button>'
    + '<button type="button" class="upgrade-real-button upgrade-real-primary" data-upgrade-action="aplicar" aria-label="Aplicar alterações" aria-describedby="upgrade-real-apply-reason">Aplicar trocas</button></div>'
    + '<p class="planning-help" id="upgrade-real-feedback" role="status" aria-live="polite" aria-atomic="true"></p></div></div>');
  dialogo.classList.add("upgrade-dialog");
  const cabecalho = dialogo.querySelector(".build-action-heading"), titulo = cabecalho.querySelector("h2");
  const contexto = document.createElement("div"); contexto.className = "upgrade-real-heading-copy";
  titulo.before(contexto); contexto.append(titulo);
  contexto.insertAdjacentHTML("beforeend",'<p class="upgrade-real-build-name" title="' + h(build.titulo) + '">' + h(build.titulo) + '</p>');
  const campoBudget = dialogo.querySelector("#upgrade-real-budget");
  const resultados = dialogo.querySelector("#upgrade-real-results");
  const previa = dialogo.querySelector("#upgrade-real-differences");
  const feedback = dialogo.querySelector("#upgrade-real-feedback");
  const motivoAplicar = dialogo.querySelector("#upgrade-real-apply-reason");
  const aplicar = dialogo.querySelector('[data-upgrade-action="aplicar"]');
  const fechar = dialogo.querySelector(".build-action-close");
  fechar.setAttribute("aria-label","Fechar janela de melhorias");
  const compacta = matchMedia("(max-width: 900px)");
  let aba = "search", frameViewport = 0;
  const abas = [...dialogo.querySelectorAll("[data-upgrade-tab]")];
  function mostrarAba(valor,{focar = false} = {}) {
    aba = valor;
    dialogo.querySelector(".upgrade-real-tabs").hidden = !compacta.matches;
    for (const controle of abas) {
      const ativa = controle.dataset.upgradeTab === aba;
      controle.setAttribute("aria-selected",String(ativa)); controle.tabIndex = ativa ? 0 : -1;
      const painel = dialogo.querySelector("#" + controle.getAttribute("aria-controls"));
      painel.hidden = compacta.matches && !ativa;
      if (compacta.matches) { painel.setAttribute("role","tabpanel"); painel.setAttribute("aria-labelledby",controle.id); }
      else { painel.removeAttribute("role"); if (painel.id === "upgrade-search") painel.removeAttribute("aria-labelledby"); else painel.setAttribute("aria-labelledby","upgrade-real-preview-title"); }
      if (ativa && focar) controle.focus({preventScroll:true});
    }
    programarViewport();
  }
  const ajustarCompacta = () => {
    const foco = document.activeElement;
    if (dialogo.querySelector("#upgrade-preview").contains(foco)) aba = "preview";
    else if (dialogo.querySelector("#upgrade-search").contains(foco)) aba = "search";
    mostrarAba(aba);
    if (foco && foco.closest("[hidden]")) abas.find(botao => botao.dataset.upgradeTab === aba)?.focus({preventScroll:true});
  };
  compacta.addEventListener("change",ajustarCompacta);
  dialogo.querySelector(".upgrade-real-tabs").addEventListener("keydown",evento => {
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(evento.key) || aplicando) return;
    evento.preventDefault(); mostrarAba(evento.key === 'Home' ? 'search' : evento.key === 'End' ? 'preview' : aba === 'search' ? 'preview' : 'search',{focar:true});
  });
  function ajustarViewport() {
    if (!dialogo.open) return;
    const altura = window.visualViewport?.scale === 1 ? window.visualViewport.height : innerHeight;
    const topo = window.visualViewport?.scale === 1 ? window.visualViewport.offsetTop : 0;
    const definir = (chave,valor) => { if (dialogo.style.getPropertyValue(chave) !== valor) dialogo.style.setProperty(chave,valor); };
    definir("--upgrade-viewport-height",Math.round(altura) + "px");
    definir("--upgrade-dialog-top",Math.max(0,topo + (altura - dialogo.getBoundingClientRect().height) / 2) + "px");
    const estilo = getComputedStyle(dialogo), painel = dialogo.querySelector(".upgrade-real-panel");
    const reserva = cabecalho.getBoundingClientRect().height + parseFloat(getComputedStyle(cabecalho).marginBottom || 0)
      + parseFloat(estilo.paddingTop) + parseFloat(estilo.paddingBottom)
      + dialogo.querySelector(".upgrade-real-footer").getBoundingClientRect().height
      + (compacta.matches ? dialogo.querySelector(".upgrade-real-tabs").getBoundingClientRect().height : 0)
      + (parseFloat(getComputedStyle(painel).gap) || 0) * 2;
    dialogo.classList.toggle("upgrade-dialog-flow",dialogo.clientHeight - reserva < 96);
    if (feedback.scrollHeight > feedback.clientHeight + 1) feedback.tabIndex = 0;
    else feedback.removeAttribute("tabindex");
  }
  function programarViewport() { cancelAnimationFrame(frameViewport); frameViewport = requestAnimationFrame(ajustarViewport); }
  const observarViewport = typeof ResizeObserver === "function" ? new ResizeObserver(programarViewport) : null;
  [dialogo,cabecalho,dialogo.querySelector(".upgrade-real-footer")].forEach(elemento => observarViewport?.observe(elemento));
  window.addEventListener("resize",programarViewport);
  window.visualViewport?.addEventListener("resize",programarViewport);
  window.visualViewport?.addEventListener("scroll",programarViewport);
  mostrarAba(aba);

  const pecaPorId = (categoria,id) => catalogo.find(peca => peca.categoria === categoria && peca.id === id);
  const atual = (base,categoria) => pecaPorId(categoria,itensCategoria(base,categoria)[0]?.id);
  const nome = peca => nomePeca(peca) || "Modelo sem nome";
  function nomeAtual(base,categoria) {
    const itens = itensCategoria(base,categoria);
    if (itens.length) return itens.map(item => {
      const peca = pecaPorId(categoria,item.id);
      const modelo = peca ? nome(peca) : item.proprio ? item.proprio + " (peça própria)" : "Modelo não encontrado no catálogo";
      return (item.quantidade > 1 ? item.quantidade + " × " : "") + modelo;
    }).join(" · ");
    const cpu = atual(base,"processador");
    return categoria === "placa_video" && cpu?.videointegrado
      ? "Vídeo integrado · " + (cpu.modelo_videointegrado || "modelo a confirmar") : "Nenhuma peça selecionada";
  }
  function budget() {
    const valor = centavos(campoBudget.value);
    return campoBudget.checkValidity() && valor > 0 && valor <= 100000000 ? valor : null;
  }
  function informar(texto,tom = "info") { feedback.textContent = texto; feedback.dataset.tone = tom; programarViewport(); }
  function escolhidas(escolhas) {
    return CATEGORIAS.filter(({id}) => escolhas.has(id)).map(({id,nome:rotulo}) => {
      if (!categorias.has(id)) throw new Error("Selecione a categoria de " + rotulo + ".");
      const peca = pecaPorId(id,escolhas.get(id));
      if (!peca || peca.esgotado) throw new Error(rotulo + ": a peça escolhida está indisponível no catálogo.");
      if (centavos(peca.preco) == null) throw new Error(rotulo + ": a peça escolhida não tem preço válido.");
      exigirTrocaMelhoria(original,peca,catalogo);
      return peca;
    });
  }
  function simular(escolhas,base = {...build,componentes:original.componentes}) {
    if (build.travada || base.travada) throw new Error(MOTIVO_TRAVA);
    const limite = budget();
    if (limite == null) throw new Error(MOTIVO_BUDGET);
    const pecas = escolhidas(escolhas);
    const gasto = pecas.reduce((total,peca) => total + centavos(peca.preco),0);
    if (gasto > limite) throw new Error("As peças escolhidas juntas ultrapassam o budget em " + valorMonetario(gasto - limite) + ". Remova uma troca, escolha outra peça ou ajuste o budget.");
    const proxima = structuredClone(base);
    // Retira todas as substituídas antes de validar: o consumo intermediário não é a combinação final.
    for (const peca of pecas) delete proxima.componentes[peca.categoria];
    for (const peca of pecas) {
      const validada = selecionarPecaCompativel(proxima,peca,catalogo);
      // O seletor normaliza a build. Copiar só o componente preserva rede, orçamento e metadados.
      proxima.componentes[peca.categoria] = validada.componentes[peca.categoria];
    }
    if (pecas.some(peca => perifericos.includes(peca.categoria))) proxima.incluirPerifericos = true;
    if (pecas.some(peca => acessoriosRede.includes(peca.categoria))) proxima.incluirRede = true;
    const avaliacao = avaliarBuild(proxima,catalogo);
    if (avaliacao.erros.length) throw new Error(avaliacao.erros.join(" "));
    return {build:proxima,avaliacao,gasto};
  }

  function renderizarResultados() {
    if (build.travada) { resultados.innerHTML = '<p class="planning-help">' + MOTIVO_TRAVA + '</p>'; return; }
    if (budget() == null) { resultados.innerHTML = '<p class="planning-help">' + MOTIVO_BUDGET + '</p>'; return; }
    if (!categorias.size) { resultados.innerHTML = '<p class="planning-help">Selecione uma ou mais categorias para consultar as peças.</p>'; return; }
    resultados.innerHTML = CATEGORIAS.filter(({id}) => categorias.has(id)).map(categoria => {
      const candidatas = [], conflitos = new Set(), comparacoesPendentes = new Set();
      let foraDoBudget = 0, indisponiveis = 0, inferiores = 0, semComparacao = 0;
      for (const peca of catalogo) {
        if (peca.categoria !== categoria.id || peca.id === atual(original,categoria.id)?.id) continue;
        const preco = centavos(peca.preco);
        if (peca.esgotado || preco == null) { indisponiveis++; continue; }
        const comparacao = avaliarTrocaMelhoria(original,peca,catalogo);
        if (!comparacao.permitida) {
          if (comparacao.codigo === "regressao") inferiores++;
          else if (comparacao.codigo !== "mesma-peca") { semComparacao++; comparacoesPendentes.add(comparacao.motivo); }
          continue;
        }
        const propostas = new Map(trocas);
        propostas.set(categoria.id,peca.id);
        try {
          const outras = escolhidas(propostas).filter(outra => outra.categoria !== categoria.id);
          if (preco + outras.reduce((total,outra) => total + centavos(outra.preco),0) > budget()) { foraDoBudget++; continue; }
          simular(propostas);
          candidatas.push(peca);
        } catch (erro) { conflitos.add(erro.message); }
      }
      candidatas.sort((a,b) => centavos(a.preco) - centavos(b.preco) || nome(a).localeCompare(nome(b),"pt-BR"));
      const exclusoes = [foraDoBudget ? foraDoBudget + " opções excedem o budget combinado." : "",
        indisponiveis ? indisponiveis + " opções indisponíveis ou sem preço válido." : "",
        inferiores ? inferiores + " opções inferiores nos dados comparados foram ocultadas." : "",
        semComparacao ? semComparacao + " opções sem comparação segura não são sugeridas." : ""].filter(Boolean).join(" ");
      return '<section class="upgrade-real-group"><div class="upgrade-real-group-heading"><h3>' + categoria.nome + '</h3><span>' + candidatas.length + (candidatas.length === 1 ? ' opção' : ' opções') + '</span></div><p class="upgrade-real-current"><span>Na build</span> '
        + h(nomeAtual(original,categoria.id)) + '</p>'
        + (candidatas.length ? '<div class="upgrade-real-candidates">' + candidatas.map(peca => {
          const selecionada = trocas.get(categoria.id) === peca.id;
          const acao = selecionada ? "Selecionada" : "Selecionar", preco = valorMonetario(centavos(peca.preco));
          return '<button type="button" class="upgrade-real-candidate" data-upgrade-pick="' + h(peca.id)
            + '" data-upgrade-category="' + categoria.id + '" aria-pressed="' + selecionada
            + '" aria-label="' + h(nome(peca) + " · " + preco + " · " + (selecionada ? "Na prévia" : "Adicionar à prévia")) + '"><span class="upgrade-real-candidate-image">' + imagemPeca(peca) + '</span><span class="upgrade-real-candidate-copy"><strong>' + h(nome(peca))
            + '</strong><span class="upgrade-real-candidate-price">' + h(preco) + '</span></span><span class="upgrade-real-candidate-action">' + acao + '</span></button>';
        }).join("") + '</div>' : '<p class="planning-help">' + h(comparacoesPendentes.size ? [...comparacoesPendentes][0] : "Nenhuma troca sem regressão verificável e compatível disponível dentro do budget combinado.") + '</p>')
        + (exclusoes ? '<p class="planning-help">' + h(exclusoes) + '</p>' : '')
        + (conflitos.size ? '<details class="upgrade-real-conflicts"><summary>Por que algumas opções não aparecem?</summary><ul>'
          + [...conflitos].map(motivo => '<li>' + h(motivo) + '</li>').join("") + '</ul></details>' : '') + '</section>';
    }).join("");
  }

  function renderizarPrevia() {
    const base = {...build,componentes:original.componentes};
    const proxima = structuredClone(base), limite = budget();
    let gasto = 0, precoConhecido = true;
    const linhas = CATEGORIAS.filter(({id}) => trocas.has(id)).map(categoria => {
      const peca = pecaPorId(categoria.id,trocas.get(categoria.id)), preco = centavos(peca?.preco);
      proxima.componentes[categoria.id] = {id:trocas.get(categoria.id),quantidade:1};
      if (preco == null) precoConhecido = false; else gasto += preco;
      const itensAntigos = itensCategoria(original,categoria.id);
      const precosAntigos = itensAntigos.map(item => { const valor = centavos(pecaPorId(categoria.id,item.id)?.preco); return valor == null ? null : valor * item.quantidade; });
      const precoAntigo = precosAntigos.length && precosAntigos.every(valor => valor != null) ? precosAntigos.reduce((soma,valor) => soma + valor,0) : null;
      return '<article class="upgrade-real-difference"><div class="upgrade-real-difference-heading"><h4>' + categoria.nome + '</h4><button type="button" class="upgrade-real-remove" data-upgrade-remove="' + categoria.id + '" aria-label="Remover ' + h(categoria.nome) + ' da prévia">' + iconeAnimado("trash") + '</button></div><dl><div><dt>Antes</dt><dd>'
        + h(nomeAtual(original,categoria.id)) + (precoAntigo != null ? ' · ' + h(valorMonetario(precoAntigo)) : '')
        + '</dd></div><div class="upgrade-real-after"><dt>Nova peça · 1 unidade/kit</dt><dd>' + h(peca ? nome(peca) : "Modelo não encontrado no catálogo")
        + ' · ' + h(preco != null ? valorMonetario(preco) : "Preço indisponível") + '</dd></div></dl>'
        + '</article>';
    }).join("");
    const antes = avaliarBuild(base,catalogo), depois = avaliarBuild(proxima,catalogo);
    totalExibido = depois.preco;
    const delta = centavos(depois.preco) - centavos(antes.preco);
    const avisos = [...depois.avisos,...(depois.faltam.length ? ["Ainda faltam na build: " + depois.faltam.join(", ") + "."] : [])];
    const verificacoes = (rotulo,textos,tom) => textos.length ? '<details class="upgrade-real-validation" data-tone="' + tom + '"><summary>' + h(rotulo) + ' <span>' + new Set(textos).size + '</span></summary><ul>' + [...new Set(textos)].map(texto => '<li>' + h(texto) + '</li>').join("") + '</ul></details>' : '';
    previa.innerHTML = '<dl class="upgrade-real-totals"><div><dt>Novas peças</dt><dd>' + h(precoConhecido ? valorMonetario(gasto) : "Parcial: " + valorMonetario(gasto))
      + '</dd></div><div data-tone="' + (limite != null && gasto > limite ? 'error' : 'info') + '"><dt>Budget restante</dt><dd>' + h(limite != null && precoConhecido ? valorMonetario(limite - gasto) : "Não definido")
      + '</dd></div></dl>'
      + (linhas || '<div class="upgrade-real-empty"><strong>Sua prévia aparece aqui</strong><p>Selecione peças para conferir o antes e depois. A build só muda quando você aplicar as trocas.</p></div>')
      + '<details class="upgrade-real-cost-details"><summary>Comparar o total da build<span class="upgrade-real-chevron" aria-hidden="true"></span></summary><dl><div><dt>Total cadastrado antes</dt><dd>' + h(moeda(antes.preco))
      + '</dd></div><div><dt>Total cadastrado da build na prévia</dt><dd>' + h(moeda(depois.preco))
      + '</dd></div><div><dt>Diferença no total</dt><dd>' + h((delta > 0 ? "+" : delta < 0 ? "−" : "") + valorMonetario(Math.abs(delta)))
      + '</dd></div></dl><p class="planning-help">Quantidades são consideradas nos totais. Peças próprias ou sem cotação deixam o valor parcial. Economia não significa ganho de desempenho.</p></details>'
      + verificacoes("Conflitos encontrados",depois.erros,"error") + verificacoes("Pontos de atenção",avisos,"warning")
      + verificacoes("Dicas e conferências",depois.dicas,"info")
      + (!depois.erros.length && !avisos.length ? '<p class="planning-help">Sem conflitos nas regras disponíveis. Dados ausentes não confirmam compatibilidade.</p>' : '');
    let motivo = build.travada ? MOTIVO_TRAVA : aplicando ? "Aguarde a aplicação das alterações." : !trocas.size ? "Adicione pelo menos uma candidata à prévia." : "";
    if (!motivo) { try { simular(trocas); } catch (erro) { motivo = erro.message; } }
    aplicar.disabled = Boolean(motivo);
    if (motivo) aplicar.dataset.disabledReason = motivo; else delete aplicar.dataset.disabledReason;
    motivoAplicar.textContent = motivo || "Confira as diferenças antes de aplicar as trocas.";
    dialogo.querySelector("#upgrade-real-count").textContent = trocas.size;
    dialogo.querySelector("#upgrade-real-category-count").textContent = categorias.size + (categorias.size === 1 ? " selecionada" : " selecionadas");
    dialogo.querySelector("#upgrade-real-selection-label").textContent = trocas.size ? trocas.size + (trocas.size === 1 ? " troca na prévia" : " trocas na prévia") : "Nenhuma troca selecionada";
    dialogo.querySelector("#upgrade-real-selection-total").textContent = trocas.size ? valorMonetario(gasto) + " em novas peças" : "Escolha uma peça para começar";
    aplicar.textContent = trocas.size ? "Aplicar " + trocas.size + (trocas.size === 1 ? " troca" : " trocas") : "Aplicar trocas";
    aplicar.setAttribute("aria-label",trocas.size ? "Aplicar " + trocas.size + (trocas.size === 1 ? " troca confirmada" : " trocas confirmadas") + " na build" : "Aplicar alterações");
  }

  function renderizar() {
    const foco = document.activeElement;
    const focoNaPrevia = previa.contains(foco);
    const restaurar = resultados.contains(foco) || focoNaPrevia;
    const idFoco = foco?.dataset?.upgradePick, categoriaFoco = foco?.dataset?.upgradeCategory;
    const removerFoco = foco?.dataset?.upgradeRemove;
    renderizarResultados();
    renderizarPrevia();
    dialogo.querySelectorAll("button,input,select").forEach(controle => {
      if (controle === aplicar) return;
      controle.disabled = aplicando || (build.travada && controle !== fechar && controle.dataset.upgradeAction !== "cancelar");
      if (controle.disabled) controle.dataset.disabledReason = aplicando ? "Aguarde a aplicação das alterações." : MOTIVO_TRAVA;
      else delete controle.dataset.disabledReason;
    });
    if (restaurar && dialogo.open) {
      const controles = [...dialogo.querySelectorAll("button")];
      const proximoFoco = controles.find(controle => idFoco && controle.dataset.upgradePick === idFoco && controle.dataset.upgradeCategory === categoriaFoco)
        || controles.find(controle => removerFoco && controle.dataset.upgradeRemove === removerFoco)
        || (focoNaPrevia ? dialogo.querySelector(".upgrade-real-preview-scroll") : dialogo.querySelector(".upgrade-real-browser-scroll"));
      proximoFoco.focus({preventScroll:true});
    }
    iniciarDetalhesAnimados(dialogo); iniciarIcones(dialogo); programarViewport();
  }

  campoBudget.addEventListener("input",() => {
    if (aplicando) return;
    renderizar();
    campoBudget.setAttribute("aria-invalid",String(budget() == null));
    informar(budget() == null ? MOTIVO_BUDGET : "Budget atualizado. O total das trocas será validado junto.",budget() == null ? "error" : "info");
  });
  dialogo.addEventListener("change",evento => {
    if (aplicando) return;
    const caixa = evento.target;
    if (caixa.name === "upgrade-real-category") {
      if (caixa.checked) categorias.add(caixa.value);
      else { categorias.delete(caixa.value); trocas.delete(caixa.value); }
      informar("Categorias atualizadas. Desmarcar uma categoria descarta a troca dela.");
    } else if (caixa !== campoBudget) return;
    renderizar();
  });
  dialogo.addEventListener("click",async evento => {
    const botao = evento.target.closest("button");
    if (!botao || botao.disabled || aplicando || aplicada || !dialogo.open) return;
    if (botao.dataset.upgradeTab) { mostrarAba(botao.dataset.upgradeTab,{focar:true}); return; }
    if (botao.dataset.upgradeAction === "cancelar") { dialogo.close("cancelar"); return; }
    try {
      if (build.travada) throw new Error(MOTIVO_TRAVA);
      if (botao.dataset.upgradePick) {
        const categoria = botao.dataset.upgradeCategory;
        if (!categorias.has(categoria)) throw new Error("Selecione a categoria antes de escolher uma candidata.");
        const propostas = new Map(trocas);
        propostas.set(categoria,botao.dataset.upgradePick);
        simular(propostas);
        trocas = propostas;
        renderizar();
        informar("Peça adicionada à prévia. Revise as trocas antes de aplicar.");
      } else if (botao.dataset.upgradeRemove) {
        trocas.delete(botao.dataset.upgradeRemove);
        renderizar();
        informar("Troca removida da prévia.");
      } else if (botao.dataset.upgradeAction === "aplicar") {
        if (!trocas.size) throw new Error("Adicione pelo menos uma candidata à prévia.");
        if (JSON.stringify(build.componentes) !== JSON.stringify(original.componentes))
          throw new Error("Os componentes da build mudaram enquanto o diálogo estava aberto. Cancele e abra as melhorias novamente para revisar a base atual.");
        const confirmada = simular(trocas,build);
        if (confirmada.avaliacao.preco !== totalExibido)
          throw new Error("O total mudou desde a última prévia. Confira os valores atualizados antes de aplicar novamente.");
        aplicando = true;
        renderizar();
        informar("Aplicando alterações confirmadas…");
        await aoAplicar(confirmada.build);
        aplicada = true;
        dialogo.close("aplicar");
      }
    } catch (erro) {
      aplicando = false;
      renderizar();
      informar("Não foi possível aplicar esta combinação: " + (erro?.message || "Tente novamente."),"error");
    }
  });
  dialogo.addEventListener("cancel",evento => {
    evento.preventDefault();
    if (!aplicando) dialogo.close("cancelar");
  });
  dialogo.addEventListener("click",evento => { if (aplicando && evento.target === dialogo) evento.stopImmediatePropagation(); },true);
  dialogo.addEventListener("close",() => {
    trocas.clear(); observarViewport?.disconnect(); cancelAnimationFrame(frameViewport);
    compacta.removeEventListener("change",ajustarCompacta); window.removeEventListener("resize",programarViewport);
    window.visualViewport?.removeEventListener("resize",programarViewport); window.visualViewport?.removeEventListener("scroll",programarViewport);
  },{once:true});
  renderizar();
  titulo.focus({preventScroll:true});
  return dialogo;
}
