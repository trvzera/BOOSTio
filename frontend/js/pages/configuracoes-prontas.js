import "../header.js";
import "../auth/auth.js";
import { carregarCatalogo, categorias, htmlSeguro as h, moeda, nomePeca } from "../build/catalogo.js";
import { buildsLocais, CHAVE_PERFIL_LOCAL, guardarRascunho, itensSelecionados,
  informacoesRam, informacoesArmazenamento } from "../build/estado.js";
import { modelosProntos, copiarModelo } from "../build/modelos.js";
import { avaliarBuild } from "../build/compatibilidade.js";
import { navegarPara } from "../components/page-loading.js";
import { planejamentoLocal } from "../build/planejamento.js";

const LIMITE_LOCAL = 3;
const MOTIVO_COTA = "Limite de três builds salvas neste navegador atingido. Exclua uma build em Minhas builds para usar um modelo como base.";
const STATUS = {completa:"Peças preenchidas", incompleta:"Peças pendentes", atencao:"Requer atenção", erro:"Há incompatibilidades"};

document.addEventListener("DOMContentLoaded", async () => {
  const formulario = document.querySelector("#prontas-filtros");
  const objetivo = document.querySelector("#prontas-objetivo");
  const budget = document.querySelector("#prontas-budget");
  const lista = document.querySelector("#prontas-lista");
  const contador = document.querySelector("#prontas-contador");
  const feedback = document.querySelector("#prontas-feedback");
  const cota = document.querySelector("#prontas-cota");
  let abrindo = false;

  function informar(texto, erro = false) {
    feedback.textContent = texto;
    feedback.dataset.tone = erro ? "error" : "info";
  }

  function atualizarCota() {
    const usadas = buildsLocais().length;
    const cheia = usadas >= LIMITE_LOCAL;
    cota.textContent = usadas + "/" + LIMITE_LOCAL + " builds salvas neste navegador";
    cota.dataset.cheia = String(cheia);
    lista.querySelectorAll("[data-usar-modelo]").forEach(botao => {
      botao.dataset.disabledReason = cheia ? MOTIVO_COTA : "Aguarde a abertura do rascunho.";
      botao.disabled = cheia || abrindo;
      if (cheia) botao.title = MOTIVO_COTA;
      else botao.removeAttribute("title");
    });
    return cheia;
  }

  formulario.addEventListener("submit",evento => evento.preventDefault());
  window.addEventListener("storage",evento => {
    if (evento.key === CHAVE_PERFIL_LOCAL || evento.key === null) atualizarCota();
  });
  window.addEventListener("pageshow",() => { abrindo = false; atualizarCota(); });
  window.addEventListener("focus",atualizarCota);
  atualizarCota();

  try {
    const catalogo = await carregarCatalogo();
    const modelos = modelosProntos(catalogo).map(build => ({build,avaliacao:avaliarBuild(build,catalogo)}));
    const objetivos = new Map(modelos.map(({build}) => [build.objetivo,build.metadados.objetivoRotulo]));
    objetivo.innerHTML = '<option value="">Todos os objetivos</option>' + [...objetivos].map(([valor,rotulo]) =>
      '<option value="' + h(valor) + '">' + h(rotulo) + '</option>').join("");

    function listaMensagens(titulo, mensagens) {
      return mensagens.length ? '<div class="prontas-pendencias"><h4>' + h(titulo) + '</h4><ul>' +
        mensagens.map(texto => '<li>' + h(texto) + '</li>').join("") + '</ul></div>' : "";
    }

    function card({build,avaliacao}) {
      const ram = informacoesRam(build,catalogo);
      const discos = informacoesArmazenamento(build,catalogo);
      const pecas = itensSelecionados(build,catalogo).map(({categoria,item,peca}) => {
        const unidade = categoria === "memoria_ram" || (categoria === "fan" && Number(peca?.quantidade) > 1) ? "kit(s)" : "unidade(s)";
        const detalhe = categoria === "memoria_ram" && peca ? " · " + item.quantidade * (peca.quantidade_pentes || 1) + " pente(s)"
          : categoria === "fan" && peca ? " · " + item.quantidade * (peca.quantidade || 1) + " fan(s)" : "";
        return '<li><div><span>' + h(categorias.find(c => c.id === categoria)?.nome || categoria) + '</span><strong>' +
          h(peca ? nomePeca(peca) : item.proprio || item.id) + '</strong><small>' + item.quantidade + ' ' + unidade + h(detalhe) +
          '</small></div><span class="prontas-preco-peca">' + (peca ? moeda(peca.preco * item.quantidade) : "Preço indisponível") + '</span></li>';
      }).join("");
      const semConflitos = !avaliacao.erros.length && !avaliacao.faltam.length && !avaliacao.avisos.length;
      return '<article class="prontas-card glass-card" aria-labelledby="titulo-' + h(build.id) + '">' +
        '<div class="prontas-tags"><span>' + h(build.metadados.plataforma) + '</span><span>' + h(build.metadados.objetivoRotulo) + '</span></div>' +
        '<h2 id="titulo-' + h(build.id) + '">' + h(build.titulo) + '</h2><p class="prontas-descricao">' + h(build.descricao) + '</p>' +
        '<dl class="prontas-resumo"><div><dt>Memória RAM</dt><dd>' + ram.capacidade + ' GB · ' + ram.usados + ' pente(s)</dd></div>' +
        '<div><dt>Armazenamento</dt><dd>' + discos.capacidade + ' GB</dd></div><div><dt>Consumo estimado</dt><dd>' + avaliacao.watts + ' W</dd></div></dl>' +
        '<div class="prontas-total"><span>Total demonstrativo</span><strong>' + moeda(avaliacao.preco) + '</strong><small>Valores do catálogo de exemplo, sem frete.</small></div>' +
        '<p class="prontas-status" data-status="' + h(avaliacao.status) + '">' + h(STATUS[avaliacao.status]) + ' · ' + avaliacao.preenchidos + '/' + avaliacao.total + '</p>' +
        '<details class="prontas-detalhes"><summary aria-label="Ver peças e compatibilidade de ' + h(build.titulo) + '">Peças e compatibilidade</summary>' +
        '<div class="prontas-detalhes-conteudo"><h3>Peças e quantidades</h3><p>Preços demonstrativos por linha, já multiplicados pela quantidade.</p><ul class="prontas-pecas">' + pecas + '</ul>' +
        '<section class="prontas-compatibilidade" aria-label="Compatibilidade de ' + h(build.titulo) + '"><h3>Compatibilidade</h3>' +
        (semConflitos ? '<p>Nenhum conflito identificado nos dados disponíveis.</p>' : "") +
        listaMensagens("Incompatibilidades",avaliacao.erros) + listaMensagens("Peças pendentes",avaliacao.faltam) +
        listaMensagens("Avisos",avaliacao.avisos) + listaMensagens("Conferências necessárias",avaliacao.dicas) +
        '<p class="prontas-nota">A avaliação depende dos dados do catálogo. Confira as medidas, conexões e o suporte dos fabricantes antes de comprar.</p></section>' +
        '<p class="prontas-nota">O objetivo orienta a escolha. Confira as peças e adapte o modelo às suas necessidades.</p></div></details>' +
        '<div class="prontas-acoes"><button type="button" class="btn-primary" data-usar-modelo="' + h(build.id) + '" aria-label="Usar como base: ' + h(build.titulo) +
        '">Usar como base</button><small>Abre uma cópia privada e destrancada no editor.</small></div></article>';
    }

    function renderizar() {
      if (!budget.validity.valid) {
        budget.setAttribute("aria-invalid","true");
        lista.innerHTML = "";
        contador.textContent = "Informe um budget válido para filtrar.";
        informar("Informe um budget entre R$ 0 e R$ 1.000.000, com até duas casas decimais.",true);
        return;
      }
      budget.removeAttribute("aria-invalid");
      const limite = budget.value === "" ? Infinity : Number(budget.value);
      const visiveis = modelos.filter(({build,avaliacao}) => (!objetivo.value || build.objetivo === objetivo.value) && avaliacao.preco <= limite);
      contador.textContent = visiveis.length + (visiveis.length === 1 ? " configuração encontrada" : " configurações encontradas");
      lista.innerHTML = visiveis.length ? visiveis.map(card).join("") :
        '<p class="prontas-vazio">Nenhum modelo atende a esses filtros. Aumente o budget ou escolha outro objetivo.</p>';
      informar("");
      atualizarCota();
    }

    objetivo.addEventListener("change",renderizar);
    budget.addEventListener("input",renderizar);
    formulario.addEventListener("reset",() => {
      objetivo.value = "";
      budget.value = "";
      renderizar();
    });
    lista.addEventListener("click",evento => {
      const botao = evento.target.closest("[data-usar-modelo]");
      if (!botao || abrindo) return;
      if (atualizarCota()) { informar(MOTIVO_COTA,true); return; }
      const modelo = modelos.find(({build}) => build.id === botao.dataset.usarModelo);
      if (!modelo) return;
      try {
        abrindo = true;
        atualizarCota();
        const copia = copiarModelo(modelo.build);
        const planejamento = planejamentoLocal();
        if (planejamento.usarBudget) copia.orcamento = planejamento.budget;
        guardarRascunho(copia);
        navegarPara("./configuracao-build.html?" + new URLSearchParams({id:copia.id}));
      } catch {
        abrindo = false;
        atualizarCota();
        informar("Não foi possível guardar o rascunho. Permita o armazenamento local do navegador e tente novamente.",true);
      }
    });
    renderizar();
  } catch (erro) {
    contador.textContent = "Configurações indisponíveis";
    lista.textContent = "Não foi possível carregar os modelos demonstrativos. Recarregue a página para tentar novamente.";
    objetivo.disabled = true;
    budget.disabled = true;
    informar(erro.message || "Falha ao carregar o catálogo demonstrativo.",true);
  } finally {
    lista.setAttribute("aria-busy","false");
  }
});
