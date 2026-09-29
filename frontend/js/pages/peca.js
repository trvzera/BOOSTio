import "../header.js";
import "../auth/auth.js";
import { carregarCatalogo, categorias, moeda, htmlSeguro as h, nomePeca, imagemPeca, ofertasPeca, fichaTecnica } from "../build/catalogo.js";
import { abrirBuild, guardarRascunho } from "../build/estado.js";
import { selecionarPecaCompativel } from "../build/compatibilidade.js";
import { avisar, mostrarFalha } from "../build/interface.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";

document.addEventListener("DOMContentLoaded", async () => {
  const main = document.querySelector("#product-main");
  try {
    const parametros = new URLSearchParams(location.search), catalogo = await carregarCatalogo();
    const peca = catalogo.find((p) => p.id === parametros.get("id"));
    if (!peca) throw new Error("Peça não encontrada no catálogo.");
    const categoria = categorias.find((c) => c.id === peca.categoria);
    let build = abrirBuild(new URLSearchParams({ id: parametros.get("build") || "" }));
    guardarRascunho(build);
    const detalhes = fichaTecnica(peca);
    let motivo = "";
    try { selecionarPecaCompativel(build,peca,catalogo); } catch (erro) { motivo = erro.message; }
    document.title = nomePeca(peca) + " — BOOSTio";
    const categoriaVoltar = ["air_cooler","water_cooler"].includes(peca.categoria) ? "cooler"
      : ["ssd","hd"].includes(peca.categoria) ? "armazenamento" : peca.categoria;
    main.innerHTML = '<header class="builder-heading"><a class="builder-back icon-back btn-ghost" data-page-back href="./pecas.html?' + new URLSearchParams({ categoria: categoriaVoltar, build: build.id }) +
      '" aria-label="Voltar ao catálogo de ' + categoria.nome + '" title="Voltar à categoria">' + iconeAnimado("arrow","back") + '</a></header>' +
      '<section class="product-detail-layout"><div class="product-detail-visual glass-card">' + imagemPeca(peca) + (peca.imagem ? "" : '<span class="font-2-xs summary-note">Imagem ainda não cadastrada</span>') + '</div>' +
      '<div class="product-detail-copy"><span class="component-category font-1-xs">' + categoria.nome + '</span><h1 class="font-1-xl">' + h(nomePeca(peca)) +
      '</h1><ul class="product-detail-highlights">' + detalhes.slice(3,7).map(([rotulo,valor]) => '<li class="font-2-xs"><span>' + h(rotulo) + '</span><strong>' + h(valor) + '</strong></li>').join("") +
      '</ul><span class="summary-eyebrow font-1-xs">Preço demonstrativo</span><strong class="summary-total font-1-xl">' + moeda(peca.preco) + '</strong>' +
      '<button type="button" id="add-product" class="btn-primary" ' + (motivo ? 'disabled data-disabled-reason="' + h(motivo) + '"' : "") + '>' + iconeAnimado("plus") + 'Adicionar à build</button>' +
      '<p class="font-2-xs summary-note">' + h(motivo || "Sem novos conflitos detectados nas verificações disponíveis. Confirme os dados no fabricante.") + '</p></div></section>' +
      '<section class="product-stores" aria-labelledby="stores-title"><h2 class="font-1-l" id="stores-title">Onde comprar</h2><p class="font-2-xs summary-note">Confira preço, estoque e o modelo exato na loja. As buscas não representam ofertas confirmadas.</p><div class="store-grid">' +
      ofertasPeca(peca).map((oferta) => '<article class="store-card glass-card"><a class="store-brand" href="' + h(oferta.url) + '" target="_blank" rel="noopener noreferrer"><img class="store-logo" src="' + h(oferta.logo) +
      '" alt="' + oferta.loja + '"><span class="store-name font-1-m-b" hidden>' + oferta.loja + '</span></a>' +
      (oferta.preco != null ? '<strong class="store-price">' + moeda(oferta.preco) + '</strong>' : '<span class="store-price-unavailable">Preço ainda não cadastrado</span>') +
      '<p class="font-2-xs">' +
      (oferta.direta ? "Página do produto cadastrada" : "Busca pelo modelo · anúncio não cadastrado") + '</p><a class="btn-ghost" href="' + h(oferta.url) +
      '" target="_blank" rel="noopener noreferrer">' + iconeAnimado("cart") + (oferta.direta ? "Comprar na loja" : "Buscar na loja") + '</a></article>').join("") + '</div></section>' +
      '<section class="product-specifications glass-card" aria-labelledby="spec-title"><h2 class="font-1-l" id="spec-title">Informações técnicas</h2><dl>' +
      detalhes.map(([rotulo,valor]) => '<div><dt class="font-2-xs">' + h(rotulo) + '</dt><dd class="font-1-xs">' + h(valor) + '</dd></div>').join("") +
      '</dl></section>';
    main.querySelectorAll(".store-logo").forEach(img => img.addEventListener("error",() => { img.hidden = true; img.nextElementSibling.hidden = false; },{once:true}));
    iniciarIcones(main);
    main.querySelector("#add-product").onclick = () => {
      try {
        build = selecionarPecaCompativel(build, peca, catalogo);
        guardarRascunho(build);
        location.href = "./configuracao-build.html?id=" + encodeURIComponent(build.id);
      } catch (erro) { avisar(erro.message); }
    };
  } catch (erro) { mostrarFalha(main, erro); }
});
