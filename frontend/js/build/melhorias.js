import { htmlSeguro as h, moeda, nomePeca, categorias as categoriasCatalogo, perifericos, acessoriosRede } from "./catalogo.js";
import { itensCategoria } from "./estado.js";
import { avaliarBuild, selecionarPecaCompativel } from "./compatibilidade.js";
import { planejamentoLocal } from "./planejamento.js";
import { abrirDialogoBuild } from "./acoes-build.js";

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
    + '<p class="planning-help">' + h(build.titulo) + '</p>'
    + '<div class="planning-grid"><label class="planning-field" for="upgrade-real-budget"><span>Budget para trocas (R$)</span>'
    + '<input id="upgrade-real-budget" type="number" min="0.01" max="1000000" step="0.01" inputmode="decimal" value="'
    + h(budgetInicial ?? "") + '" aria-describedby="upgrade-real-budget-help"></label>'
    + '<label class="planning-field" for="upgrade-real-order"><span>Ordenar por</span><select id="upgrade-real-order" aria-describedby="upgrade-real-order-help">'
    + '<option value="preco">Menor preço</option>'
    + '<option value="desempenho" disabled title="Faltam benchmarks comparáveis.">Melhor desempenho — indisponível: faltam benchmarks comparáveis</option>'
    + '</select></label></div>'
    + '<details class="upgrade-real-help"><summary>Como funcionam as trocas</summary><p class="planning-help" id="upgrade-real-budget-help">Budget só para peças novas, sem descontar as antigas. RAM, discos e fans substituem a categoria por uma unidade/kit; ajuste quantidades no editor.</p></details>'
    + '<span class="sr-only" id="upgrade-real-order-help">Somente preço está disponível; ganho de desempenho ainda não foi medido.</span>'
    + '<fieldset class="upgrade-real-categories"><legend>Categorias para buscar</legend>'
    + CATEGORIAS.map(categoria => '<label><input type="checkbox" name="upgrade-real-category" value="' + categoria.id
      + '" ' + (categorias.has(categoria.id) ? 'checked' : '') + '> ' + categoria.nome + '</label>').join("") + '</fieldset>'
    + '<p class="planning-help" id="upgrade-real-feedback" role="status" aria-live="polite" aria-atomic="true"></p>'
    + '<div class="upgrade-real-workspace"><div class="upgrade-real-results" id="upgrade-real-results" tabindex="0" role="region" aria-label="Peças sugeridas"></div>'
    + '<section class="upgrade-real-preview" aria-labelledby="upgrade-real-preview-title"><h3 id="upgrade-real-preview-title" tabindex="-1">Prévia das alterações</h3>'
    + '<div id="upgrade-real-differences"></div></section></div>'
    + '<p class="planning-help" id="upgrade-real-apply-reason" aria-live="polite"></p>'
    + '<div class="build-action-actions"><button type="button" class="upgrade-real-button" data-upgrade-action="cancelar" aria-label="Cancelar alterações e fechar">Cancelar</button>'
    + '<button type="button" class="upgrade-real-button upgrade-real-primary" data-upgrade-action="aplicar" aria-label="Aplicar alterações" aria-describedby="upgrade-real-apply-reason">Aplicar alterações</button></div></div>');
  dialogo.classList.add("upgrade-dialog");
  const campoBudget = dialogo.querySelector("#upgrade-real-budget");
  const ordem = dialogo.querySelector("#upgrade-real-order");
  const resultados = dialogo.querySelector("#upgrade-real-results");
  const previa = dialogo.querySelector("#upgrade-real-differences");
  const feedback = dialogo.querySelector("#upgrade-real-feedback");
  const motivoAplicar = dialogo.querySelector("#upgrade-real-apply-reason");
  const aplicar = dialogo.querySelector('[data-upgrade-action="aplicar"]');
  const fechar = dialogo.querySelector(".build-action-close");
  fechar.setAttribute("aria-label","Fechar janela de melhorias");

  const pecaPorId = (categoria,id) => catalogo.find(peca => peca.categoria === categoria && peca.id === id);
  const atual = (base,categoria) => pecaPorId(categoria,itensCategoria(base,categoria)[0]?.id);
  const nome = peca => nomePeca(peca) || "Modelo sem nome";
  function nomeAtual(base,categoria) {
    const item = itensCategoria(base,categoria)[0], peca = atual(base,categoria);
    if (peca) return nome(peca);
    if (item) return item.proprio ? item.proprio + " (peça própria)" : "Modelo não encontrado no catálogo";
    const cpu = atual(base,"processador");
    return categoria === "placa_video" && cpu?.videointegrado
      ? "Vídeo integrado · " + (cpu.modelo_videointegrado || "modelo a confirmar") : "Nenhuma peça selecionada";
  }
  function budget() {
    const valor = centavos(campoBudget.value);
    return campoBudget.checkValidity() && valor > 0 && valor <= 100000000 ? valor : null;
  }
  function informar(texto) { feedback.textContent = texto; }
  function escolhidas(escolhas) {
    return CATEGORIAS.filter(({id}) => escolhas.has(id)).map(({id,nome:rotulo}) => {
      if (!categorias.has(id)) throw new Error("Selecione a categoria de " + rotulo + ".");
      const peca = pecaPorId(id,escolhas.get(id));
      if (!peca || peca.esgotado) throw new Error(rotulo + ": a peça escolhida está indisponível no catálogo.");
      if (centavos(peca.preco) == null) throw new Error(rotulo + ": a peça escolhida não tem preço válido.");
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
      const candidatas = [], conflitos = new Set();
      let foraDoBudget = 0, indisponiveis = 0;
      for (const peca of catalogo) {
        if (peca.categoria !== categoria.id || peca.id === atual(original,categoria.id)?.id) continue;
        const preco = centavos(peca.preco);
        if (peca.esgotado || preco == null) { indisponiveis++; continue; }
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
        indisponiveis ? indisponiveis + " opções indisponíveis ou sem preço válido." : ""].filter(Boolean).join(" ");
      return '<section class="upgrade-real-group"><h3>' + categoria.nome + '</h3><p class="planning-help">Atual: '
        + h(nomeAtual(original,categoria.id)) + '</p>'
        + (candidatas.length ? '<div class="upgrade-real-candidates">' + candidatas.map(peca => {
          const selecionada = trocas.get(categoria.id) === peca.id;
          const acao = selecionada ? "Na prévia" : "Adicionar à prévia", preco = valorMonetario(centavos(peca.preco));
          return '<button type="button" class="upgrade-real-candidate" data-upgrade-pick="' + h(peca.id)
            + '" data-upgrade-category="' + categoria.id + '" aria-pressed="' + selecionada
            + '" aria-label="' + h(nome(peca) + " " + preco + " " + acao) + '"><strong>' + h(nome(peca))
            + '</strong> <span>' + h(preco) + '</span> <span>' + acao + '</span></button>';
        }).join("") + '</div>' : '<p class="planning-help">Nenhuma candidata compatível disponível dentro do budget combinado para esta combinação.</p>')
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
      const precoAntigo = centavos(atual(original,categoria.id)?.preco);
      return '<article class="upgrade-real-difference"><h4>' + categoria.nome + '</h4><dl><div><dt>Antes</dt><dd>'
        + h(nomeAtual(original,categoria.id)) + (precoAntigo != null ? ' · ' + h(valorMonetario(precoAntigo)) : '')
        + '</dd></div><div><dt>Depois</dt><dd>' + h(peca ? nome(peca) : "Modelo não encontrado no catálogo")
        + ' · ' + h(preco != null ? valorMonetario(preco) : "Preço indisponível") + '</dd></div></dl>'
        + '<button type="button" class="upgrade-real-button" data-upgrade-remove="' + categoria.id + '" aria-label="Remover '
        + categoria.sigla + ' da prévia">Remover ' + categoria.sigla + ' da prévia</button></article>';
    }).join("");
    const antes = avaliarBuild(base,catalogo), depois = avaliarBuild(proxima,catalogo);
    totalExibido = depois.preco;
    const delta = centavos(depois.preco) - centavos(antes.preco);
    const pendencias = [...depois.erros,...depois.avisos,...depois.dicas,
      ...(depois.faltam.length ? ["Ainda faltam na build: " + depois.faltam.join(", ") + "."] : [])];
    previa.innerHTML = (linhas || '<p class="planning-help">Nenhuma alteração escolhida. Adicione candidatas para comparar antes e depois.</p>')
      + '<dl class="upgrade-real-totals"><div><dt>Custo combinado das novas peças</dt><dd>' + h(precoConhecido ? valorMonetario(gasto) : "Preço parcial: " + valorMonetario(gasto))
      + '</dd></div><div><dt>Budget restante para novas peças</dt><dd>' + h(limite != null && precoConhecido ? valorMonetario(limite - gasto) : "Indisponível")
      + '</dd></div><div><dt>Total cadastrado da build antes</dt><dd>' + h(moeda(antes.preco))
      + '</dd></div><div><dt>Total cadastrado da build na prévia</dt><dd>' + h(moeda(depois.preco))
      + '</dd></div><div><dt>Diferença no total</dt><dd>' + h((delta > 0 ? "+" : delta < 0 ? "−" : "") + valorMonetario(Math.abs(delta)))
      + '</dd></div></dl><p class="planning-help">Totais consideram as quantidades e o custo de rede já previsto. Peças próprias ou sem preço podem deixar o total parcial. Economia não indica aumento de desempenho.</p>'
      + (pendencias.length ? '<div class="upgrade-real-validation"><h4>Pendências e verificações</h4><ul>'
        + [...new Set(pendencias)].map(texto => '<li>' + h(texto) + '</li>').join("") + '</ul></div>'
        : '<p class="planning-help">Nenhum conflito detectado nas verificações disponíveis do catálogo.</p>');
    let motivo = build.travada ? MOTIVO_TRAVA : aplicando ? "Aguarde a aplicação das alterações." : !trocas.size ? "Adicione pelo menos uma candidata à prévia." : "";
    if (!motivo) { try { simular(trocas); } catch (erro) { motivo = erro.message; } }
    aplicar.disabled = Boolean(motivo);
    if (motivo) aplicar.dataset.disabledReason = motivo; else delete aplicar.dataset.disabledReason;
    motivoAplicar.textContent = motivo || "Confira as diferenças e confirme em Aplicar alterações.";
  }

  function renderizar() {
    const foco = document.activeElement;
    const restaurar = resultados.contains(foco) || previa.contains(foco);
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
        || dialogo.querySelector("#upgrade-real-preview-title");
      proximoFoco.focus({preventScroll:true});
    }
  }

  campoBudget.addEventListener("input",() => {
    if (aplicando) return;
    renderizar();
    informar(budget() == null ? MOTIVO_BUDGET : "Budget atualizado para esta prévia. As escolhas serão validadas juntas.");
  });
  dialogo.addEventListener("change",evento => {
    if (aplicando) return;
    const caixa = evento.target;
    if (caixa.name === "upgrade-real-category") {
      if (caixa.checked) categorias.add(caixa.value);
      else { categorias.delete(caixa.value); trocas.delete(caixa.value); }
      informar("Categorias atualizadas. Desmarcar uma categoria descarta a troca dela.");
    } else if (caixa === ordem) ordem.value = "preco";
    else if (caixa !== campoBudget) return;
    renderizar();
  });
  dialogo.addEventListener("click",async evento => {
    const botao = evento.target.closest("button");
    if (!botao || botao.disabled || aplicando || aplicada || !dialogo.open) return;
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
        informar("Candidata adicionada à prévia. Confirme em Aplicar alterações para alterar a build.");
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
      informar("Não foi possível aplicar esta combinação: " + (erro?.message || "Tente novamente."));
    }
  });
  dialogo.addEventListener("cancel",evento => {
    evento.preventDefault();
    if (!aplicando) dialogo.close("cancelar");
  });
  dialogo.addEventListener("close",() => { trocas.clear(); },{once:true});
  renderizar();
  return dialogo;
}
