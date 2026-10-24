import "../header.js";
import "../auth/auth.js";
import { carregarCatalogo, categorias, moeda, htmlSeguro as h, nomePeca, imagemPeca, ofertasPeca, fichaTecnica, informacoesPreco } from "../build/catalogo.js";
import { abrirBuild, guardarRascunho } from "../build/estado.js";
import { selecionarPecaCompativel } from "../build/compatibilidade.js";
import { avisar, mostrarFalha } from "../build/interface.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";
import { navegarPara } from "../components/page-loading.js";
import { avisoCompraHtml, abrirCompraBuild } from "../build/acoes-build.js";
import { salvarAlteracaoLocal } from "../build/autosalvar.js";
import { carregarCatalogoConta, carregarBuildConta, salvarBuildConta } from "../build/conta.js";

document.addEventListener("DOMContentLoaded", async () => {
  const main = document.querySelector("#product-main");
  try {
    const parametros = new URLSearchParams(location.search);
    const conta = parametros.get("build")?.startsWith("s-");
    const catalogo = conta ? await carregarCatalogoConta() : await carregarCatalogo();
    const peca = catalogo.find((p) => p.id === parametros.get("id"));
    if (!peca) throw new Error("Peça não encontrada no catálogo.");
    const categoria = categorias.find((c) => c.id === peca.categoria);
    let build = conta ? await carregarBuildConta(parametros.get("build")) : abrirBuild(new URLSearchParams({ id: parametros.get("build") || "" }));
    if (!conta) guardarRascunho(build);
    const detalhes = fichaTecnica(peca);
    const preco = informacoesPreco(peca,conta);
    let motivo = "";
    try { selecionarPecaCompativel(build,peca,catalogo); } catch (erro) { motivo = erro.message; }
    document.title = nomePeca(peca) + " — BOOSTio";
    const categoriaVoltar = ["air_cooler","water_cooler"].includes(peca.categoria) ? "cooler"
      : ["ssd","hd"].includes(peca.categoria) ? "armazenamento" : ["cabo_rede","adaptador_wifi"].includes(peca.categoria) ? "rede" : peca.categoria;
    main.innerHTML = '<header class="builder-heading"><a class="builder-back icon-back btn-ghost" data-page-back data-back-destination href="./pecas.html?' + new URLSearchParams({ categoria: categoriaVoltar, build: build.id }) +
      '" aria-label="Voltar ao catálogo de ' + categoria.nome + '" title="Voltar à categoria">' + iconeAnimado("arrow","back") + '</a></header>' +
      '<section class="product-detail-layout"><div class="product-detail-visual glass-card">' + imagemPeca(peca) + (peca.imagem ? "" : '<span class="font-2-xs summary-note">Imagem ainda não cadastrada</span>') + '</div>' +
      '<div class="product-detail-copy"><span class="component-category font-1-xs">' + categoria.nome + '</span><h1 class="font-1-xl">' + h(nomePeca(peca)) +
      '</h1><ul class="product-detail-highlights">' + detalhes.slice(3,7).map(([rotulo,valor]) => '<li class="font-2-xs"><span>' + h(rotulo) + '</span><strong>' + h(valor) + '</strong></li>').join("") +
      '</ul><span class="summary-eyebrow font-1-xs">' + h(preco.rotulo) + '</span><strong class="summary-total font-1-xl">' + h(preco.valor) + '</strong><p class="font-2-xs summary-note">' + h(preco.nota) + '</p>' +
      '<button type="button" id="add-product" class="btn-primary" aria-label="Adicionar à build: ' + h(nomePeca(peca)) + '" ' + (motivo ? 'disabled data-disabled-reason="' + h(motivo) + '"' : "") + '>' + iconeAnimado("plus") + 'Adicionar à build</button>' +
      '<p class="font-2-xs summary-note">' + h(motivo || "Sem novos conflitos detectados nas verificações disponíveis. Confirme os dados no fabricante.") + '</p></div></section>' +
      '<section class="product-stores" aria-labelledby="stores-title"><h2 class="font-1-l" id="stores-title">Onde comprar</h2><p class="font-2-xs summary-note">Confira preço, estoque e o modelo exato na loja. As buscas não representam ofertas confirmadas.</p><div class="store-grid">' +
      ofertasPeca(peca).map((oferta) => '<article class="store-card glass-card"><a class="store-brand" href="' + h(oferta.url) + '" target="_blank" rel="noopener noreferrer" aria-label="Abrir ' + h(oferta.loja) + ' em uma nova aba"><img class="store-logo" src="' + h(oferta.logo) +
      '" alt="' + oferta.loja + '"><span class="store-name font-1-m-b" hidden>' + oferta.loja + '</span></a>' +
      (oferta.preco != null ? '<strong class="store-price">' + moeda(oferta.preco) + '</strong>' : '<span class="store-price-unavailable">Preço ainda não cadastrado</span>') +
      '<p class="font-2-xs">' +
      (oferta.esgotado ? "Último preço cadastrado · produto indisponível" : oferta.preco != null ? "Preço cadastrado, sem frete · confirme na loja" : oferta.direta ? "Página do produto cadastrada" : "Busca pelo modelo · anúncio não cadastrado") + '</p><a class="btn-ghost" href="' + h(oferta.url) +
      '" target="_blank" rel="noopener noreferrer" aria-label="' + (oferta.direta ? "Comprar na loja" : "Buscar na loja") + ' ' + h(oferta.loja) + ' em uma nova aba">' + iconeAnimado("cart") + (oferta.direta ? "Comprar na loja" : "Buscar na loja") + '</a></article>').join("") + '</div></section>' +
      '<section class="product-specifications glass-card" aria-labelledby="spec-title"><h2 class="font-1-l" id="spec-title">Informações técnicas</h2><dl>' +
      detalhes.map(([rotulo,valor]) => '<div><dt class="font-2-xs">' + h(rotulo) + '</dt><dd class="font-1-xs">' + h(valor) + '</dd></div>').join("") +
      '</dl></section>';
    main.querySelector(".product-stores > p").insertAdjacentHTML("afterend",avisoCompraHtml());
    main.querySelectorAll(".store-logo").forEach(img => img.addEventListener("error",() => { img.hidden = true; img.nextElementSibling.hidden = false; },{once:true}));
    main.querySelectorAll('.store-card').forEach((card,indice)=>card.querySelectorAll('a').forEach(link=>link.addEventListener('click',evento=>{
      evento.preventDefault();
      try { abrirCompraBuild({...build,componentes:{[peca.categoria]:{id:peca.id,quantidade:1}}},catalogo,{loja:ofertasPeca(peca)[indice].codigo}); }
      catch(erro) { avisar(erro.message); }
    })));
    iniciarIcones(main);
    main.querySelector("#add-product").onclick = async () => {
      try {
        build = selecionarPecaCompativel(build, peca, catalogo);
        if (conta) await salvarBuildConta(build);
        else {
          const salvo = salvarAlteracaoLocal(build,catalogo);
          if (!salvo.salvo) { avisar(salvo.motivo); return; }
        }
        navegarPara("./configuracao-build.html?" + new URLSearchParams({[conta ? "build_id" : "id"]:build.id}));
      } catch (erro) { avisar(erro.message); }
    };
  } catch (erro) { mostrarFalha(main, erro); }
});
