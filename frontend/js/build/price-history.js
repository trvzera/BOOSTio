import { moeda, htmlSeguro as h } from "./catalogo.js";

const DIA = 86400000;
const periodos = [["30", "30 dias"], ["90", "90 dias"], ["todos", "Todo o período"]];
const dataCurta = new Intl.DateTimeFormat("pt-BR", {day:"2-digit", month:"2-digit", year:"numeric", timeZone:"UTC"});

function instanteRegistro(valor) {
  if (typeof valor !== "string" || !/^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?(?:Z|[+-]\d{2}:\d{2}))?$/.test(valor)) return NaN;
  const dia = valor.slice(0, 10);
  const meiaNoite = new Date(dia + "T00:00:00Z");
  if (!Number.isFinite(meiaNoite.getTime()) || meiaNoite.toISOString().slice(0, 10) !== dia) return NaN;
  return Date.parse(valor.length === 10 ? valor + "T00:00:00Z" : valor);
}

// Usa cotações explícitas da loja recebidas do backend, nunca visitas locais
// ou cópias do preço atual apresentadas como se fossem cotações anteriores.
export function normalizarHistoricoPrecos(registros, agora = Date.now()) {
  if (!Array.isArray(registros)) return [];
  const porInstante = new Map();
  for (const registro of registros) {
    if (!registro || typeof registro !== "object") continue;
    const instante = instanteRegistro(registro.data);
    const loja = typeof registro.loja === "string" ? registro.loja.trim().toLowerCase().replace(/!$/, "") : "";
    if (loja !== "kabum" || typeof registro.preco !== "number" || !Number.isFinite(registro.preco) || registro.preco <= 0 || !Number.isFinite(instante) || instante > agora || registro.esgotado === true) continue;
    porInstante.set(instante, {instante, preco:registro.preco});
  }
  return [...porInstante.values()].sort((a, b) => a.instante - b.instante);
}

export function filtrarHistoricoPrecos(registros, periodo, agora = Date.now()) {
  if (!periodos.some(([valor]) => valor === periodo)) return [];
  if (periodo === "todos") return registros.slice();
  // Inclui o dia atual e os anteriores até completar o número de dias escolhido.
  const hoje = new Date(agora);
  const inicio = Date.UTC(hoje.getUTCFullYear(), hoje.getUTCMonth(), hoje.getUTCDate()) - (Number(periodo) - 1) * DIA;
  return registros.filter(registro => registro.instante >= inicio && registro.instante <= agora);
}

function vazioHistorico(temHistorico) {
  return '<div class="price-history-empty"><strong>' + (temHistorico ? 'Nenhum registro neste período' : 'Ainda não há histórico desta peça') +
    '</strong><p>' + (temHistorico ? 'Escolha um período maior para consultar os preços disponíveis.' : 'Os valores anteriores aparecerão aqui quando houver registros disponíveis. Você pode conferir o preço atual nas opções de compra acima.') + '</p></div>';
}

