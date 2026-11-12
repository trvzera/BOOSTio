import { ofertasPeca, moeda, htmlSeguro as h } from "./catalogo.js";

export function cartoesOfertasHtml(peca,{loja,somenteDisponiveis=false,referenciaIndisponivel=false}={}) {
  return ofertasPeca(peca).filter(oferta => (!loja || oferta.codigo === loja)
    && (!somenteDisponiveis || !oferta.esgotado)
    && (!referenciaIndisponivel || oferta.marketplace)).map(oferta => {
    const marca = oferta.logo ? '<img class="store-logo" src="' + h(oferta.logo) + '" alt="" aria-hidden="true"><span class="store-name font-1-m-b">' + h(oferta.loja) + '</span>'
      : '<span class="store-name font-1-m-b">' + h(oferta.loja) + '</span>';
    const descricao = oferta.marketplace ? (oferta.esgotado ? "Último registro: indisponível" : "Preço registrado · estoque não confirmado; confirme estoque e frete na loja")
      : oferta.esgotado ? "Último preço cadastrado · produto indisponível" : oferta.preco != null ? "Preço cadastrado, sem frete · confirme na loja"
      : oferta.direta ? "Página do produto cadastrada" : "Busca pelo modelo · anúncio não cadastrado";
    const data = oferta.marketplace ? '<p class="font-2-xs">' + h(oferta.vendedor) + '</p><p class="font-2-xs">Consulta registrada em ' +
      h(new Intl.DateTimeFormat("pt-BR", {dateStyle:"short",timeStyle:"short"}).format(new Date(oferta.atualizadoEm))) + ' · sem frete</p>' : "";
    return '<article class="store-card glass-card"><div class="store-brand">' + marca + '</div><span class="store-offer-kind">' + (oferta.esgotado ? 'Indisponível' : oferta.direta ? 'Oferta cadastrada' : 'Busca pelo modelo') + '</span>' +
      (oferta.preco != null ? '<strong class="store-price">' + moeda(oferta.preco) + '</strong>' : '<span class="store-price-unavailable">Preço ainda não cadastrado</span>') +
      '<p class="font-2-xs">' + h(descricao) + '</p>' + data + '<a class="btn-ghost" href="' + h(oferta.url) + '" target="_blank" rel="noopener noreferrer" aria-label="' +
      h((oferta.direta ? "Conferir oferta na " : "Buscar na ") + oferta.loja + (oferta.vendedor ? " · " + oferta.vendedor : "")) + '">' +
      (oferta.direta ? "Conferir na loja" : "Buscar na loja") + '<span aria-hidden="true">↗</span></a></article>';
  }).join("");
}
