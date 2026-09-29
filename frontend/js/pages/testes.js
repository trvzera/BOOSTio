import { carregarCatalogo, htmlSeguro as h, moeda, nomePeca } from "../build/catalogo.js";
import { buildsLocais, normalizarBuild, categoriasMultiplas, itensCategoria, itensSelecionados,
  informacoesRam, informacoesArmazenamento } from "../build/estado.js";
import { avaliarBuild } from "../build/compatibilidade.js";
import { iniciarTesteMelhorias } from "./test-upgrades.js";

const CHAVE_BUDGET_TESTE = "boostio:teste-budget";
const CHAVE_BUDGET_NOVAS = "boostio:teste-budget-novas";
const EXEMPLOS = [
  { id:"teste-am4", titulo:"Exemplo AM4", descricao:"Build demonstrativa com Ryzen 7 5700X e RTX 3060.",
    pecas:["SEED-CPU-02","SEED-MB-03","SEED-RAM-02","SEED-SSD-02","SEED-GPU-02","SEED-PSU-01","SEED-CASE-01","SEED-FAN-01","SEED-ACOOL-01"] },
  { id:"teste-am5", titulo:"Exemplo AM5", descricao:"Build demonstrativa com Ryzen 5 7600 e RTX 4060.",
    pecas:["SEED-CPU-03","SEED-MB-17","SEED-RAM-03","SEED-SSD-04","SEED-GPU-04","SEED-PSU-02","SEED-CASE-02","SEED-FAN-02"] },
  { id:"teste-am5-2", titulo:"Exemplo AM5 avançado", descricao:"Build demonstrativa com Ryzen 7 7700X e RTX 5060.",
    pecas:["SEED-CPU-04","SEED-MB-08","SEED-RAM-05","SEED-SSD-02","SEED-GPU-06","SEED-PSU-03","SEED-CASE-02","SEED-FAN-03","SEED-ACOOL-02"] },
];

function montarExemplo(exemplo,catalogo) {
  const componentes = {};
  for (const id of exemplo.pecas) {
    const peca = catalogo.find(item => item.id === id);
    if (!peca) throw new Error("A peça " + id + " não foi encontrada no catálogo demonstrativo.");
    componentes[peca.categoria] = categoriasMultiplas.has(peca.categoria)
      ? [{id,quantidade:1}] : {id,quantidade:1};
  }
  return normalizarBuild({...exemplo,componentes});
}

function valorBudget() {
  try {
    const salvo = sessionStorage.getItem(CHAVE_BUDGET_TESTE);
    if (salvo == null) return null;
    const valor = Number(salvo);
    return Number.isFinite(valor) && valor >= 0 ? valor : null;
  } catch { return null; }
}

