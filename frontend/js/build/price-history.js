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


export const nomesLojas = {todas: "Todas as lojas · menor preço do dia", kabum: "KaBuM!", mercado_livre: "Mercado Livre", shopee: "Shopee"};

export function normalizarHistoricoPrecos(registros, agora = Date.now(), lojaEsperada = "kabum") {
  if (!Array.isArray(registros)) return [];
  const porInstante = new Map();
  for (const registro of registros) {
    if (!registro || typeof registro !== "object") continue;
    const instante = instanteRegistro(registro.data);
    const loja = typeof registro.loja === "string" ? registro.loja.trim().toLowerCase().replace(/!$/, "") : "";
    if (!nomesLojas[lojaEsperada] || !["kabum", "mercado_livre", "shopee"].includes(loja) || (lojaEsperada !== "todas" && loja !== lojaEsperada) || typeof registro.preco !== "number" || !Number.isFinite(registro.preco) || registro.preco <= 0 || !Number.isFinite(instante) || instante > agora || registro.esgotado === true) continue;
    porInstante.set(instante, {instante, preco:registro.preco});
  }
  return [...porInstante.values()].sort((a, b) => a.instante - b.instante);
}

export function filtrarHistoricoPrecos(registros, periodo, agora = Date.now()) {
  if (!periodos.some(([valor]) => valor === periodo)) return [];
  if (periodo === "todos") return registros.slice();

  const hoje = new Date(agora);
  const inicio = Date.UTC(hoje.getUTCFullYear(), hoje.getUTCMonth(), hoje.getUTCDate()) - (Number(periodo) - 1) * DIA;
  return registros.filter(registro => registro.instante >= inicio && registro.instante <= agora);
}

function vazioHistorico(temHistorico) {
  return '<div class="price-history-empty"><strong>' + (temHistorico ? 'Nenhum registro neste período' : 'Ainda não há histórico desta peça') +
    '</strong><p>' + (temHistorico ? 'Escolha um período maior para consultar os preços disponíveis.' : 'Os valores anteriores aparecerão aqui quando houver registros disponíveis. Você pode conferir o preço atual nas opções de compra acima.') + '</p></div>';
}

export function indiceHistoricoMaisProximo(registros, instante) {
  if (!registros.length || !Number.isFinite(instante)) return -1;
  let inicio = 0, fim = registros.length - 1;
  while (inicio < fim) {
    const meio = Math.floor((inicio + fim) / 2);
    if (registros[meio].instante < instante) inicio = meio + 1;
    else fim = meio;
  }
  if (!inicio) return 0;
  return instante - registros[inicio - 1].instante <= registros[inicio].instante - instante ? inicio - 1 : inicio;
}

function pontosHistorico(registros) {
  const primeiro = registros[0], ultimo = registros.at(-1);
  const precos = registros.map(r => r.preco), minimo = Math.min(...precos), maximo = Math.max(...precos);
  return registros.map(registro => ({
    x:registros.length === 1 ? 320 : 12 + (registro.instante - primeiro.instante) / (ultimo.instante - primeiro.instante) * 616,
    y:registros.length === 1 || maximo === minimo ? 100 : 172 - (registro.preco - minimo) / (maximo - minimo) * 144,
  }));
}

