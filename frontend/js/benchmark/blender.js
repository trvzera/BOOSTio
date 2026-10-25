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

export function painelBlenderHtml(dispositivos) {
  return '<section class="blender-panel" aria-label="Desempenho de renderização no Blender"><p class="planning-help">Consulte resultados públicos de uma peça, sem executar testes no seu computador.</p>' +
    '<form id="blender-form"><label class="test-field" for="blender-device">Dispositivo de renderização<select id="blender-device">' +
    Object.entries(dispositivos).filter(([,nome]) => nome).map(([tipo,nome]) => '<option value="' + tipo + '">' + tipo.toUpperCase() + ' · ' + h(nome) + '</option>').join("") +
    '</select></label><button type="submit" class="btn-primary" aria-label="Consultar desempenho no Blender" ' +
    (!dispositivos.cpu && !dispositivos.gpu ? 'disabled data-disabled-reason="Não há CPU ou GPU com identificação cadastrada para o Blender."' : '') + '>Consultar Blender</button></form>' +
    '<p class="test-feedback" role="status" aria-live="polite" id="blender-feedback">' + (!dispositivos.cpu && !dispositivos.gpu ? 'Identifique uma CPU ou GPU no catálogo para consultar seus resultados.' : '') + '</p>' +
    '<div id="blender-result" aria-live="polite"></div><p class="planning-help">A pontuação representa renderização no Cycles, não FPS. CPU e GPU não são somadas. RAM, VRAM, drivers e a cena alteram o resultado real; a fonte pode agrupar variantes do mesmo nome.</p>' +
    '<p class="fpshq-attribution">Fonte: <a href="https://opendata.blender.org/about/" target="_blank" rel="noopener noreferrer" aria-label="Ver metodologia do Blender Open Data em nova aba">Blender Open Data</a></p></section>';
}

export function iniciarPainelBlender(raiz,dispositivos,{cliente = criarClienteBenchmark()} = {}) {
  const form = raiz.querySelector("#blender-form"), feedback = raiz.querySelector("#blender-feedback"), resultado = raiz.querySelector("#blender-result");
  const botao = form.querySelector('button[type="submit"]'), controle = new AbortController();
  let ativo = true, ocupado = false, espera = 0, timer;
  form.addEventListener("submit",async evento => {
    evento.preventDefault();
    const tipo = form.querySelector("select").value, dispositivo = dispositivos[tipo];
    if (ocupado || espera || !dispositivo) return;
    ocupado = true; botao.disabled = true; resultado.replaceChildren(); resultado.setAttribute("aria-busy","true");
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
      if (erro.espera > 0) {
        espera = Math.min(erro.espera,3600);
        botao.dataset.disabledReason = "Aguarde o intervalo solicitado pela fonte.";
        timer = setInterval(() => { if (--espera <= 0) { clearInterval(timer); botao.disabled = false; } },1000);
      }
    } finally {
      ocupado = false;
      if (ativo) { resultado.setAttribute("aria-busy","false"); botao.disabled = espera > 0; }
    }
  });
  return () => { ativo = false; clearInterval(timer); controle.abort(); };
}
