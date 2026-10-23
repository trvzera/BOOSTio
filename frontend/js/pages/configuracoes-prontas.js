import "../header.js";
import "../auth/auth.js";
import { carregarCatalogo, htmlSeguro as h, moeda } from "../build/catalogo.js";
import { informacoesRam, informacoesArmazenamento } from "../build/estado.js";
import { modelosProntos, copiarModelo, ordenarModelosPorPreco } from "../build/modelos.js";
import { avaliarBuild } from "../build/compatibilidade.js";
import { navegarPara } from "../components/page-loading.js";
import { planejamentoLocal } from "../build/planejamento.js";
import { carregarCatalogoConta, estadoParaConta } from "../build/conta.js";
import { criarBuildManual, verificarEspacoBuild, listarBuilds, LIMITE_BUILDS } from "../api/build/builds.js";
import { carregarPerfil } from '../conta/perfil.js';

document.addEventListener("DOMContentLoaded", async () => {
  const formulario = document.querySelector("#prontas-filtros");
  const objetivo = document.querySelector("#prontas-objetivo");
  const budget = document.querySelector("#prontas-budget");
  const lista = document.querySelector("#prontas-lista");
  const contador = document.querySelector("#prontas-contador");
  const feedback = document.querySelector("#prontas-feedback");
  const cota = document.querySelector("#prontas-cota");
  let abrindo = false;
  let motivoBloqueio = 'Verificando as vagas da sua conta…', revisaoCota = 0;

  function informar(texto, erro = false) {
    feedback.textContent = texto;
    feedback.dataset.tone = erro ? "error" : "info";
  }

  function aplicarCota() {
    lista.querySelectorAll("[data-usar-modelo]").forEach(botao => {
      botao.disabled = abrindo || Boolean(motivoBloqueio);
      if (motivoBloqueio) botao.dataset.disabledReason = motivoBloqueio;
      else delete botao.dataset.disabledReason;
    });
  }
  async function atualizarCota() {
    const atual = ++revisaoCota;
    motivoBloqueio = 'Verificando as vagas da sua conta…'; aplicarCota();
    try {
      const perfil = await carregarPerfil();
      if (!perfil.auth) throw new Error('Entre na sua conta para salvar uma configuração pronta.');
      if (!perfil.usuario?.verificado) throw new Error('Verifique seu e-mail nas configurações para salvar uma configuração pronta.');
      const resposta = await listarBuilds();
      if (atual !== revisaoCota) return;
      const usados = resposta.builds.length;
      motivoBloqueio = usados >= LIMITE_BUILDS ? 'Você atingiu o limite de três builds. Exclua uma para liberar espaço.' : '';
      cota.textContent = motivoBloqueio || usados + ' de ' + LIMITE_BUILDS + ' builds salvas · Abrir cria uma cópia privada';
    } catch(erro) {
      if (atual !== revisaoCota) return;
      motivoBloqueio = erro.message; cota.textContent = motivoBloqueio;
    }
    aplicarCota();
  }

  formulario.addEventListener("submit",evento => evento.preventDefault());
  window.addEventListener("pageshow",() => { abrindo = false; atualizarCota(); });
  window.addEventListener("focus",atualizarCota);
  atualizarCota();

  try {
    const [catalogo,referencias] = await Promise.all([carregarCatalogoConta(),carregarCatalogo()]);
    const modelos = ordenarModelosPorPreco(modelosProntos(catalogo,{referencias}).map(build => ({build,avaliacao:avaliarBuild(build,catalogo)})));
    const objetivos = new Map(modelos.map(({build}) => [build.objetivo,build.metadados.objetivoRotulo]));
    objetivo.innerHTML = '<option value="">Todos os objetivos</option>' + [...objetivos].map(([valor,rotulo]) =>
      '<option value="' + h(valor) + '">' + h(rotulo) + '</option>').join("");

    function card({build,avaliacao}) {
      const ram = informacoesRam(build,catalogo), discos = informacoesArmazenamento(build,catalogo);
      return '<article class="prontas-card glass-card" aria-labelledby="titulo-' + h(build.id) + '">' +
        '<div class="prontas-tags"><span>' + h(build.metadados.plataforma) + '</span><span>' + h(build.metadados.objetivoRotulo) + '</span></div>' +
        '<h2 id="titulo-' + h(build.id) + '">' + h(build.titulo) + '</h2><p class="prontas-descricao">' + h(build.descricao) + '</p>' +
        '<dl class="prontas-resumo"><div><dt>Memória RAM</dt><dd>' + ram.capacidade + ' GB</dd></div><div><dt>Armazenamento</dt><dd>' + discos.capacidade + ' GB</dd></div></dl>' +
        '<div class="prontas-total"><span>' + (build.metadados.pendentes.length ? 'Total parcial dos preços disponíveis' : 'Total das peças') + '</span><strong>' + (avaliacao.preco > 0 ? moeda(avaliacao.preco) : 'Preço a consultar') + '</strong><small>Sem periféricos e sem frete.' + (build.metadados.pendentes.length ? ' Há peças sem cotação ou estoque confirmado.' : '') + '</small></div>' +
        '<div class="prontas-acoes"><button type="button" class="btn-primary" data-usar-modelo="' + h(build.id) + '" aria-label="Abrir build e personalizar: ' + h(build.titulo) +
        '">Abrir build</button><small>Peças e compatibilidade aparecem no editor. Salva uma cópia na sua conta.</small></div></article>';
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
      const visiveis = modelos.filter(({build,avaliacao}) => (!objetivo.value || build.objetivo === objetivo.value)
        && (!Number.isFinite(limite) || !build.metadados.pendentes.length && avaliacao.preco <= limite));
      contador.textContent = visiveis.length + (visiveis.length === 1 ? " configuração encontrada" : " configurações encontradas") + " · Menor preço primeiro";
      lista.innerHTML = visiveis.length ? visiveis.map(card).join("") :
        '<p class="prontas-vazio">Nenhum modelo atende a esses filtros. Aumente o budget ou escolha outro objetivo.</p>';
      informar("");
      aplicarCota();
    }

    objetivo.addEventListener("change",renderizar);
    budget.addEventListener("input",renderizar);
    formulario.addEventListener("reset",() => {
      objetivo.value = "";
      budget.value = "";
      renderizar();
    });
    lista.addEventListener("click",async evento => {
      const botao = evento.target.closest("[data-usar-modelo]");
      if (!botao || abrindo) return;
      const modelo = modelos.find(({build}) => build.id === botao.dataset.usarModelo);
      if (!modelo) return;
      try {
        abrindo = true;
        aplicarCota();
        await verificarEspacoBuild();
        const copia = copiarModelo(modelo.build);
        const planejamento = planejamentoLocal();
        if (planejamento.usarBudget) copia.orcamento = planejamento.budget;
        const {build} = await criarBuildManual(estadoParaConta(copia));
        navegarPara("./configuracao-build.html?" + new URLSearchParams({build_id:build.id}));
      } catch (erro) {
        abrindo = false;
        atualizarCota();
        informar(erro.message || "Não foi possível salvar a build na conta.",true);
      }
    });
    renderizar();
  } catch (erro) {
    contador.textContent = "Configurações indisponíveis";
    lista.textContent = "Não foi possível carregar os modelos e os preços do catálogo. Recarregue a página para tentar novamente.";
    objetivo.disabled = true;
    budget.disabled = true;
    informar(erro.message || "Falha ao carregar o catálogo demonstrativo.",true);
  } finally {
    lista.setAttribute("aria-busy","false");
  }
});