function conteudoHistorico(registros, temHistorico, nomeLoja = "KaBuM!") {
  if (!registros.length) return vazioHistorico(temHistorico);
  const primeiro = registros[0], ultimo = registros.at(-1);
  const precos = registros.map(registro => registro.preco);
  const minimo = Math.min(...precos), maximo = Math.max(...precos);
  const metricas = [["Último registro", ultimo.preco], ["Menor preço no período", minimo], ["Maior preço no período", maximo]];
  const pontos = pontosHistorico(registros);
  const linha = pontos.map((p, i) => (i ? "L" : "M") + p.x.toFixed(2) + " " + p.y.toFixed(2)).join(" ");
  const pontoFinal = pontos.at(-1);
  return '<dl class="price-history-stats">' + metricas.map(([rotulo, valor]) => '<div><dt>' + rotulo + '</dt><dd>' + moeda(valor) + '</dd></div>').join("") + '</dl>' +
    '<figure class="price-history-figure"><div class="price-history-plot" data-history-plot tabindex="0" role="group" aria-label="Gráfico de preços. Use as setas esquerda e direita para consultar os registros; Home e End para ir ao início ou ao fim; Escape para fechar o detalhe."><svg class="price-history-chart" viewBox="0 0 640 200" preserveAspectRatio="none" aria-hidden="true" focusable="false">' +
    '<path class="price-history-grid" d="M0 28H640 M0 100H640 M0 172H640"/>' +
    '<path class="price-history-line" d="' + linha + '"/><ellipse class="price-history-point" cx="' + pontoFinal.x.toFixed(2) + '" cy="' + pontoFinal.y.toFixed(2) + '" rx="4" ry="4" data-history-radius="4"/>' +
    '<g data-history-marker visibility="hidden"><line class="price-history-guide" y1="12" y2="188"/><ellipse class="price-history-halo" rx="10" ry="10" data-history-radius="10"/><ellipse class="price-history-active-point" rx="5" ry="5" data-history-radius="5"/></g></svg>' +
    '<div class="price-history-tooltip" data-history-tooltip aria-hidden="true" hidden><span data-history-date></span><strong data-history-price></strong></div></div>' +
    '<div class="price-history-dates" aria-hidden="true"><span>' + dataCurta.format(primeiro.instante) + '</span><span>' + (registros.length > 1 ? dataCurta.format(ultimo.instante) : '') + '</span></div>' +
    '<figcaption>' + (registros.length === 1 ? 'Há apenas um preço registrado neste período. Ainda não é possível mostrar uma tendência.' : 'Evolução dos preços registrados em ' + h(nomeLoja) + ', de ' + dataCurta.format(primeiro.instante) + ' a ' + dataCurta.format(ultimo.instante) + '. As datas sem registro não representam novas consultas.') + '</figcaption></figure>' +
    '<details class="price-history-records"><summary>Ver registros de preços</summary><table><caption class="sr-only">Registros de preço em ' + h(nomeLoja) + ', em reais e sem frete</caption><thead><tr><th scope="col">Data</th><th scope="col">Preço</th></tr></thead><tbody>' +
    registros.slice().reverse().map(registro => '<tr><td>' + dataCurta.format(registro.instante) + '</td><td>' + moeda(registro.preco) + '</td></tr>').join("") + '</tbody></table></details>';
}

function iniciarInspecaoHistorico(secao, registros) {
  const plot = secao.querySelector("[data-history-plot]");
  if (!plot || !registros.length) return () => {};
  const controle = new AbortController(), opcoes = {signal:controle.signal};
  const pontos = pontosHistorico(registros);
  const tooltip = plot.querySelector("[data-history-tooltip]");
  const marcador = plot.querySelector("[data-history-marker]");
  const guia = marcador.querySelector("line");
  const rotulo = plot.getAttribute("aria-label");
  let indiceAtual = registros.length - 1;
  function mostrar(indice, anunciar = false) {
    if (indice < 0 || indice >= registros.length) return;
    indiceAtual = indice;
    const ponto = pontos[indice], registro = registros[indice];
    const data = dataCurta.format(registro.instante), preco = moeda(registro.preco);
    guia.setAttribute("x1",ponto.x); guia.setAttribute("x2",ponto.x);
    marcador.querySelectorAll("ellipse").forEach(circulo => {
      circulo.setAttribute("cx",ponto.x); circulo.setAttribute("cy",ponto.y);
    });
    marcador.setAttribute("visibility","visible");
    tooltip.querySelector("[data-history-date]").textContent = data;
    tooltip.querySelector("[data-history-price]").textContent = preco;
    tooltip.hidden = false;
    const x = ponto.x / 640 * plot.clientWidth, y = ponto.y / 200 * plot.clientHeight;
    tooltip.style.left = Math.max(8,Math.min(x - tooltip.offsetWidth / 2,plot.clientWidth - tooltip.offsetWidth - 8)) + "px";
    const topo = y - tooltip.offsetHeight - 14;
    tooltip.style.top = Math.max(8,Math.min(topo < 8 ? y + 14 : topo,plot.clientHeight - tooltip.offsetHeight - 8)) + "px";
    plot.classList.add("is-inspecting");
    if (anunciar) {
      plot.setAttribute("aria-label",data + ": " + preco + ". " + rotulo);
      secao.querySelector("[data-history-status]").textContent = data + ": " + preco + ".";
    }
  }
  function esconder() {
    tooltip.hidden = true; marcador.setAttribute("visibility","hidden");
    plot.classList.remove("is-inspecting"); plot.setAttribute("aria-label",rotulo);
  }
  function ajustarMarcadores() {
    const {width,height} = plot.querySelector("svg").getBoundingClientRect();
    if (!width || !height) return;
    // O traçado ocupa toda a largura; compense a escala para manter os pontos circulares em pixels.
    plot.querySelectorAll("[data-history-radius]").forEach(ponto => {
      const raio = Number(ponto.dataset.historyRadius);
      ponto.setAttribute("rx",raio * 640 / width);
      ponto.setAttribute("ry",raio * 200 / height);
    });
    if (!tooltip.hidden) mostrar(indiceAtual);
  }
  const observar = typeof ResizeObserver === "function" ? new ResizeObserver(ajustarMarcadores) : null;
  observar?.observe(plot);
  window.addEventListener("resize",ajustarMarcadores,opcoes);
  ajustarMarcadores();
  function apontar(evento) {
    const r = plot.getBoundingClientRect();
    if (!r.width) return;
    const proporcao = Math.max(0,Math.min(1,((evento.clientX - r.left) / r.width * 640 - 12) / 616));
    const instante = registros[0].instante + proporcao * (registros.at(-1).instante - registros[0].instante);
    mostrar(indiceHistoricoMaisProximo(registros,instante));
  }
  plot.addEventListener("pointermove",apontar,{...opcoes,passive:true});
  plot.addEventListener("pointerdown",apontar,{...opcoes,passive:true});
  plot.addEventListener("pointerleave",evento => { if (evento.pointerType === "mouse" && document.activeElement !== plot) esconder(); },opcoes);
  plot.addEventListener("focus",() => mostrar(indiceAtual,true),opcoes);
  plot.addEventListener("blur",esconder,opcoes);
  secao.addEventListener("pointerdown",evento => { if (!plot.contains(evento.target)) esconder(); },opcoes);
  plot.addEventListener("keydown",evento => {
    if (evento.key === "Escape") { esconder(); return; }
    const indice = {ArrowLeft:Math.max(0,indiceAtual - 1),ArrowRight:Math.min(registros.length - 1,indiceAtual + 1),Home:0,End:registros.length - 1}[evento.key];
    if (indice === undefined) return;
    evento.preventDefault(); mostrar(indice,true);
  },opcoes);
  return () => { controle.abort(); observar?.disconnect(); };
}

