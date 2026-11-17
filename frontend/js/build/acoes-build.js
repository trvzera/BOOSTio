import { htmlSeguro as h, moeda, nomePeca, imagemPeca } from "./catalogo.js";
import { cartoesOfertasHtml } from "./ofertas-peca.js";
import { itensSelecionados, itensCategoria, informacoesRam } from "./estado.js";
import { avaliarBuild } from "./compatibilidade.js";
import { normalizarRede, resumoRede } from "./rede.js";
import { iniciarIcones } from "../components/ui.js";
import { hardwareBlender } from "../benchmark/hardware.js";
import { dashboardBenchmarkHtml, iniciarDashboardBenchmark } from "../benchmark/dashboard.js";
import { catalogoBuilds } from "../api/build/builds.js";
import { fetchComErro } from "../api/_shared/fetchComErro.js";
import { compararCatalogosCompra } from "./compra-revalidacao.js";
import { avaliarDisponibilidadeFps } from "../benchmark/disponibilidade.js";

export function avisoCompraHtml() {
  return '<p class="purchase-notice">A BOOSTio não vende, entrega ou processa pagamentos de peças e periféricos. Os links abrem lojas de terceiros, responsáveis pela venda e pelo atendimento da compra. Confira preço, estoque, frete, garantia e devolução diretamente na loja.</p>';
}
export function avisoFreteHtml() {
  return '<p class="shipping-notice planning-help" role="note"><strong>Frete não incluído</strong>Reserve parte do orçamento para a entrega. O valor varia conforme seu CEP e as lojas escolhidas.</p>';
}
export function abrirDialogoBuild(titulo,conteudo) {
  const anterior = document.activeElement;
  document.querySelectorAll("dialog.build-action-dialog").forEach(dialogo => dialogo.close());
  const dialogo = document.createElement("dialog");
  dialogo.className = "build-action-dialog";
  dialogo.setAttribute("aria-labelledby","build-action-title");
  dialogo.innerHTML = '<div class="build-action-heading"><h2 id="build-action-title" class="font-1-l" tabindex="-1">' + h(titulo) + '</h2><button type="button" class="build-action-close" aria-label="Fechar janela">×</button></div>' + conteudo;
  dialogo.querySelector(".build-action-close").onclick = () => dialogo.close();
  dialogo.addEventListener("click",e => {
    const r = dialogo.getBoundingClientRect();
    if (e.target === dialogo && (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom)) dialogo.close();
  });
  dialogo.addEventListener("close",() => { dialogo.remove(); if (anterior?.isConnected) anterior.focus({preventScroll:true}); },{once:true});
  document.body.append(dialogo);
  dialogo.showModal();
  dialogo.querySelector("h2").focus({preventScroll:true});
  iniciarIcones(dialogo);
  return dialogo;
}
export function motivoBenchmark(build,catalogo) {
  const avaliacao = avaliarBuild(build,catalogo);
  if (String(build.id).startsWith("s-")) {
    if (!itensCategoria(build,"processador").length)
      return "Escolha um processador para consultar os testes de desempenho.";
    if (avaliacao.erros.length) return "Resolva os erros de compatibilidade antes de testar o desempenho.";
    return "";
  }
  if (avaliacao.preenchidos !== avaliacao.total) return "Complete 100% das peças da build para testar o desempenho.";
  if (avaliacao.erros.length) return "Resolva os erros de compatibilidade antes de testar o desempenho.";
  return "";
}
export function abrirBenchmark(build,catalogo,{publica = false} = {}) {
  const motivo = motivoBenchmark(build,catalogo);
  if (motivo) throw new Error(motivo);
  const peca = categoria => catalogo.find(p => p.id === itensCategoria(build,categoria)[0]?.id);
  const cpu = peca("processador"), gpu = peca("placa_video"), ram = informacoesRam(build,catalogo);
  const buildId = /^(?:s-)?[1-9][0-9]{0,17}$/.test(String(build.id)) ? String(build.id) : null;
  const prefixo = "build-benchmark";
  const memoria = ram.itens.length && ram.itens.every(({peca}) => Number.isInteger(peca?.capacidade_gb) && peca.capacidade_gb > 0) ? ram.capacidade : null;
  const dispositivos = hardwareBlender(cpu,gpu);
  const disponibilidadeFps = avaliarDisponibilidadeFps(build,catalogo);
  const dialogo = abrirDialogoBuild("Desempenho esperado",dashboardBenchmarkHtml({prefixo,titulo:build.titulo,
    cpu:cpu ? nomePeca(cpu) : null,gpu:gpu ? nomePeca(gpu) : null,memoria,verificarRequisitos:Boolean(buildId),dispositivos}));
  dialogo.classList.add("benchmark-dialog");
  const limpar = iniciarDashboardBenchmark(dialogo.querySelector("[data-benchmark-dashboard]"),
    {prefixo,hardware:disponibilidadeFps.permitido ? disponibilidadeFps.hardware : {motivo:disponibilidadeFps.motivo},dispositivos,buildId,publica});
  dialogo.addEventListener("close",limpar,{once:true});
  return dialogo;
}
export function abrirCompraBuild(build,catalogo,{publica = false,loja,recarregar} = {}) {
  const itens = itensSelecionados(build,catalogo);
  if (!itens.length) throw new Error("Adicione pelo menos uma peça à build para consultar lojas.");
  const estado = structuredClone(build), conta = /^s-/.test(String(build.id));
  const carregar = recarregar || (conta ? async signal => {
    if (!publica) return (await catalogoBuilds({signal,cache:"no-store"})).pecas;
    const {build:atual}=await fetchComErro('/build/'+encodeURIComponent(build.id)+'/publica',{method:'GET',cache:'no-store',signal});
    if (atual?.id!==build.id||atual.estado?.visibilidade!=="publico") throw new Error("Esta build não está mais disponível publicamente.");
    return atual.pecas;
  } : async()=>catalogo);
  const dialogo=abrirDialogoBuild(itens.length===1?"Onde comprar a peça":"Onde comprar a build",'<div class="purchase-body"><p class="purchase-context">'+h(itens.length===1?nomePeca(itens[0].peca):build.titulo)+'</p>'
    +'<p class="planning-help" data-purchase-status role="status" aria-live="polite">Consultando o catálogo atualizado…</p><div data-purchase-content aria-busy="true"></div><button type="button" class="btn-secondary" data-purchase-retry hidden aria-label="Tentar verificar preços e estoque novamente">Tentar novamente</button>'
    +avisoFreteHtml()+'<details class="purchase-information"><summary>Sobre a compra nas lojas</summary>'+avisoCompraHtml()+'</details></div>');
  dialogo.classList.add("build-purchase-dialog");
  let consulta;
  const conteudo=dialogo.querySelector('[data-purchase-content]'),status=dialogo.querySelector('[data-purchase-status]'),repetir=dialogo.querySelector('[data-purchase-retry]');
  async function verificar() {
    consulta?.abort();const atual=consulta=new AbortController();repetir.hidden=true;conteudo.innerHTML="";conteudo.setAttribute("aria-busy","true");
    status.textContent="Consultando o catálogo atualizado…";status.dataset.tone="info";
    try {
      const atualizado=await carregar(atual.signal);
      if (atual.signal.aborted||!dialogo.open) return;
      const comparacao=compararCatalogosCompra(estado,catalogo,atualizado);
      conteudo.innerHTML=conteudoCompra(estado,atualizado,comparacao,loja);
      status.textContent=conta||recarregar?"Catálogo consultado agora. Preços e estoque são os últimos registros da BOOSTio, não uma cotação em tempo real; confirme na loja.":"Catálogo demonstrativo: não é possível confirmar preço ou estoque real neste modo.";
      iniciarIcones(dialogo);
    } catch(erro) {
      if (atual.signal.aborted||!dialogo.open) return;
      status.textContent="Não foi possível revalidar a compra: "+erro.message;status.dataset.tone="error";repetir.hidden=false;
    } finally { if (!atual.signal.aborted) conteudo.setAttribute("aria-busy","false"); }
  }
  repetir.onclick=verificar;
  dialogo.addEventListener("close",()=>consulta?.abort(),{once:true});
  verificar();return dialogo;
}

