import { htmlSeguro as h } from "../build/catalogo.js";
import { iniciarDetalhesAnimados } from "../components/animated-details.js";

const FONTES = new Set(["support.riotgames.com","store.steampowered.com","www.epicgames.com","support.cdprojektred.com","support.rockstargames.com"]);
const mensagens = {
  nao_informada:"Falta identificar toda a RAM da build para verificar a capacidade.",
  abaixo_minimo:"A RAM da build está abaixo do mínimo publicado para este jogo. Revise a memória antes de consultar FPS.",
  abaixo_recomendado:"A RAM alcança o mínimo, mas fica abaixo do recomendado.",
  recomendado:"A capacidade de RAM alcança o recomendado publicado.",
  minimo_sem_recomendacao:"A RAM alcança o mínimo. A fonte não publica uma capacidade recomendada.",
};

export function resumoRequisitosBuildHtml(dados) {
  const fonte = new URL(dados.fonte.url);
  if (fonte.protocol !== "https:" || !FONTES.has(fonte.hostname)) throw new Error("Fonte de requisitos não reconhecida.");
  const ram = dados.ram;
  let mensagem = mensagens[ram.status];
  if (!mensagem) throw new Error("Estado de requisitos inválido.");
  const impedimentos = dados.impedimentosMinimos || [];
  if (impedimentos.length && ram.atendeMinimo !== false) mensagem = "Há requisitos mínimos não atendidos. Revise as capacidades indicadas antes de consultar FPS.";
  const tom = ram.status === "abaixo_minimo" || impedimentos.length ? "error" : ram.status === "abaixo_recomendado" ? "warning" : "info";
  const instalada = ram.completa ? ram.informadaGb + " GB" : ram.conhecidaGb > 0 ? "Pelo menos " + ram.conhecidaGb + " GB identificados" : "A confirmar";
  const ficha = (titulo,valor) => '<div><dt>' + titulo + '</dt><dd>' + h(valor) + '</dd></div>';
  const capacidades = (dados.vram?.dedicadaGb != null ? '<p>VRAM dedicada: ' + h(dados.vram.dedicadaGb) + ' GB. Capacidade não comprova desempenho nem recursos da GPU.</p>' : '')
    + (dados.armazenamento ? '<p>Armazenamento: ' + (dados.armazenamento.maiorUnidadeElegivelGb ? h(dados.armazenamento.maiorUnidadeElegivelGb) + ' GB na maior unidade ' + (dados.armazenamento.exigeSsd ? 'SSD ' : '') + 'identificada.' : 'unidade elegível a confirmar.') + ' Espaço livre não verificado; não somamos discos separados para instalar o jogo.</p>' : '');
  const detalhe = (titulo,requisitos) => '<div><h4>' + titulo + '</h4><dl>' + (requisitos
    ? [["Processador",requisitos.cpu],["Placa de vídeo",requisitos.gpu],["Armazenamento",requisitos.armazenamento],["Sistema",requisitos.sistema]]
      .map(([nome,valor]) => '<dt>' + nome + '</dt><dd>' + h(valor || "Não informado") + '</dd>').join("")
    : '<dd>Não publicado na fonte consultada.</dd>') + '</dl></div>';
  return '<h3>Requisitos de ' + h(dados.jogo) + '</h3><p class="fpshq-requirements-status" data-tone="' + tom + '" role="status">' + mensagem + '</p>'
    + '<dl class="fpshq-requirements-ram">' + ficha("RAM da build salva",instalada) + ficha("Mínimo",dados.minimos.ramGb + " GB")
    + ficha("Recomendado",dados.recomendados?.ramGb != null ? dados.recomendados.ramGb + " GB" : "Não publicado") + '</dl>'
    + (impedimentos.length ? '<p role="status">' + impedimentos.map(h).join(' ') + '</p>' : '')
    + '<p>A verificação é parcial: CPU, GPU, VRAM, sistema e demais recursos ainda precisam ser confirmados. Capacidades suficientes não garantem que o jogo rode.</p>'
    + (ram.pendencias.length ? '<p>' + ram.pendencias.map(h).join(" ") + '</p>' : '')
    + '<details class="fpshq-disclosure" data-animated-details><summary>Ver requisitos oficiais e capacidades</summary>' + capacidades + '<p>' + h(dados.contexto) + '</p><div class="fpshq-requirements-specs">'
    + detalhe("Mínimos",dados.minimos) + detalhe("Recomendados",dados.recomendados) + '</div><p>' + h(dados.observacoes) + '</p><p><a href="' + h(fonte.href)
    + '" target="_blank" rel="noopener noreferrer" aria-label="Ver requisitos oficiais de ' + h(dados.jogo) + ' em nova aba">' + h(dados.fonte.nome)
    + '</a> · Revisado em ' + h(dados.fonte.verificadoEm) + '</p></details>';
}

export function iniciarRequisitosBuild(raiz,{prefixo,buildId,cliente}) {
  const saida = raiz.querySelector('#' + prefixo + '-requirements');
  const botao = raiz.querySelector('[data-check-build-requirements]');
  const jogo = raiz.querySelector('#' + prefixo + '-game');
  const memoria = raiz.querySelector('[data-benchmark-ram]');
  if (!saida || !botao || !jogo || !buildId) return null;
  let ativo = true, versao = 0, controle, pendente, jogoPendente;
  const rotuloMemoria = memoria?.textContent;
  const informar = (mensagem,tom = "info") => {
    saida.hidden = false;
    saida.innerHTML = '<p class="fpshq-requirements-status" role="status" data-tone="' + tom + '">' + h(mensagem) + '</p>';
  };
  const limpar = () => {
    versao++; controle?.abort(); pendente = null; jogoPendente = null;
    botao.disabled = false; saida.hidden = true; saida.replaceChildren(); saida.setAttribute("aria-busy","false");
    if (memoria) memoria.textContent = rotuloMemoria;
  };
  function verificar(game) {
    if (pendente && jogoPendente === game) return pendente;
    controle?.abort(); controle = new AbortController();
    const atual = ++versao, signal = controle.signal;
    jogoPendente = game; botao.disabled = true; saida.setAttribute("aria-busy","true");
    informar("Verificando as capacidades da build salva e os requisitos do jogo…");
    pendente = (async () => {
      try {
        const dados = await cliente.consultarRequisitosBuild({game,buildId},{signal});
        if (!ativo || atual !== versao) throw Object.assign(new Error("Consulta cancelada."),{codigo:"cancelado"});
        saida.innerHTML = resumoRequisitosBuildHtml(dados); saida.hidden = false;
        iniciarDetalhesAnimados(saida);
        if (memoria) memoria.textContent = dados.ram.completa ? dados.ram.informadaGb + " GB de RAM na build salva" : "Capacidade total de RAM a confirmar";
        return dados;
      } catch (erro) {
        if (ativo && atual === versao) informar(erro.message,erro.codigo === "sem-requisitos" ? "info" : "error");
        if (erro.codigo === "sem-requisitos") return null;
        throw erro;
      } finally {
        if (ativo && atual === versao) { botao.disabled = false; saida.setAttribute("aria-busy","false"); pendente = null; }
      }
    })();
    return pendente;
  }
  const aoVerificar = () => { if (!botao.disabled && jogo.reportValidity()) verificar(jogo.value).catch(() => {}); };
  botao.addEventListener("click",aoVerificar); jogo.addEventListener("change",limpar);
  return {verificar,destruir() { ativo = false; limpar(); botao.removeEventListener("click",aoVerificar); jogo.removeEventListener("change",limpar); }};
}
