import { REFERENCIA_FPS,JOGOS_INICIAIS } from "./config.js";
import { criarClienteBenchmark } from "../api/benchmark/consultarBenchmark.js";
import { htmlSeguro as h } from "../build/catalogo.js";
import { resultadoDesempenhoHtml,resolucoesHtml } from "./view.js";
import { definirDetalheAberto,iniciarDetalhesAnimados } from "../components/animated-details.js";

export function iniciarPainelBenchmark(raiz,{prefixo = "fpshq",hardware = REFERENCIA_FPS,cliente = criarClienteBenchmark()} = {}) {
  const localizar = seletor => raiz.querySelector(seletor.replaceAll("#fpshq-","#" + prefixo + "-"));
  const form = localizar("#fpshq-test-form");
  if (!form || form.dataset.benchmarkReady) return;
  form.dataset.benchmarkReady = "true";
  const controle = new AbortController();
  let ativo = true;
  const jogo = localizar("#fpshq-game"), res = localizar("#fpshq-resolution"), preset = localizar("#fpshq-preset");
  const feedback = localizar("#fpshq-feedback"), resultado = localizar("#fpshq-result");
  const buscar = localizar("#fpshq-search"), textoBusca = localizar("#fpshq-search-text");
  const feedbackBusca = localizar("#fpshq-search-status"), resultadosBusca = localizar("#fpshq-search-results");
  const painelBusca = localizar(".fpshq-search-details"), aviso = localizar("#fpshq-notice");
  const fonte = localizar("#fpshq-source");
  const painel = localizar(".fpshq-panel"), vazio = localizar("#fpshq-empty");
  const interfaces = localizar("#fpshq-layouts");
  const consulta = form.querySelector('button[type="submit"]');
  iniciarDetalhesAnimados(raiz);
  // Uma só interface de dados: trocar o layout não recria o DOM nem consulta a API.
  const aplicarInterface = opcao => {
    if (!opcao?.matches('input[name="fpshq-layout"]') || !["cards","panel","compact"].includes(opcao.value)) return;
    painel.dataset.layout = opcao.value;
  };
  interfaces?.addEventListener("change",evento => aplicarInterface(evento.target));
  aplicarInterface(interfaces?.querySelector('input:checked'));
  let ocupado = false, versao = 0, versaoBusca = 0, cooldown, dadosAtuais = null, acaoAtual = "";
  const informar = (mensagem,tom = "info",alvo = feedback) => {
    alvo.textContent = mensagem; alvo.dataset.tone = tom; alvo.hidden = !mensagem;
  };
  function incluirJogos(jogos) {
    for (const item of jogos) {
      if ([...jogo.options].some(opcao => opcao.value === item.slug)) continue;
      jogo.add(new Option(item.name,item.slug));
    }
  }
  incluirJogos(JOGOS_INICIAIS);
  function controles() {
    consulta.disabled = ocupado || Boolean(hardware.motivo); buscar.disabled = ocupado;
    if (hardware.motivo) consulta.dataset.disabledReason = hardware.motivo;
    consulta.textContent = acaoAtual === "consulta" ? "Consultando…" : "Ver desempenho";
    consulta.setAttribute("aria-label",acaoAtual === "consulta" ? "Consultando desempenho esperado na FPSHQ" : "Ver desempenho esperado na FPSHQ");
    buscar.textContent = acaoAtual === "busca" ? "Buscando…" : "Buscar";
    buscar.setAttribute("aria-label",acaoAtual === "busca" ? "Buscando jogos na FPSHQ" : "Buscar jogos na FPSHQ");
    resultadosBusca.querySelectorAll("button").forEach(botao => { botao.disabled = ocupado; });
  }
  function mostrarAviso(mostrar) {
    aviso.hidden = !mostrar;
    if (!mostrar) definirDetalheAberto(aviso.querySelector("details"),false,{animar:false});
  }
  function limparResultado() {
    versao++; dadosAtuais = null; resultado.hidden = true; resultado.replaceChildren(); vazio.hidden = false;
  }
  function atualizarFonte(url = "https://fpshq.com/pt/api/") { fonte.href = url; }
  function tratarErro(erro,alvo = feedback) {
    informar(erro.message,"error",alvo);
    if (erro.espera > 0) {
      ocupado = true; acaoAtual = "espera";
      let restante = erro.espera;
      informar(erro.message + " Aguarde " + restante + " s.","error",alvo);
      clearInterval(cooldown);
      cooldown = setInterval(() => {
        restante--;
        if (restante > 0) informar("Aguarde " + restante + " s para consultar novamente.","error",alvo);
        else { clearInterval(cooldown); ocupado = false; acaoAtual = ""; controles(); informar("Você já pode consultar novamente.","info",alvo); }
      },1000);
    }
  }
  function renderizar(dados) {
    dadosAtuais = dados;
    resultado.innerHTML = resultadoDesempenhoHtml(dados,prefixo);
    resultado.hidden = false;
    vazio.hidden = true;
    iniciarDetalhesAnimados(resultado);
    atualizarFonte(dados.url); mostrarAviso(true);
  }
  resultado.addEventListener("change",evento => {
    if (!dadosAtuais || !evento.target.matches('input[data-benchmark-quality]')) return;
    resultado.querySelector(".fpshq-resolutions").innerHTML = resolucoesHtml(dadosAtuais.matriz,evento.target.value);
  });
  form.addEventListener("change",evento => {
    limparResultado(); informar("");
    if (evento.target === jogo) {
      mostrarAviso(Boolean(jogo.value));
      atualizarFonte("https://fpshq.com/pt/games/" + jogo.value + "/");
    }
  });
  form.addEventListener("submit",async evento => {
    evento.preventDefault();
    if (ocupado || hardware.motivo || !form.reportValidity()) return;
    const atual = ++versao;
    ocupado = true; acaoAtual = "consulta"; controles(); resultado.hidden = true; resultado.setAttribute("aria-busy","true");
    informar("Consultando desempenho…");
    try {
      const dados = await cliente.consultar({...hardware,game:jogo.value,res:res.value,preset:preset.value},{signal:controle.signal});
      if (ativo && atual === versao) { renderizar(dados); informar(""); }
      ocupado = false; acaoAtual = "";
    } catch (erro) { ocupado = false; acaoAtual = ""; if (ativo && atual === versao) tratarErro(erro); }
    finally { resultado.setAttribute("aria-busy","false"); controles(); }
  });
  buscar.addEventListener("click",async () => {
    if (ocupado) return;
    const atual = ++versaoBusca;
    limparResultado(); mostrarAviso(false); informar("");
    resultadosBusca.hidden = true; resultadosBusca.replaceChildren();
    ocupado = true; acaoAtual = "busca"; controles();
    informar("Buscando jogos…","info",feedbackBusca);
    try {
      const jogos = await cliente.buscarJogos(textoBusca.value,{signal:controle.signal});
      if (ativo && atual === versaoBusca) {
        incluirJogos(jogos);
        resultadosBusca.innerHTML = jogos.map(item => '<li><button type="button" data-fpshq-game="' + h(item.slug) + '" aria-label="Selecionar ' + h(item.name) + '">' + h(item.name) + '<span aria-hidden="true">→</span></button></li>').join("");
        resultadosBusca.hidden = !jogos.length;
        informar(jogos.length ? "Selecione o jogo desejado." : "Nenhum jogo encontrado. Tente outro nome.","info",feedbackBusca);
      }
      ocupado = false; acaoAtual = "";
    } catch (erro) { ocupado = false; acaoAtual = ""; if (ativo && atual === versaoBusca) tratarErro(erro,feedbackBusca); }
    finally { controles(); }
  });
  resultadosBusca.addEventListener("click",evento => {
    const botao = evento.target.closest("button[data-fpshq-game]");
    if (!botao || ocupado) return;
    jogo.value = botao.dataset.fpshqGame;
    jogo.dispatchEvent(new Event("change",{bubbles:true}));
    definirDetalheAberto(painelBusca,false,{animar:false}); informar("","info",feedbackBusca);
    jogo.focus({preventScroll:true});
  });
  textoBusca.addEventListener("input",() => {
    versaoBusca++; resultadosBusca.hidden = true; resultadosBusca.replaceChildren();
    informar("","info",feedbackBusca);
  });
  textoBusca.addEventListener("keydown",evento => { if (evento.key === "Enter") { evento.preventDefault(); buscar.click(); } });
  controles();
  if (hardware.motivo) informar(hardware.motivo);
  return () => { ativo = false; versao++; versaoBusca++; clearInterval(cooldown); controle.abort(); };
}
