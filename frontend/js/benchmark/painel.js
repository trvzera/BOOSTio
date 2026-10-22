import { htmlSeguro as h } from "../build/catalogo.js";

export function painelBenchmarkHtml({prefixo = "fpshq",hardware = "",memoria = null,verificarRequisitos = false} = {}) {
  const id = nome => h(prefixo + "-" + nome);
  return '<section class="fpshq-panel benchmark-panel" data-layout="cards" aria-label="Consulta de desempenho esperado">'
    + '<p class="fpshq-hardware">' + h(hardware) + (memoria != null ? '<span data-benchmark-ram>' + h(memoria) + ' GB de RAM · não avaliada na estimativa</span>' : verificarRequisitos ? '<span data-benchmark-ram>Capacidade total de RAM a confirmar</span>' : '') + '</p>'
    + '<div class="fpshq-workspace"><div class="fpshq-controls"><form id="' + id("test-form") + '">'
    + '<div class="test-field-row fpshq-fields"><label class="test-field" for="' + id("game") + '">Jogo<select id="' + id("game") + '" required></select></label>'
    + '<label class="test-field" for="' + id("resolution") + '">Resolução<select id="' + id("resolution") + '"><option value="1080p">1080p</option><option value="1440p">1440p</option><option value="4k">4K</option></select></label>'
    + '<label class="test-field" for="' + id("preset") + '">Qualidade<select id="' + id("preset") + '"><option value="low">Baixa</option><option value="medium">Média</option><option value="high" selected>Alta</option><option value="ultra">Ultra</option></select></label></div>'
    + '<div class="test-actions"><button type="submit" class="btn-primary" aria-label="Ver desempenho esperado na FPSHQ" data-disabled-reason="Aguarde a consulta atual ou o intervalo solicitado pelo provedor.">Ver desempenho</button>'
    + (verificarRequisitos ? '<button type="button" class="btn-secondary" data-check-build-requirements aria-label="Verificar requisitos do jogo com a RAM da build salva" data-disabled-reason="Aguarde a verificação dos requisitos.">Verificar requisitos</button>' : '') + '</div></form>'
    + '<details class="fpshq-search-details fpshq-disclosure" data-animated-details><summary>Buscar outro jogo</summary>'
    + '<div class="fpshq-search-row"><label class="test-field" for="' + id("search-text") + '"><span class="sr-only">Nome do jogo</span><input id="' + id("search-text") + '" type="search" minlength="2" maxlength="60" placeholder="Nome do jogo" aria-describedby="' + id("search-help") + '"></label><button id="' + id("search") + '" type="button" class="btn-secondary" aria-label="Buscar jogos na FPSHQ" data-disabled-reason="Aguarde a consulta atual.">Buscar</button></div>'
    + '<p class="sr-only" id="' + id("search-help") + '">Digite entre 2 e 60 caracteres e selecione um jogo nos resultados.</p>'
    + '<p class="test-feedback" id="' + id("search-status") + '" role="status" aria-live="polite" hidden></p><ul id="' + id("search-results") + '" class="fpshq-search-results" aria-label="Jogos encontrados" hidden></ul></details></div>'
    + '<div class="fpshq-output"><p id="' + id("feedback") + '" class="test-feedback" role="status" aria-live="polite" hidden></p>'
    + (verificarRequisitos ? '<section id="' + id("requirements") + '" class="fpshq-build-requirements" aria-label="Requisitos do jogo e capacidade de RAM da build" hidden></section>' : '')
    + '<div id="' + id("empty") + '" class="fpshq-empty"><span>O resultado aparece aqui</span></div>'
    + '<div id="' + id("result") + '" class="fpshq-result" hidden aria-live="polite" aria-atomic="true"></div>'
    + '<aside id="' + id("notice") + '" class="fpshq-notice" aria-label="Limitações do desempenho esperado" hidden><p>Expectativa de CPU/GPU, não uma medição do seu PC.</p><details class="fpshq-disclosure fpshq-limitations" data-animated-details><summary>O que pode influenciar?</summary><p>' + (verificarRequisitos ? 'A capacidade de RAM é verificada separadamente na build salva. CPU, GPU, VRAM e os demais requisitos ainda não estão validados.' : 'RAM e requisitos mínimos do jogo ainda não foram verificados.') + ' Modelo das peças, drivers, temperatura, energia e programas em segundo plano podem alterar o resultado.</p><p>Rede pode causar lag, mas não equivale necessariamente a queda de FPS. Nenhum teste é executado na sua máquina.</p></details></aside>'
    + '<p class="fpshq-attribution">Fonte: <a id="' + id("source") + '" href="https://fpshq.com/pt/api/" target="_blank" rel="noopener noreferrer" aria-label="FPSHQ — ver fonte em nova aba">FPSHQ</a> · <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener noreferrer" aria-label="Ver licença CC BY 4.0 em nova aba">CC BY 4.0</a></p></div></div></section>';
}
