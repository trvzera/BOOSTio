import { htmlSeguro as h, moeda, nomePeca, ofertasPeca } from "./catalogo.js";
import { itensSelecionados, itensCategoria, informacoesRam } from "./estado.js";
import { avaliarBuild } from "./compatibilidade.js";
import { normalizarRede, resumoRede } from "./rede.js";
import { iniciarIcones } from "../components/ui.js";

export function avisoCompraHtml() {
  return '<p class="purchase-notice">A BOOSTio não vende, entrega ou processa pagamentos de peças e periféricos. Os links abrem lojas de terceiros, responsáveis pela venda e pelo atendimento da compra. Confira preço, estoque, frete, garantia e devolução diretamente na loja.</p>';
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
  if (avaliacao.preenchidos !== avaliacao.total) return "Complete 100% das peças da build para testar o desempenho.";
  if (avaliacao.erros.length) return "Resolva os erros de compatibilidade antes de testar o desempenho.";
  return "";
}
export function abrirBenchmark(build,catalogo) {
  const motivo = motivoBenchmark(build,catalogo);
  if (motivo) throw new Error(motivo);
  const peca = categoria => catalogo.find(p => p.id === itensCategoria(build,categoria)[0]?.id);
  const cpu = peca("processador"), gpu = peca("placa_video"), ram = informacoesRam(build,catalogo);
  return abrirDialogoBuild("Testar build",'<p class="planning-help">' + h(build.titulo) + '</p>' +
    '<dl class="benchmark-specs"><div><dt>Processador</dt><dd>' + h(nomePeca(cpu)) + '</dd></div>' +
    '<div><dt>Placa de vídeo</dt><dd>' + h(gpu ? nomePeca(gpu) : cpu?.modelo_videointegrado || "Vídeo integrado · modelo a confirmar") + '</dd></div>' +
    '<div><dt>Memória</dt><dd>' + ram.capacidade + ' GB</dd></div></dl>' +
    '<div class="planning-grid"><label class="planning-field" for="benchmark-resolution"><span>Resolução</span><select id="benchmark-resolution"><option>1080p</option><option>1440p</option><option>4K</option></select></label>' +
    '<label class="planning-field" for="benchmark-preset"><span>Qualidade gráfica</span><select id="benchmark-preset"><option value="low">Baixa</option><option value="medium" selected>Média</option><option value="high">Alta</option><option value="ultra">Ultra</option></select></label></div>' +
    '<div class="benchmark-empty" role="status"><strong>Estimativas de FPS em breve</strong><p>O serviço de desempenho ainda não está disponível. Quando estiver integrado, você poderá consultar os jogos suportados com estas configurações.</p></div>' +
    '<button type="button" class="btn-primary" disabled data-disabled-reason="A integração com o serviço de benchmark ainda está em andamento." aria-label="Consultar FPS estimado">Consultar FPS estimado</button>' +
    '<p class="planning-help">O FPS será uma estimativa da combinação entre processador e GPU, não uma medição da sua máquina. RAM, drivers, temperatura, resolução e configurações do jogo podem alterar o desempenho real.</p>');
}
export function abrirCompraBuild(build,catalogo) {
  const itens = itensSelecionados(build,catalogo);
  if (!itens.length) throw new Error("Adicione pelo menos uma peça à build para consultar lojas.");
  const linhas = itens.map(({item,peca}) => '<article class="build-purchase-item"><h3 class="font-1-m-b">' + h(peca ? nomePeca(peca) : item.proprio || "Modelo não encontrado") + '</h3><p class="planning-help">Quantidade: ' + item.quantidade + (peca ? ' · referência demonstrativa: ' + moeda(Number(peca.preco || 0) * item.quantidade) : ' · peça própria, sem compra indicada') + '</p>' +
    (peca ? '<div class="build-store-links">' + ofertasPeca(peca).map(oferta => '<a class="build-store-link" href="' + h(oferta.url) + '" target="_blank" rel="noopener noreferrer" aria-label="' + (oferta.direta ? 'Comprar na ' : 'Buscar na ') + h(oferta.loja) + ' ' + h(oferta.preco != null ? moeda(oferta.preco) + ' por unidade' : 'Preço a consultar') + ': ' + h(nomePeca(peca)) + '"><img src="' + h(oferta.logo) + '" alt="' + h(oferta.loja) + '"><span>' + (oferta.direta ? 'Comprar na ' : 'Buscar na ') + h(oferta.loja) + '</span> <strong>' + (oferta.preco != null ? moeda(oferta.preco) + ' por unidade' : 'Preço a consultar') + '</strong></a>').join("") + '</div>' : '') + '</article>').join("");
  const rede = normalizarRede(build.rede);
  const extra = build.incluirRede && rede.tipo !== "indefinido" && rede.possuiAcessorio === false &&
    !itens.some(({categoria}) => categoria === (rede.tipo === "cabo" ? "cabo_rede" : "adaptador_wifi")) ? '<div class="benchmark-empty"><strong>Acessório de rede a incluir</strong><p>' + h(resumoRede(rede)) + (rede.comprimentoCaboM ? ' · ' + rede.comprimentoCaboM + ' m' : '') + '. Escolha um produto com as especificações necessárias na loja. Esse acessório ainda não tem oferta cadastrada.</p></div>' : '';
  return abrirDialogoBuild("Comprar build",'<p class="planning-help">' + h(build.titulo) + ' · escolha onde comprar cada peça. As quantidades não são enviadas automaticamente ao carrinho da loja. Preços demonstrativos não são ofertas confirmadas.</p>' + avisoCompraHtml() + '<div class="build-purchase-list">' + linhas + '</div>' + extra);
}
