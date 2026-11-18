import { htmlSeguro as h } from "../build/catalogo.js";
import { criarClienteBenchmark } from "../api/benchmark/consultarBenchmark.js";

export function mensagemFalhaBlender(erro) {
  const mensagem = erro?.message || "Não foi possível consultar o Blender agora.";
  const referencia = [];
  if (Number.isInteger(erro?.status)) referencia.push("HTTP " + erro.status + " da BOOSTio");
  if (erro?.codigo) referencia.push(erro.codigo);
  if (Number.isInteger(erro?.diagnostico?.httpProvedor)) referencia.push("Blender: HTTP " + erro.diagnostico.httpProvedor);
  return mensagem + (referencia.length ? " Referência: " + referencia.join(" · ") + "." : "");
}

export function painelBlenderHtml(dispositivos,{prefixo = "blender",disponibilidade} = {}) {
  const id = nome => h(prefixo + "-" + nome);
  return '<section class="blender-panel" aria-label="Desempenho de renderização no Blender"><p class="planning-help">Consulte resultados públicos de uma peça, sem executar testes no seu computador.</p>' +
    '<form id="' + id("form") + '"><label class="test-field" for="' + id("device") + '">Dispositivo de renderização<select id="' + id("device") + '">' +
    Object.entries(disponibilidade || dispositivos).filter(([,valor]) => valor).map(([tipo]) => '<option value="' + tipo + '">' + tipo.toUpperCase() + ' · ' + h(dispositivos[tipo] || "Identificação a confirmar") + '</option>').join("") +
    '</select></label><button type="submit" class="btn-primary" aria-label="Consultar desempenho no Blender" ' +
    (!dispositivos.cpu && !dispositivos.gpu ? 'disabled data-disabled-reason="Não há CPU ou GPU com identificação cadastrada para o Blender."' : '') + '>Consultar Blender</button></form>' +
    '<p class="test-feedback" data-blender-feedback role="status" aria-live="polite" id="' + id("feedback") + '">' + (!dispositivos.cpu && !dispositivos.gpu ? 'Identifique uma CPU ou GPU no catálogo para consultar seus resultados.' : '') + '</p>' +
    '<div id="' + id("result") + '" data-blender-result aria-live="polite"></div><p class="planning-help">A pontuação representa renderização no Cycles, não FPS. CPU e GPU não são somadas. RAM, VRAM, drivers e a cena alteram o resultado real; a fonte pode agrupar variantes do mesmo nome.</p>' +
    '<p class="fpshq-attribution">Fonte: <a href="https://opendata.blender.org/about/" target="_blank" rel="noopener noreferrer" aria-label="Ver metodologia do Blender Open Data em nova aba">Blender Open Data</a></p></section>';
}

export function iniciarPainelBlender(raiz,dispositivos,{cliente = criarClienteBenchmark(),prefixo = "blender",disponibilidade} = {}) {
  const form = raiz.querySelector("#" + prefixo + "-form"), feedback = raiz.querySelector("#" + prefixo + "-feedback"), resultado = raiz.querySelector("#" + prefixo + "-result");
  const botao = form.querySelector('button[type="submit"]'), controle = new AbortController();
  const seletor = form.querySelector("select");
  const semDados = new Map();
  let ativo = true, ocupado = false, espera = 0, timer;
  const motivo = () => disponibilidade?.[seletor.value]?.permitido === false ? disponibilidade[seletor.value].motivo
    : semDados.get(seletor.value) || (dispositivos[seletor.value] ? "" : "Identifique uma CPU ou GPU no catálogo para consultar seus resultados.");
  function controles() {
    const bloqueio = motivo() || (espera > 0 ? "Aguarde o intervalo solicitado pela fonte." : ocupado ? "Aguarde a consulta atual." : "");
    botao.disabled = Boolean(bloqueio); seletor.disabled = ocupado;
    if (bloqueio) botao.dataset.disabledReason = bloqueio;
    else delete botao.dataset.disabledReason;
  }
  if (disponibilidade) {
    const inicial = ["cpu","gpu"].find(tipo => disponibilidade[tipo]?.permitido);
    if (inicial) seletor.value = inicial;
  }
  controles();
  if (motivo()) { feedback.textContent = motivo(); feedback.dataset.tone = "warning"; }
  seletor.addEventListener("change",() => {
    resultado.replaceChildren(); feedback.textContent = motivo() || "Pronto para consultar " + seletor.value.toUpperCase() + ".";
    feedback.dataset.tone = motivo() ? "warning" : "info"; controles();
  },{signal:controle.signal});
  form.addEventListener("submit",async evento => {
    evento.preventDefault();
    const tipo = form.querySelector("select").value, dispositivo = dispositivos[tipo];
    if (ocupado || espera || motivo()) return;
    if (typeof navigator !== "undefined" && navigator.onLine === false) {
      feedback.textContent = "Você está sem conexão com a internet. Reconecte-se para consultar o Blender.";
      feedback.dataset.tone = "error"; return;
    }
    ocupado = true; controles(); resultado.replaceChildren(); resultado.setAttribute("aria-busy","true");
    feedback.textContent = "Consultando Blender Open Data…"; feedback.dataset.tone = "info";
    try {
      const dados = await cliente.consultarBlender({dispositivo,tipo},{signal:controle.signal});
      if (!ativo) return;
      const numero = new Intl.NumberFormat("pt-BR",{maximumFractionDigits:2});
      resultado.innerHTML = '<article class="blender-score"><h3>' + h(dados.dispositivo) + '</h3><strong>' + h(numero.format(dados.score)) + '<small>amostras/min · mediana</small></strong>' +
        '<p>Blender ' + h(dados.versao) + ' · ' + h(dados.metodo) + ' · ' + h(dados.quantidade) + ' resultado(s)</p>' +
        (dados.quantidade < 5 ? '<p class="planning-help">Poucos resultados disponíveis: interprete a mediana com cautela.</p>' : '') +
        '<p class="planning-help">Maior pontuação indica mais amostras renderizadas por minuto, não um tempo garantido para seu projeto.</p>' +
        '<a href="' + h(dados.url) + '" target="_blank" rel="noopener noreferrer" aria-label="Ver resultados deste dispositivo no Blender Open Data">Ver resultados na fonte</a></article>';
      feedback.textContent = (dados.cache ? "Dados em cache" : "Consultado agora") + " · " + new Date(dados.consultadoEm).toLocaleString("pt-BR");
    } catch (erro) {
      if (!ativo) return;
      feedback.textContent = mensagemFalhaBlender(erro);
      feedback.dataset.tone = erro.codigo === "sem-dados" ? "warning" : "error";
      if (erro.codigo === "sem-dados") semDados.set(tipo,"A fonte não encontrou resultados públicos para esta " + tipo.toUpperCase() + ". Consulte o outro dispositivo, se disponível. Nenhuma pontuação foi inventada.");
      if (erro.espera > 0) {
        espera = Math.min(erro.espera,3600);
        timer = setInterval(() => { if (--espera <= 0) { clearInterval(timer); controles(); } },1000);
      }
    } finally {
      ocupado = false;
      if (ativo) { resultado.setAttribute("aria-busy","false"); controles(); }
    }
  });
  return () => { ativo = false; clearInterval(timer); controle.abort(); };
}
