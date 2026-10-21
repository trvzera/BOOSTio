import { criarClienteBenchmark } from "../api/benchmark/consultarBenchmark.js";
import { htmlSeguro as h } from "../build/catalogo.js";

const FONTES = new Set(["support.riotgames.com","store.steampowered.com","www.epicgames.com","support.cdprojektred.com","support.rockstargames.com"]);
export function requisitosHtml(dados) {
  const url = new URL(dados.fonte.url);
  if (url.protocol !== "https:" || !FONTES.has(url.hostname)) throw new Error("Fonte de requisitos não reconhecida.");
  const mensagem = {
    nao_informada:"RAM não informada: capacidade não verificada.",
    abaixo_minimo:"A capacidade de RAM informada está abaixo do mínimo. Um FPS positivo da API não aprova esta configuração.",
    abaixo_recomendado:"A capacidade de RAM alcança o mínimo, mas fica abaixo do recomendado.",
    recomendado:"A capacidade de RAM alcança o valor recomendado. Isso não confirma que o PC atende aos demais requisitos.",
    minimo_sem_recomendacao:"A capacidade de RAM alcança o mínimo. A fonte não informa um valor recomendado.",
  }[dados.ram.status];
  if (!mensagem) throw new Error("Estado de requisitos inválido.");
  const ficha = (titulo,itens) => '<article><h4 class="font-1-s">' + titulo + '</h4>' + (itens ? '<dl class="font-2-xs">' +
    [["Processador",itens.cpu],["Placa de vídeo",itens.gpu],["RAM",itens.ramGb + " GB"],["Armazenamento",itens.armazenamento],["Sistema",itens.sistema]]
      .map(([nome,valor]) => '<dt>' + nome + '</dt><dd>' + h(valor || "Não informado nesta ficha") + '</dd>').join("") + '</dl>' : '<p class="font-2-xs">Não publicado na fonte consultada.</p>') + '</article>';
  return '<h3 class="font-1-l">' + h(dados.jogo) + '</h3><p class="font-2-xs">' + h(dados.contexto) + '</p>'
    + '<p class="test-feedback font-2-xs" data-tone="' + (dados.ram.status === "abaixo_minimo" ? "error" : dados.ram.status === "abaixo_recomendado" ? "warning" : "info") + '">' + mensagem + '</p>'
    + '<div class="test-requirements-grid">' + ficha("Mínimos",dados.minimos) + ficha("Recomendados",dados.recomendados) + '</div>'
    + '<p class="test-muted font-2-xs">' + h(dados.observacoes) + '</p><p class="test-muted font-2-xs">Verificação parcial de capacidade instalada, não de memória livre, canais ou frequência. CPU, GPU, VRAM, sistema e demais recursos não foram validados. Nenhum FPS foi calculado ou corrigido.</p>'
    + '<p class="font-2-xs"><a href="' + h(url.href) + '" target="_blank" rel="noopener noreferrer" aria-label="Ver requisitos oficiais de ' + h(dados.jogo) + ' em nova aba">' + h(dados.fonte.nome) + '</a> · Fonte revisada em ' + h(dados.fonte.verificadoEm) + '. Não é uma consulta em tempo real à publicadora.</p>';
}

export function iniciarRequisitosLaboratorio(raiz,{cliente = criarClienteBenchmark()} = {}) {
  const botao = raiz.querySelector("#requirements-check"), ram = raiz.querySelector("#requirements-ram"), jogo = raiz.querySelector("#fpshq-game");
  const feedback = raiz.querySelector("#requirements-feedback"), resultado = raiz.querySelector("#requirements-result");
  if (!botao || !ram || !jogo) return;
  let controle, versao = 0, ativo = true;
  const limpar = () => {
    versao++; controle?.abort(); botao.disabled = false; resultado.replaceChildren(); resultado.hidden = true;
    resultado.setAttribute("aria-busy","false"); feedback.textContent = ""; feedback.hidden = true;
  };
  jogo.addEventListener("change",limpar); ram.addEventListener("input",limpar);
  botao.addEventListener("click",async () => {
    if (botao.disabled || !ram.reportValidity() || !jogo.reportValidity()) return;
    limpar(); const atual = versao; controle = new AbortController(); botao.disabled = true;
    feedback.hidden = false; feedback.dataset.tone = "info"; feedback.textContent = "Consultando requisitos revisados…";
    resultado.setAttribute("aria-busy","true");
    try {
      const dados = await cliente.consultarRequisitos({game:jogo.value,ramGb:ram.value === "" ? null : ram.valueAsNumber},{signal:controle.signal});
      if (!ativo || atual !== versao) return;
      resultado.innerHTML = requisitosHtml(dados); resultado.hidden = false; feedback.hidden = true;
    } catch (erro) { if (ativo && atual === versao) { feedback.textContent = erro.message; feedback.dataset.tone = "error"; } }
    finally { if (ativo && atual === versao) { botao.disabled = false; resultado.setAttribute("aria-busy","false"); } }
  });
  return () => { ativo = false; limpar(); jogo.removeEventListener("change",limpar); ram.removeEventListener("input",limpar); };
}
