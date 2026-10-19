import { criarClienteFPSHQ, REFERENCIA_FPS, JOGOS_INICIAIS } from "../experimentos/fpshq.js";
import { htmlSeguro as h } from "../build/catalogo.js";
import { resultadoDesempenhoHtml,resolucoesHtml } from "../experimentos/benchmark-view.js";
import { definirDetalheAberto,iniciarDetalhesAnimados } from "../components/animated-details.js";

document.addEventListener("DOMContentLoaded",() => {
  const form = document.querySelector("#fpshq-test-form");
  if (!form) return;
  let armazenamento;
  try { armazenamento = sessionStorage; } catch { /* O teste também funciona sem cache persistente. */ }
  const cliente = criarClienteFPSHQ({armazenamento});
  const jogo = form.querySelector("#fpshq-game"), res = form.querySelector("#fpshq-resolution"), preset = form.querySelector("#fpshq-preset");
  const feedback = document.querySelector("#fpshq-feedback"), resultado = document.querySelector("#fpshq-result");
  const buscar = document.querySelector("#fpshq-search"), textoBusca = document.querySelector("#fpshq-search-text");
  const feedbackBusca = document.querySelector("#fpshq-search-status"), resultadosBusca = document.querySelector("#fpshq-search-results");
  const painelBusca = document.querySelector(".fpshq-search-details"), aviso = document.querySelector("#fpshq-notice");
  const fonte = document.querySelector("#fpshq-source");
  const painel = document.querySelector(".fpshq-panel"), vazio = document.querySelector("#fpshq-empty");
  const interfaces = document.querySelector("#fpshq-layouts");
  const consulta = form.querySelector('button[type="submit"]');
  iniciarDetalhesAnimados(document.querySelector("#teste-desempenho"));
  // Uma só interface de dados: trocar o layout não recria o DOM nem consulta a API.
  const aplicarInterface = opcao => {
    if (!opcao?.matches('input[name="fpshq-layout"]') || !["cards","panel","compact"].includes(opcao.value)) return;
    painel.dataset.layout = opcao.value;
  };
  interfaces.addEventListener("change",evento => aplicarInterface(evento.target));
  aplicarInterface(interfaces.querySelector('input:checked'));
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
    consulta.disabled = ocupado; buscar.disabled = ocupado;
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
    resultado.innerHTML = resultadoDesempenhoHtml(dados);
    resultado.hidden = false;
    vazio.hidden = true;
    iniciarDetalhesAnimados(resultado);
    atualizarFonte(dados.url); mostrarAviso(true);
  }
  resultado.addEventListener("change",evento => {
    if (!dadosAtuais || !evento.target.matches('input[name="fpshq-comparison-quality"]')) return;
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
    if (ocupado || !form.reportValidity()) return;
    const atual = ++versao;
    ocupado = true; acaoAtual = "consulta"; controles(); resultado.hidden = true; resultado.setAttribute("aria-busy","true");
    informar("Consultando desempenho…");
    try {
      const dados = await cliente.consultar({...REFERENCIA_FPS,game:jogo.value,res:res.value,preset:preset.value});
      if (atual === versao) { renderizar(dados); informar(""); }
      ocupado = false; acaoAtual = "";
    } catch (erro) { ocupado = false; acaoAtual = ""; if (atual === versao) tratarErro(erro); }
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
      const jogos = await cliente.buscarJogos(textoBusca.value);
      if (atual === versaoBusca) {
        incluirJogos(jogos);
        resultadosBusca.innerHTML = jogos.map(item => '<li><button type="button" data-fpshq-game="' + h(item.slug) + '" aria-label="Selecionar ' + h(item.name) + '">' + h(item.name) + '<span aria-hidden="true">→</span></button></li>').join("");
        resultadosBusca.hidden = !jogos.length;
        informar(jogos.length ? "Selecione o jogo desejado." : "Nenhum jogo encontrado. Tente outro nome.","info",feedbackBusca);
      }
      ocupado = false; acaoAtual = "";
    } catch (erro) { ocupado = false; acaoAtual = ""; if (atual === versaoBusca) tratarErro(erro,feedbackBusca); }
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
});
