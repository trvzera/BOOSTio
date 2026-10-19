import { htmlSeguro as h, moeda, nomePeca } from "../build/catalogo.js";
import { itensCategoria } from "../build/estado.js";
import { pecaCompativel, selecionarPecaCompativel } from "../build/compatibilidade.js";

const CATEGORIAS = [
  { id:"processador", nome:"Processador" },
  { id:"placa_video", nome:"Placa de vídeo" },
];

// Este módulo só altera uma cópia em memória. A integração com builds salvas virá depois dos testes.
export function iniciarTesteMelhorias({builds,catalogo,valorBudget,informar}) {
  const seletor = document.querySelector("#upgrade-build");
  const resultados = document.querySelector("#upgrade-results");
  const previa = document.querySelector("#upgrade-preview");
  const feedback = document.querySelector("#upgrade-feedback");
  const checkboxes = [...document.querySelectorAll('input[name="upgrade-category"]')];
  const porId = new Map(builds.map(build => [build.id,build]));
  let original = builds[0];
  let simulada = structuredClone(original);
  let trocas = new Map();

  const pecaAtual = (build,categoria) => {
    const item = itensCategoria(build,categoria)[0];
    return catalogo.find(peca => peca.categoria === categoria && peca.id === item?.id);
  };
  const nomeAtual = (build,categoria) => nomePeca(pecaAtual(build,categoria)) || "Não identificada";
  const gasto = escolhas => [...escolhas.values()].reduce((total,peca) => total + Number(peca.preco || 0),0);
  const selecionadas = () => checkboxes.filter(caixa => caixa.checked).map(caixa => caixa.value);

  function renderizarPrevia() {
    const valor = valorBudget();
    const total = gasto(trocas);
    previa.innerHTML = '<div class="test-upgrade-preview-top"><span class="test-label font-1-xs">Build de teste · não salva</span><strong class="font-1-m-b">' + h(original.titulo) +
      '</strong></div><div class="test-upgrade-preview-parts"><span>Processador<strong>' + h(nomeAtual(simulada,"processador")) +
      '</strong></span><span>Placa de vídeo<strong>' + h(nomeAtual(simulada,"placa_video")) +
      '</strong></span></div><p class="font-2-xs">Trocas escolhidas: <strong>' + moeda(total) +
      '</strong>' + (valor != null ? ' · restante no budget: <strong>' + moeda(Math.max(0,valor - total)) + '</strong>' : '') + '</p>';
  }

  function montarSimulacao(escolhas) {
    let proxima = structuredClone(original);
    proxima.travada = false;
    for (const {id} of CATEGORIAS) {
      const peca = escolhas.get(id);
      if (!peca) continue;
      const componentes = {...proxima.componentes};
      delete componentes[id];
      proxima = selecionarPecaCompativel({...proxima,componentes},peca,catalogo);
    }
    return proxima;
  }

  function buscar() {
    resultados.hidden = true;
    const budget = valorBudget();
    if (budget == null || budget <= 0) {
      informar(feedback,"Registre um budget maior que zero antes da busca.","error");
      return;
    }
    const categorias = selecionadas();
    if (!categorias.length) {
      informar(feedback,"Selecione pelo menos uma peça para avaliar.","error");
      return;
    }
    const grupos = categorias.map(categoria => {
      const rotulo = CATEGORIAS.find(item => item.id === categoria).nome;
      const atual = pecaAtual(simulada,categoria);
      if (!atual) return '<section class="test-candidate-group"><h3 class="font-1-m-b">' + rotulo + '</h3><p class="font-2-xs test-muted">Identifique esta peça no catálogo para testar a troca.</p></section>';
      const componentes = {...simulada.componentes};
      delete componentes[categoria];
      const base = {...simulada,travada:false,componentes};
      const disponivelParaCategoria = budget - gasto(trocas) + Number(trocas.get(categoria)?.preco || 0);
      const candidatas = catalogo.filter(peca => peca.categoria === categoria && peca.id !== pecaAtual(original,categoria)?.id &&
        !peca.esgotado && Number(peca.preco) <= disponivelParaCategoria && pecaCompativel(base,peca,catalogo))
        .sort((a,b) => a.preco - b.preco).slice(0,3);
      if (!candidatas.length) return '<section class="test-candidate-group"><h3 class="font-1-m-b">' + rotulo + '</h3><p class="font-2-xs test-muted">Nenhuma candidata compatível foi encontrada no catálogo demonstrativo.</p></section>';
      return '<section class="test-candidate-group"><h3 class="font-1-m-b">' + rotulo + '</h3><div class="test-candidate-list">' +
        candidatas.map(peca => {
          const escolhida = trocas.get(categoria)?.id === peca.id;
          const detalhe = escolhida ? ' · na build de teste' : ' · clique para testar';
          const textoVisivel = nomePeca(peca) + ' ' + moeda(peca.preco) + detalhe;
          return '<button type="button" class="test-candidate' + (escolhida ? ' is-selected' : '') + '" data-upgrade-pick="' + h(peca.id) +
            '" data-upgrade-category="' + categoria + '" aria-label="' + h(textoVisivel) + '. Adicionar à build de teste" aria-pressed="' + escolhida +
            '"><strong>' + h(nomePeca(peca)) + '</strong> <span>' + moeda(peca.preco) + detalhe + '</span></button>';
        }).join("") + '</div></section>';
    });
    resultados.innerHTML = grupos.join("");
    resultados.hidden = false;
    informar(feedback,"Opções compatíveis ordenadas por menor preço dentro do budget disponível. Clique para testar a troca.");
  }

  seletor.innerHTML = builds.map(build => '<option value="' + h(build.id) + '">' + h(build.titulo) + '</option>').join("");
  renderizarPrevia();
  seletor.addEventListener("change",() => {
    original = porId.get(seletor.value);
    simulada = structuredClone(original);
    trocas = new Map();
    resultados.hidden = true;
    renderizarPrevia();
    informar(feedback,"Build de teste alterada. Escolha as peças que deseja avaliar.");
  });
  checkboxes.forEach(caixa => caixa.addEventListener("change",() => {
    if (!caixa.checked && trocas.has(caixa.value)) {
      trocas.delete(caixa.value);
      simulada = montarSimulacao(trocas);
      renderizarPrevia();
    }
    if (!resultados.hidden) buscar();
  }));
  document.querySelector("#upgrade-search").addEventListener("click",buscar);
  resultados.addEventListener("click",evento => {
    const botao = evento.target.closest("[data-upgrade-pick]");
    if (!botao) return;
    const peca = catalogo.find(item => item.id === botao.dataset.upgradePick && item.categoria === botao.dataset.upgradeCategory);
    if (!peca) return;
    const propostas = new Map(trocas);
    propostas.set(peca.categoria,peca);
    if (gasto(propostas) > valorBudget()) {
      informar(feedback,"As peças escolhidas juntas ultrapassam o budget. Selecione uma opção mais barata ou aumente o valor.","error");
      return;
    }
    try {
      const proxima = montarSimulacao(propostas);
      trocas = propostas;
      simulada = proxima;
      renderizarPrevia();
      buscar();
      informar(feedback,nomePeca(peca) + " entrou na build de teste. A build real não foi alterada.","success");
    } catch (erro) {
      informar(feedback,"Esta combinação não pode ser aplicada: " + erro.message,"error");
    }
  });

  return {
    atualizarBudget() {
      trocas = new Map();
      simulada = structuredClone(original);
      resultados.hidden = true;
      renderizarPrevia();
      const valor = valorBudget();
      informar(feedback,valor > 0 ? "Budget de " + moeda(valor) + " disponível. Busque peças para testar trocas." :
        "Registre um budget maior que zero antes da busca.");
    },
  };
}
