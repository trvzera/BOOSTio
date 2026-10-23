import { htmlSeguro as h, moeda, nomePeca, ofertasPeca } from "./catalogo.js";
import { itensSelecionados, itensCategoria, informacoesRam } from "./estado.js";
import { avaliarBuild } from "./compatibilidade.js";
import { normalizarRede, resumoRede } from "./rede.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";
import { hardwareBenchmark, hardwareBlender } from "../benchmark/hardware.js";
import { painelBenchmarkHtml } from "../benchmark/painel.js";
import { iniciarPainelBenchmark } from "../benchmark/interface.js";
import { painelBlenderHtml, iniciarPainelBlender } from "../benchmark/blender.js";

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
  const prefixo = "build-fpshq";
  const dialogo = abrirDialogoBuild("Desempenho esperado",'<p class="planning-help">' + h(build.titulo) + '</p>' +
    '<div class="benchmark-type-picker" role="group" aria-label="Escolha o tipo de teste"><button type="button" class="btn-secondary" data-benchmark-type="games" aria-pressed="false" aria-label="Selecionar teste de desempenho em jogos">' + iconeAnimado("gamepad") + '<span>Jogos · FPS</span></button><button type="button" class="btn-secondary" data-benchmark-type="blender" aria-pressed="false" aria-label="Selecionar teste de renderização no Blender">' + iconeAnimado("microchip") + '<span>Blender · Renderização</span></button></div><div data-benchmark-content><p class="planning-help">Escolha qual desempenho deseja consultar. Nenhum teste é executado no seu computador.</p></div>');
  dialogo.classList.add("benchmark-dialog");
  let limpar;
  dialogo.querySelectorAll("[data-benchmark-type]").forEach(botao => botao.addEventListener("click",() => {
    if (botao.getAttribute("aria-pressed") === "true") return;
    limpar?.();
    dialogo.querySelectorAll("[data-benchmark-type]").forEach(outro => outro.setAttribute("aria-pressed",String(outro === botao)));
    const conteudo = dialogo.querySelector("[data-benchmark-content]");
    if (botao.dataset.benchmarkType === "games") {
      const memoria = ram.itens.length && ram.itens.every(({peca}) => Number.isInteger(peca?.capacidade_gb) && peca.capacidade_gb > 0) ? ram.capacidade : null;
      conteudo.innerHTML = painelBenchmarkHtml({prefixo,hardware:nomePeca(cpu) + " · " + (gpu ? nomePeca(gpu) : "Vídeo integrado"),memoria,verificarRequisitos:Boolean(buildId)});
      limpar = iniciarPainelBenchmark(dialogo,{prefixo,hardware:hardwareBenchmark(cpu,gpu),buildId,publica});
    } else {
      const dispositivos = hardwareBlender(cpu,gpu);
      conteudo.innerHTML = painelBlenderHtml(dispositivos);
      limpar = iniciarPainelBlender(dialogo,dispositivos);
    }
  }));
  dialogo.addEventListener("close",() => limpar?.(),{once:true});
  return dialogo;
}
export function abrirCompraBuild(build,catalogo) {
  const itens = itensSelecionados(build,catalogo);
  if (!itens.length) throw new Error("Adicione pelo menos uma peça à build para consultar lojas.");
  const linhas = itens.map(({item,peca}) => '<article class="build-purchase-item"><h3 class="font-1-m-b">' + h(peca ? nomePeca(peca) : item.proprio || "Modelo não encontrado") + '</h3><p class="planning-help">Quantidade: ' + item.quantidade + (peca ? ' · preço de referência: ' + moeda(Number(peca.preco || 0) * item.quantidade) : ' · peça própria, sem compra indicada') + '</p>' +
    (peca ? '<div class="build-store-links">' + ofertasPeca(peca).map(oferta => '<a class="build-store-link" href="' + h(oferta.url) + '" target="_blank" rel="noopener noreferrer" aria-label="' + (oferta.direta ? 'Comprar na ' : 'Buscar na ') + h(oferta.loja) + ' ' + h(oferta.preco != null ? moeda(oferta.preco) + ' por unidade' : 'Preço a consultar') + ': ' + h(nomePeca(peca)) + '"><img src="' + h(oferta.logo) + '" alt="' + h(oferta.loja) + '"><span>' + (oferta.direta ? 'Comprar na ' : 'Buscar na ') + h(oferta.loja) + '</span> <strong>' + (oferta.preco != null ? moeda(oferta.preco) + ' por unidade' : 'Preço a consultar') + '</strong></a>').join("") + '</div>' : '') + '</article>').join("");
  const rede = normalizarRede(build.rede);
  const extra = build.incluirRede && rede.tipo !== "indefinido" && rede.possuiAcessorio === false &&
    !itens.some(({categoria}) => categoria === (rede.tipo === "cabo" ? "cabo_rede" : "adaptador_wifi")) ? '<div class="benchmark-empty"><strong>Acessório de rede a incluir</strong><p>' + h(resumoRede(rede)) + (rede.comprimentoCaboM ? ' · ' + rede.comprimentoCaboM + ' m' : '') + '. Escolha um produto com as especificações necessárias na loja. Esse acessório ainda não tem oferta cadastrada.</p></div>' : '';
  return abrirDialogoBuild("Comprar build",'<p class="planning-help">' + h(build.titulo) + ' · escolha onde comprar cada peça. As quantidades não são enviadas automaticamente ao carrinho da loja. Os preços podem mudar na loja.</p>' + avisoFreteHtml() + avisoCompraHtml() + '<div class="build-purchase-list">' + linhas + '</div>' + extra);
}
