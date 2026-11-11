import { ofertasPeca, moeda, htmlSeguro as h } from "./catalogo.js";

function botaoRemover(oferta, administrador) {
  const id = oferta.marketplace ? oferta.id : oferta.ofertaId;
  if (!administrador || !Number.isSafeInteger(id) || id <= 0 || oferta.preco == null) return "";
  return '<button type="button" class="btn-ghost" data-remover-oferta="' + id + '" aria-label="Remover a oferta da ' + h(oferta.loja) + ' do site">Remover oferta</button>';
}

export function cartoesOfertasHtml(peca, {administrador = false} = {}) {
  return ofertasPeca(peca).map(oferta => {
    const marca = oferta.logo ? '<img class="store-logo" src="' + h(oferta.logo) + '" alt="' + h(oferta.loja) + '"><span class="store-name font-1-m-b" hidden>' + h(oferta.loja) + '</span>'
      : '<span class="store-name font-1-m-b">' + h(oferta.loja) + '</span>';
    const descricao = oferta.marketplace ? (oferta.esgotado ? "Último registro: indisponível" : "Preço registrado · estoque não confirmado")
      : oferta.esgotado ? "Último preço cadastrado · produto indisponível" : oferta.preco != null ? "Preço cadastrado, sem frete · confirme na loja"
      : oferta.direta ? "Página do produto cadastrada" : "Busca pelo modelo · anúncio não cadastrado";
    const data = oferta.marketplace ? '<p class="font-2-xs">' + h(oferta.vendedor) + '</p><p class="font-2-xs">Consulta registrada em ' +
      h(new Intl.DateTimeFormat("pt-BR", {dateStyle:"short",timeStyle:"short"}).format(new Date(oferta.atualizadoEm))) + ' · sem frete</p>' : "";
    return '<article class="store-card glass-card"><a class="store-brand" href="' + h(oferta.url) + '" target="_blank" rel="noopener noreferrer" aria-label="Abrir ' + h(oferta.loja) + ' em uma nova aba">' + marca + '</a>' +
      (oferta.preco != null ? '<strong class="store-price">' + moeda(oferta.preco) + '</strong>' : '<span class="store-price-unavailable">Preço ainda não cadastrado</span>') +
      '<p class="font-2-xs">' + h(descricao) + '</p>' + data + '<a class="btn-ghost" href="' + h(oferta.url) + '" target="_blank" rel="noopener noreferrer" aria-label="' +
      h((oferta.direta ? "Conferir oferta na " : "Buscar na ") + oferta.loja + (oferta.vendedor ? " · " + oferta.vendedor : "")) + '">' +
      (oferta.direta ? "Conferir na loja" : "Buscar na loja") + '</a>' + botaoRemover(oferta, administrador) + '</article>';
  }).join("");
}
