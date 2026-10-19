import { htmlSeguro as h } from "../build/catalogo.js";

export const QUALIDADES_FPS = Object.freeze({low:"Baixa",medium:"Média",high:"Alta",ultra:"Ultra"});
const numero = n => n == null ? "Sem dados" : new Intl.NumberFormat("pt-BR",{maximumFractionDigits:0}).format(n);

export function resolucoesHtml(matriz,qualidade) {
  const preset = Object.hasOwn(QUALIDADES_FPS,qualidade) ? qualidade : "high";
  return ["1080p","1440p","4K"].map(res => {
    const fps = matriz?.[res]?.[preset];
    return '<div class="fpshq-resolution-card"><dt>' + res + '</dt><dd>' + numero(fps)
      + (fps == null ? '' : '<small> FPS</small>') + '</dd></div>';
  }).join("");
}

export function resultadoDesempenhoHtml(dados) {
  const qualidade = QUALIDADES_FPS[dados.consulta.preset];
  const origem = dados.base === "aggregate" ? "Dados agregados de análises, recalculados pela FPSHQ." : dados.base === "model" || dados.origem === "model" ? "Estimativa do modelo FPSHQ." : dados.origem === "measured" ? "Baseado em medições, segundo a FPSHQ. Não é uma medição desta máquina." : "Origem não informada pelo provedor.";
  const valor = dados.intervalo ? dados.intervalo.map(numero).join("–") : numero(dados.fps);
  return '<div class="fpshq-result-heading"><h3 class="font-1-l">' + h(dados.jogo) + '</h3><span class="font-2-xs">'
    + h(dados.consulta.res.toUpperCase()) + ' <span aria-hidden="true">·</span> ' + h(qualidade) + '</span></div>'
    + '<dl class="fpshq-metrics"><div><dt>FPS médio esperado</dt><dd>' + valor + '<small> FPS</small></dd></div>'
    + '<div><dt>1% low</dt><dd>' + numero(dados.low1) + (dados.low1 == null ? '' : '<small> FPS</small>') + '</dd></div></dl>'
    + '<details class="fpshq-alternatives fpshq-disclosure" data-animated-details><summary>Comparar ajustes</summary>'
    + '<fieldset class="fpshq-quality-tabs"><legend class="sr-only">Qualidade gráfica da comparação</legend>'
    + Object.entries(QUALIDADES_FPS).map(([preset,rotulo]) => '<label><input type="radio" name="fpshq-comparison-quality" value="' + preset
      + '"' + (preset === dados.consulta.preset ? ' checked' : '') + '><span>' + rotulo + '</span></label>').join("")
    + '</fieldset><dl class="fpshq-resolutions" aria-label="FPS médios por resolução" aria-live="polite">'
    + resolucoesHtml(dados.matriz,dados.consulta.preset) + '</dl><p class="font-2-xs test-muted fpshq-matrix-caption">Valores da matriz do provedor, sem nova consulta.</p></details>'
    + '<details class="fpshq-data-details fpshq-disclosure" data-animated-details><summary>Sobre os dados</summary><div class="fpshq-data-copy">'
    + '<p>' + origem + '</p><p>1% low representa momentos de menor fluidez; não é o FPS mínimo. A origem de cada célula da comparação não é informada separadamente.</p>'
    + '<p>' + (dados.cache ? 'Resposta em cache' : 'Consulta à API') + ' <span aria-hidden="true">·</span> '
    + h(new Date(dados.consultadoEm).toLocaleString("pt-BR")) + '.</p>'
    + '<p>Cache de uma hora. A API informa limites de 60 consultas/minuto e 10 mil/dia por IP. Nenhuma consulta é feita automaticamente.</p></div></details>';
}