function conteudoHistorico(registros, temHistorico) {
  if (!registros.length) return vazioHistorico(temHistorico);
  const primeiro = registros[0], ultimo = registros.at(-1);
  const precos = registros.map(registro => registro.preco);
  const minimo = Math.min(...precos), maximo = Math.max(...precos);
  const metricas = [["Último registro", ultimo.preco], ["Menor preço no período", minimo], ["Maior preço no período", maximo]];
  const amplitude = maximo - minimo || Math.max(maximo * .1, 1);
  const pontos = registros.map(registro => ({
    x:registros.length === 1 ? 320 : 12 + (registro.instante - primeiro.instante) / (ultimo.instante - primeiro.instante) * 616,
    y:registros.length === 1 || maximo === minimo ? 100 : 172 - (registro.preco - minimo) / amplitude * 144,
  }));
  const linha = pontos.map((p, i) => (i ? "L" : "M") + p.x.toFixed(2) + " " + p.y.toFixed(2)).join(" ");
  const pontoFinal = pontos.at(-1);
  return '<dl class="price-history-stats">' + metricas.map(([rotulo, valor]) => '<div><dt>' + rotulo + '</dt><dd>' + moeda(valor) + '</dd></div>').join("") + '</dl>' +
    '<figure class="price-history-figure"><svg class="price-history-chart" viewBox="0 0 640 200" preserveAspectRatio="none" aria-hidden="true" focusable="false">' +
    '<path class="price-history-grid" d="M0 28H640 M0 100H640 M0 172H640"/>' +
    '<path class="price-history-line" d="' + linha + '"/><circle class="price-history-point" cx="' + pontoFinal.x.toFixed(2) + '" cy="' + pontoFinal.y.toFixed(2) + '" r="4"/></svg>' +
    '<div class="price-history-dates" aria-hidden="true"><span>' + dataCurta.format(primeiro.instante) + '</span><span>' + (registros.length > 1 ? dataCurta.format(ultimo.instante) : '') + '</span></div>' +
    '<figcaption>' + (registros.length === 1 ? 'Há apenas um preço registrado neste período. Ainda não é possível mostrar uma tendência.' : 'Evolução dos preços registrados na KaBuM!, de ' + dataCurta.format(primeiro.instante) + ' a ' + dataCurta.format(ultimo.instante) + '. As datas sem registro não representam novas consultas.') + '</figcaption></figure>' +
    '<details class="price-history-records"><summary>Ver registros de preços</summary><table><caption class="sr-only">Registros de preço na KaBuM!, em reais e sem frete</caption><thead><tr><th scope="col">Data</th><th scope="col">Preço</th></tr></thead><tbody>' +
    registros.slice().reverse().map(registro => '<tr><td>' + dataCurta.format(registro.instante) + '</td><td>' + moeda(registro.preco) + '</td></tr>').join("") + '</tbody></table></details>';
}

export function historicoPrecosHtml(peca, agora = Date.now()) {
  const registros = normalizarHistoricoPrecos(peca?.historico_precos, agora);
  return '<section class="product-price-history glass-card" data-price-history aria-labelledby="price-history-title"><div class="price-history-heading"><div><h2 class="font-1-l" id="price-history-title">Histórico de preços</h2>' +
    '<p>Veja como o preço desta peça mudou ao longo do tempo.</p></div><span class="price-history-store">KaBuM!</span></div>' +
    (registros.length ? '<div class="price-history-periods" role="group" aria-label="Período do histórico de preços">' + periodos.map(([valor, rotulo]) => '<button type="button" data-history-period="' + valor + '" aria-label="Mostrar histórico: ' + h(rotulo) + '" aria-pressed="' + (valor === "todos") + '">' + h(valor === 'todos' && peca?.historico_precos_incompleto ? 'Todos os registros carregados' : rotulo) + '</button>').join("") + '</div>' : '') +
    (peca?.historico_precos_incompleto ? '<p class="price-history-note">Exibindo somente os 1.000 registros mais recentes deste anúncio.</p>' : '') +
    '<div data-history-content>' + conteudoHistorico(registros, registros.length > 0) + '</div>' +
    '<p class="price-history-note">Valores registrados, sem frete. O preço e a disponibilidade atuais devem ser confirmados na loja.</p><p class="sr-only" data-history-status role="status" aria-atomic="true"></p></section>';
}

export function iniciarHistoricoPrecos(raiz, peca, agora = Date.now()) {
  const secao = raiz.querySelector("[data-price-history]");
  if (!secao || secao.dataset.historyInitialized) return;
  secao.dataset.historyInitialized = "true";
  const registros = normalizarHistoricoPrecos(peca?.historico_precos, agora);
  secao.querySelectorAll("[data-history-period]").forEach(botao => botao.addEventListener("click", () => {
    if (botao.getAttribute("aria-pressed") === "true") return;
    const periodo = botao.dataset.historyPeriod;
    const filtrados = filtrarHistoricoPrecos(registros, periodo, agora);
    secao.querySelectorAll("[data-history-period]").forEach(outro => outro.setAttribute("aria-pressed", String(outro === botao)));
    secao.querySelector("[data-history-content]").innerHTML = conteudoHistorico(filtrados, registros.length > 0);
    secao.querySelector("[data-history-status]").textContent = filtrados.length ? filtrados.length + ' registros de preço exibidos para ' + botao.textContent.toLowerCase() + '.' : 'Nenhum registro de preço neste período. Escolha um período maior.';
  }));
}