function linksCompra(peca, loja, referenciaIndisponivel) {
  if (!peca) return "";
  const ofertas = cartoesOfertasHtml(peca,{loja,somenteDisponiveis:true,referenciaIndisponivel});
  return ofertas ? '<div class="build-store-links">' + ofertas + '</div>' : '<p class="planning-help">Não há ofertas disponíveis para esta seleção de loja.</p>';
}

export function conteudoCompra(build,catalogo,comparacao,loja) {
  const itens = itensSelecionados(build,catalogo);
  const linhas = comparacao.linhas.map(({item,depois:peca,indisponivel,antigo,novo,diferenca}) => '<article class="build-purchase-item"><div class="purchase-product">' + imagemPeca(peca,"purchase-product-image") + '<div><h3 class="font-1-m-b">' + h(peca ? nomePeca(peca) : item.proprio || "Modelo não encontrado") + '</h3><p class="planning-help">Quantidade: ' + item.quantidade
    +(novo!=null?' · preço cadastrado: '+moeda(novo*item.quantidade/100):' · sem cotação confirmada')
    +(diferenca!=null&&diferenca!==0?' · antes: '+moeda(antigo*item.quantidade/100)+' · diferença: '+(diferenca>0?'+':'−')+moeda(Math.abs(diferenca)/100):'')+'</p></div></div>'
    +(indisponivel ? '<p class="planning-help" data-tone="warning">Referência indisponível ou sem preço/estoque confirmado no catálogo. Confira separadamente as ofertas de outras lojas, quando disponíveis.</p>' : '')
    + linksCompra(peca,loja,indisponivel) + '</article>').join("");
  const rede = normalizarRede(build.rede);
  const conexoes = rede.tipo === "ambos" ? [{...rede,tipo:"cabo"},{...rede,tipo:"wifi",comprimentoCaboM:null}] : [rede];
  const extra = conexoes.map(rede => build.incluirRede && rede.tipo !== "indefinido" && rede.possuiAcessorio === false &&
    !itens.some(({categoria}) => categoria === (rede.tipo === "cabo" ? "cabo_rede" : "adaptador_wifi")) ? '<div class="benchmark-empty"><strong>Acessório de rede a incluir</strong><p>' + h(resumoRede(rede)) + (rede.comprimentoCaboM ? ' · ' + rede.comprimentoCaboM + ' m' : '') + '. Escolha um produto com as especificações necessárias na loja. Esse acessório ainda não tem oferta cadastrada.</p></div>' : '').join("");
  return '<div class="purchase-totals"><div><span>Total de referência'+(comparacao.parcial?' (parcial)':'')+'</span><strong>'+moeda(comparacao.depois/100)+'</strong></div><p>Total anterior: '+moeda(comparacao.antes/100)
    +(comparacao.diferenca!=null?' · diferença: '+(comparacao.diferenca>0?'+':comparacao.diferenca<0?'−':'')+moeda(Math.abs(comparacao.diferenca)/100):' · diferença completa indisponível')+'</p></div><p class="purchase-total-note">Sem frete. Os valores são referências do catálogo; cada loja pode ter um preço diferente.</p><div class="build-purchase-list">'+linhas+'</div>'+extra;
}