export function historicoPrecosHtml(peca, agora = Date.now()) {
  const loja = nomesLojas[peca?.historico_loja] ? peca.historico_loja : "kabum";
  const nomeLoja = nomesLojas[loja];
  const registros = normalizarHistoricoPrecos(peca?.historico_precos, agora, loja);
  return '<section class="product-price-history glass-card" data-price-history aria-labelledby="price-history-title"><div class="price-history-heading"><div><h2 class="font-1-l" id="price-history-title">Histórico de preços</h2>' +
    '<p>Veja como o preço desta peça mudou ao longo do tempo.</p></div><span class="price-history-store">' + h(nomeLoja) + '</span></div>' +
    (registros.length ? '<div class="price-history-periods" role="group" aria-label="Período do histórico de preços">' + periodos.map(([valor, rotulo]) => '<button type="button" data-history-period="' + valor + '" aria-label="Mostrar histórico: ' + h(rotulo) + '" aria-pressed="' + (valor === "todos") + '">' + h(valor === 'todos' && peca?.historico_precos_incompleto ? 'Todos os registros carregados' : rotulo) + '</button>').join("") + '</div>' : '') +
    (peca?.historico_precos_incompleto ? '<p class="price-history-note">Exibindo somente os 1.000 registros mais recentes deste anúncio.</p>' : '') +
    '<div data-history-content>' + conteudoHistorico(registros, registros.length > 0, nomeLoja) + '</div>' +
    '<p class="price-history-note">Valores registrados, sem frete. O preço e a disponibilidade atuais devem ser confirmados na loja.</p><p class="sr-only" data-history-status role="status" aria-atomic="true"></p></section>';
}

export function iniciarHistoricoPrecos(raiz, peca, agora = Date.now()) {
  const secao = raiz.querySelector("[data-price-history]");
  if (!secao || secao.dataset.historyInitialized) return;
  secao.dataset.historyInitialized = "true";
  const loja = nomesLojas[peca?.historico_loja] ? peca.historico_loja : "kabum";
  const nomeLoja = nomesLojas[loja];
  const registros = normalizarHistoricoPrecos(peca?.historico_precos, agora, loja);
  let limparInspecao = iniciarInspecaoHistorico(secao,registros);
  secao.querySelectorAll("[data-history-period]").forEach(botao => botao.addEventListener("click", () => {
    if (botao.getAttribute("aria-pressed") === "true") return;
    const periodo = botao.dataset.historyPeriod;
    const filtrados = filtrarHistoricoPrecos(registros, periodo, agora);
    limparInspecao();
    secao.querySelectorAll("[data-history-period]").forEach(outro => outro.setAttribute("aria-pressed", String(outro === botao)));
    secao.querySelector("[data-history-content]").innerHTML = conteudoHistorico(filtrados, registros.length > 0, nomeLoja);
    limparInspecao = iniciarInspecaoHistorico(secao,filtrados);
    secao.querySelector("[data-history-status]").textContent = filtrados.length ? filtrados.length + ' registros de preço exibidos para ' + botao.textContent.toLowerCase() + '.' : 'Nenhum registro de preço neste período. Escolha um período maior.';
  }));
}