document.addEventListener("DOMContentLoaded", async () => {
  const opcoes = document.querySelector("#compare-options");
  const prontas = document.querySelector("#ready-builds");
  const resultadoComparacao = document.querySelector("#compare-results");
  const dialogoComparacao = document.querySelector("#compare-dialog");
  const selecionarComparacao = document.querySelector("#compare-selection");
  const feedbackComparacao = document.querySelector("#compare-feedback");
  const feedbackBudget = document.querySelector("#budget-feedback");
  const feedbackMelhorias = document.querySelector("#upgrade-feedback");
  const budgetInput = document.querySelector("#test-budget");
  const selecionarDesempenho = document.querySelector("#performance-build");
  const detalhesDesempenho = document.querySelector("#performance-details");
  const feedbackDesempenho = document.querySelector("#performance-feedback");
  const usarBudgetNovas = document.querySelector("#budget-use-new");
  const previaBudget = document.querySelector("#budget-new-build-preview");
  const budgetNovaBuild = document.querySelector("#budget-new-build-input");
  const valorNovaBuild = document.querySelector("#budget-new-build-value");
  const comparar = document.querySelector("#compare-button");
  const selecionadas = new Set();
  const informar = (elemento,mensagem,tom) => {
    elemento.textContent = mensagem;
    if (tom) elemento.dataset.tone = tom;
    else delete elemento.dataset.tone;
  };

  try {
    const catalogo = await carregarCatalogo();
    const exemplos = EXEMPLOS.map(exemplo => montarExemplo(exemplo,catalogo));
    const salvas = buildsLocais().flatMap(valor => {
      try { return [normalizarBuild(valor)]; } catch { return []; }
    });
    const idSolicitado = new URLSearchParams(location.search).get("build");
    let rascunho = null;
    if (idSolicitado && !salvas.some(build => build.id === idSolicitado)) {
      try {
        const valor = JSON.parse(localStorage.getItem("boostio:rascunhos-build") || "{}")[idSolicitado];
        if (valor) rascunho = normalizarBuild({...valor,id:idSolicitado});
      } catch { /* A prévia continua disponível com as builds de exemplo. */ }
    }
    const builds = [...salvas,...(rascunho ? [rascunho] : []),
      ...exemplos.filter(exemplo => !salvas.some(build => build.id === exemplo.id) && exemplo.id !== rascunho?.id)];
    const porId = new Map(builds.map(build => [build.id,build]));
    const pecaDaBuild = (build,categoria) => {
      const item = itensCategoria(build,categoria)[0];
      return catalogo.find(peca => peca.categoria === categoria && peca.id === item?.id);
    };
    const nomeDaPeca = (build,categoria) => {
      const peca = pecaDaBuild(build,categoria);
      return peca ? nomePeca(peca) : itensCategoria(build,categoria)[0]?.proprio || "Não selecionado";
    };
    const estado = build => {
      const avaliacao = avaliarBuild(build,catalogo);
      const cpu = pecaDaBuild(build,"processador"), gpu = pecaDaBuild(build,"placa_video");
      const ram = informacoesRam(build,catalogo), discos = informacoesArmazenamento(build,catalogo);
      const totalConfiavel = !avaliacao.faltam.length && itensSelecionados(build,catalogo).every(item => Boolean(item.peca));
      return {build,avaliacao,cpu,gpu,ram,discos,totalConfiavel};
    };
    const dados = new Map(builds.map(build => [build.id,estado(build)]));
    const status = avaliacao => ({completa:"Completa",incompleta:"Incompleta",atencao:"Com atenção",erro:"Com erro"})[avaliacao.status];

    selecionarDesempenho.innerHTML = builds.map(build => '<option value="' + h(build.id) + '">' + h(build.titulo) + '</option>').join("");
    if (idSolicitado && porId.has(idSolicitado)) selecionarDesempenho.value = idSolicitado;
    const testeTopo = document.querySelector("#preview-builder-test");
    const checarDesempenho = document.querySelector("#performance-check");
    const atualizarNomePreview = () => {
      const item = dados.get(selecionarDesempenho.value);
      const completo = item?.avaliacao.total > 0 && item.avaliacao.preenchidos === item.avaliacao.total;
      const percentual = item?.avaliacao.total ? Math.round(item.avaliacao.preenchidos / item.avaliacao.total * 100) : 0;
      document.querySelector("#preview-build-progress").textContent = (item?.build.titulo || "Build") + " · " + percentual + "% das peças selecionadas";
      testeTopo.disabled = !completo;
      checarDesempenho.disabled = !completo;
      detalhesDesempenho.hidden = true;
      informar(feedbackDesempenho,completo ? "Build 100% preenchida. Confira os dados para a futura estimativa." :
        "Complete 100% das peças para habilitar o teste.");
    };
    selecionarDesempenho.addEventListener("change",atualizarNomePreview);
    atualizarNomePreview();
    function verificarDadosDesempenho() {
      const item = dados.get(selecionarDesempenho.value);
      if (!item || item.avaliacao.preenchidos !== item.avaliacao.total) return;
      const resolucao = document.querySelector("#performance-resolution").value;
      const pendencias = [];
      if (!item.cpu) pendencias.push("Identifique o processador no catálogo.");
      if (!item.gpu) pendencias.push(item.cpu?.videointegrado ?
        "Identifique o modelo da GPU integrada entre os modelos aceitos pelo provedor." : "Identifique a placa de vídeo no catálogo.");
      if (!item.ram.itens.some(ram => ram.peca?.frequencia_mhz)) pendencias.push("Identifique a frequência da memória RAM.");
      if (item.avaliacao.erros.length) pendencias.push("Resolva os erros de compatibilidade da build antes da estimativa.");
      detalhesDesempenho.innerHTML = '<div class="test-performance-specs"><div><span>Processador</span><strong>' + h(nomeDaPeca(item.build,"processador")) +
        '</strong></div><div><span>Placa de vídeo / GPU</span><strong>' + h(item.gpu ? nomeDaPeca(item.build,"placa_video") : item.cpu?.videointegrado ? "Vídeo integrado · modelo a mapear" : "Não selecionada") +
        '</strong></div><div><span>Memória</span><strong>' + (item.ram.capacidade || 0) + ' GB · ' + h(item.ram.itens[0]?.peca?.frequencia_mhz || "frequência não identificada") +
        ' MHz</strong></div><div><span>Resolução</span><strong>' + h(resolucao) + '</strong></div></div>' +
        (pendencias.length ? '<ul class="test-performance-pending">' + pendencias.map(texto => '<li>' + h(texto) + '</li>').join("") + '</ul>' :
          '<p class="test-performance-ready">Os dados básicos estão presentes. Ainda será necessário confirmar se os modelos de CPU e GPU existem nas listas do provedor.</p>') +
        '<div class="test-performance-empty"><strong>FPS estimado: indisponível</strong><span>Os jogos e seus resultados aparecerão aqui somente após a integração com uma fonte verificada. Mesmo com dados disponíveis, o FPS será apenas uma estimativa da combinação CPU + GPU; memória, drivers, temperatura e configurações do jogo podem alterar o desempenho real.</span></div>';
      detalhesDesempenho.hidden = false;
      informar(feedbackDesempenho,pendencias.length ? "Há dados ou correções pendentes nesta build." :
        "Dados básicos encontrados; a estimativa de FPS ainda depende de uma API de benchmarks.",pendencias.length ? "error" : undefined);
      document.querySelector("#teste-desempenho .test-performance-panel").scrollIntoView({block:"start",behavior:"smooth"});
    }
    checarDesempenho.addEventListener("click",verificarDadosDesempenho);
    testeTopo.addEventListener("click",verificarDadosDesempenho);

    const demoComparacao = salvas.length < 2;
    const baseComparacao = demoComparacao ? exemplos : salvas;
    const terceiraDemo = document.querySelector("#compare-third");
    const listaComparacao = document.querySelector("#compare-build-list");
    const confirmarComparacao = document.querySelector("#compare-confirm");
    terceiraDemo.closest("label").hidden = !demoComparacao;
    const disponiveis = () => demoComparacao && !terceiraDemo.checked ? baseComparacao.slice(0,2) : baseComparacao;
    const descricaoComparacao = build => {
      const item = dados.get(build.id);
      return '<strong class="font-1-m-b">' + h(build.titulo) + '</strong><span class="font-2-xs">' +
        h(nomeDaPeca(build,"processador")) + ' · ' + h(nomeDaPeca(build,"placa_video")) +
        '</span><em class="font-1-s">' + moeda(item.avaliacao.preco) + '</em>';
    };
    function atualizarListaComparacao() {
      const lista = disponiveis();
      comparar.disabled = lista.length < 2;
      document.querySelector("#compare-available").textContent = lista.length + " builds " +
        (demoComparacao ? "demonstrativas" : "salvas neste navegador") + " disponíveis para comparar.";
      listaComparacao.innerHTML = lista.map(build => '<div class="test-compare-build-item">' + descricaoComparacao(build) + '</div>').join("");
      opcoes.innerHTML = lista.map(build => '<label class="test-choice font-2-xs"><input type="checkbox" value="' + h(build.id) + '"' +
        (selecionadas.has(build.id) ? ' checked' : '') + '><span class="test-choice-copy">' + descricaoComparacao(build) + '</span></label>').join("");
    }
    function atualizarSelecao() {
      opcoes.querySelectorAll('input[type="checkbox"]').forEach(caixa => { caixa.checked = selecionadas.has(caixa.value); });
      confirmarComparacao.disabled = selecionadas.size < 2;
      informar(feedbackComparacao,selecionadas.size < 2 ? "Selecione pelo menos duas builds." :
        selecionadas.size + " builds selecionadas. Prontas para comparar.");
    }
    function mostrarSelecao() {
      resultadoComparacao.hidden = true;
      selecionarComparacao.hidden = false;
      atualizarListaComparacao();
      atualizarSelecao();
    }
    function renderizarComparacao() {
      if (selecionadas.size < 2) return;
      const itens = disponiveis().filter(build => selecionadas.has(build.id)).map(build => dados.get(build.id));
      const totais = itens.filter(item => item.totalConfiavel);
      const menorPreco = totais.length ? Math.min(...totais.map(item => item.avaliacao.preco)) : null;
      const menorConsumo = totais.length ? Math.min(...totais.map(item => item.avaliacao.watts)) : null;
      const menorPrecoItem = totais.find(item => item.avaliacao.preco === menorPreco);
      const menorConsumoItem = totais.find(item => item.avaliacao.watts === menorConsumo);
      const campo = (rotulo,valor,detalhe = "",destaque = false) => '<div class="test-compare-field' + (destaque ? ' is-best' : '') + '"><span>' + rotulo + '</span><strong>' + valor + '</strong>' + (detalhe ? '<small>' + detalhe + '</small>' : '') + '</div>';
      const colunas = itens.map(item => {
        const maisBarata = item.totalConfiavel && item.avaliacao.preco === menorPreco;
        const menosWatts = item.totalConfiavel && item.avaliacao.watts === menorConsumo;
        const precoDetalhe = !item.totalConfiavel ? "Total parcial · faltam peças ou preços" : maisBarata ? "Menor preço entre as builds completas" :
          "+" + moeda(item.avaliacao.preco - menorPreco) + " frente à mais barata";
        const wattsDetalhe = !item.totalConfiavel ? "Consumo parcial" : menosWatts ? "Menor consumo estimado" :
          "+" + (item.avaliacao.watts - menorConsumo) + " W frente à mais econômica";
        const compatibilidade = item.avaliacao.erros.length ? item.avaliacao.erros.length + " erro(s) para corrigir" :
          item.avaliacao.faltam.length ? item.avaliacao.faltam.length + " peça(s) pendentes" :
          item.avaliacao.avisos.length ? item.avaliacao.avisos.length + " aviso(s)" : "Sem pendências identificadas";
        return '<article class="test-compare-card" aria-label="Comparação da build ' + h(item.build.titulo) + '"><div class="test-compare-card-head"><div class="test-compare-tags">' +
          (maisBarata ? '<span>Menor preço</span>' : '') + (menosWatts ? '<span>Menor consumo</span>' : '') +
          (!item.totalConfiavel ? '<span class="is-partial">Build parcial</span>' : '') + '</div><h4 class="font-1-m-b">' + h(item.build.titulo) +
          '</h4><p class="font-2-xs">' + h(item.build.descricao || "Configuração sem descrição") + '</p>' +
          (selecionadas.size > 2 ? '<button type="button" class="test-compare-remove" data-compare-remove="' + h(item.build.id) + '" aria-label="Remover build ' + h(item.build.titulo) + ' da comparação">Remover build</button>' : '') + '</div>' +
          campo("Preço cadastrado",moeda(item.avaliacao.preco),precoDetalhe,maisBarata) +
          campo("Consumo estimado",item.avaliacao.watts + " W",wattsDetalhe,menosWatts) +
          campo("Processador",h(nomeDaPeca(item.build,"processador")),item.cpu?.thread ? h(item.cpu.thread) + " threads" : "") +
          campo("Placa de vídeo",h(nomeDaPeca(item.build,"placa_video")),item.gpu?.memoria_gb ? h(item.gpu.memoria_gb) + " GB de VRAM" : "") +
          campo("Memória RAM",item.ram.capacidade ? item.ram.capacidade + " GB" : "Não identificada",item.ram.usados ? item.ram.usados + " pentes" : "") +
          campo("Armazenamento",item.discos.capacidade ? item.discos.capacidade + " GB" : "Não identificado") +
          campo("Compatibilidade",status(item.avaliacao),compatibilidade) +
          campo("Desempenho em jogos","Ainda não estimado","Aguardando uma fonte de benchmarks verificada") + '</article>';
      }).join("");
      const podeAdicionar = selecionadas.size === 2 && baseComparacao.some(build => !selecionadas.has(build.id));
      resultadoComparacao.innerHTML = '<div class="test-compare-results-head"><h3 class="font-1-l">O que muda entre elas</h3>' +
        (podeAdicionar ? '<button type="button" class="btn-secondary" id="compare-add" aria-label="Adicionar outra build à comparação">Adicionar outra build</button>' : '') +
        '</div><div class="test-compare-summary font-2-xs"><p>Mais acessível<strong>' +
        h(menorPrecoItem?.build.titulo || "Indisponível") + '</strong><span>' + (menorPreco == null ? "Nenhum total completo" : moeda(menorPreco)) +
        '</span></p><p>Menor consumo<strong>' + h(menorConsumoItem?.build.titulo || "Indisponível") + '</strong><span>' +
        (menorConsumo == null ? "Nenhum total completo" : menorConsumo + " W estimados") +
        '</span></p><p>Melhor desempenho<strong>Ainda indisponível</strong><span>Depende de benchmarks comparáveis da API</span></p></div><p class="test-swipe-hint font-2-xs">Deslize as colunas para ver todas as builds.</p><div class="test-compare-columns" tabindex="0" role="group" aria-label="Builds comparadas lado a lado">' +
        colunas + '</div><p class="test-muted font-2-xs">Preços do catálogo são demonstrativos e o consumo não é uma medição real. Nenhuma build recebe uma classificação de desempenho sem benchmark comparável.</p>';
      selecionarComparacao.hidden = true;
      resultadoComparacao.hidden = false;
      dialogoComparacao.scrollTop = 0;
    }
    comparar.addEventListener("click",() => {
      const lista = disponiveis();
      if (lista.length < 2) return;
      selecionadas.clear();
      if (lista.length === 2) lista.forEach(build => selecionadas.add(build.id));
      dialogoComparacao.showModal();
      if (lista.length === 2) renderizarComparacao();
      else mostrarSelecao();
    });
    document.querySelector("#compare-close").addEventListener("click",() => dialogoComparacao.close());
    dialogoComparacao.addEventListener("click",evento => { if (evento.target === dialogoComparacao) dialogoComparacao.close(); });
    terceiraDemo.addEventListener("change",() => { selecionadas.clear(); atualizarListaComparacao(); });
    opcoes.addEventListener("change",evento => {
      const caixa = evento.target.closest('input[type="checkbox"]');
      if (!caixa) return;
      if (caixa.checked && selecionadas.size >= 3) {
        caixa.checked = false;
        informar(feedbackComparacao,"O comparador aceita no máximo três builds.","error");
        return;
      }
      if (caixa.checked) selecionadas.add(caixa.value);
      else selecionadas.delete(caixa.value);
      atualizarSelecao();
    });
    confirmarComparacao.addEventListener("click",renderizarComparacao);
    resultadoComparacao.addEventListener("click",evento => {
      if (evento.target.closest("#compare-add")) {
        if (demoComparacao) terceiraDemo.checked = true;
        mostrarSelecao();
        return;
      }
      const botao = evento.target.closest("[data-compare-remove]");
      if (botao && selecionadas.size > 2) {
        selecionadas.delete(botao.dataset.compareRemove);
        renderizarComparacao();
      }
    });
    atualizarListaComparacao();

    prontas.innerHTML = exemplos.map(build => {
      const item = dados.get(build.id);
      const lista = EXEMPLOS.find(exemplo => exemplo.id === build.id).pecas.map(id => {
        const peca = catalogo.find(produto => produto.id === id);
        return '<li>' + h(nomePeca(peca)) + '</li>';
      }).join("");
      return '<article class="test-demo-card glass-card"><span class="test-label font-1-xs">Exemplo · ' + status(item.avaliacao) + '</span><h3 class="font-1-m-b">' + h(build.titulo) +
        '</h3><p class="font-2-xs">' + h(build.descricao) + '</p><strong class="font-1-m">' + moeda(item.avaliacao.preco) + '</strong><small class="test-muted">' + item.avaliacao.watts +
        ' W estimados · preço demonstrativo</small><details class="font-2-xs"><summary>Ver peças</summary><ul>' + lista + '</ul></details></article>';
    }).join("");

    const melhorias = iniciarTesteMelhorias({builds,catalogo,valorBudget,informar});
    const atualizarPreviaBudget = () => {
      const valor = valorBudget();
      const disponivel = valor != null && valor > 0;
      let marcado = false;
      try { marcado = sessionStorage.getItem(CHAVE_BUDGET_NOVAS) === "1"; } catch { /* Sem persistência na sessão. */ }
      usarBudgetNovas.disabled = !disponivel;
      usarBudgetNovas.dataset.disabledReason = "Registre um budget maior que zero para habilitar esta opção.";
      usarBudgetNovas.checked = disponivel && marcado;
      budgetNovaBuild.max = String(Math.max(10000,Math.ceil((valor || 0) / 1000) * 1000));
      budgetNovaBuild.value = usarBudgetNovas.checked ? String(valor) : "0";
      valorNovaBuild.value = moeda(Number(budgetNovaBuild.value));
      previaBudget.textContent = usarBudgetNovas.checked ? "Valor do perfil aplicado como limite inicial. Você pode mudar apenas nesta build." :
        "Sem budget aplicado automaticamente. Ajuste o range para definir um valor nesta build.";
    };
    const registrado = valorBudget();
    if (registrado != null) {
      budgetInput.value = String(registrado);
      informar(feedbackBudget,moeda(registrado) + " registrados apenas nesta sessão de teste.","success");
      melhorias.atualizarBudget();
    }
    atualizarPreviaBudget();
    document.querySelector("#budget-save").addEventListener("click",() => {
      const valor = Number(budgetInput.value);
      if (budgetInput.value.trim() === "" || !Number.isFinite(valor) || valor < 0 || valor > 1000000) {
        informar(feedbackBudget,"Informe um valor entre R$ 0 e R$ 1.000.000.","error");
        return;
      }
      try {
        sessionStorage.setItem(CHAVE_BUDGET_TESTE,String(valor));
        if (valor === 0) sessionStorage.setItem(CHAVE_BUDGET_NOVAS,"0");
        informar(feedbackBudget,moeda(valor) + " registrados apenas nesta sessão de teste.","success");
        atualizarPreviaBudget();
        melhorias.atualizarBudget();
      } catch {
        informar(feedbackBudget,"O navegador não permitiu guardar o valor nesta sessão.","error");
      }
    });
    usarBudgetNovas.addEventListener("change",() => {
      try {
        sessionStorage.setItem(CHAVE_BUDGET_NOVAS,usarBudgetNovas.checked ? "1" : "0");
        atualizarPreviaBudget();
      } catch {
        usarBudgetNovas.checked = false;
        informar(feedbackBudget,"O navegador não permitiu guardar esta preferência na sessão.","error");
      }
    });
    budgetNovaBuild.addEventListener("input",() => {
      const valor = Number(budgetNovaBuild.value);
      valorNovaBuild.value = moeda(valor);
      previaBudget.textContent = "Esta build usaria " + moeda(valor) + ". O budget registrado no perfil não muda.";
    });
  } catch (erro) {
    opcoes.textContent = "Não foi possível carregar os dados de teste: " + erro.message;
    prontas.textContent = "Os exemplos não estão disponíveis neste momento.";
    comparar.disabled = true;
    informar(feedbackComparacao,"O catálogo demonstrativo não carregou.","error");
    informar(feedbackMelhorias,"O catálogo demonstrativo não carregou.","error");
  }
});
