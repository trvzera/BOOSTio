import "../header.js";
import "../auth/auth.js";
import { carregarCatalogo, categoriaCatalogo, moeda, htmlSeguro as h, nomePeca, imagemPeca, fichaTecnica } from "../build/catalogo.js";
import { abrirBuild, guardarRascunho, motivoSelecao, itensRam } from "../build/estado.js";
import { pecaCompativel, selecionarPecaCompativel } from "../build/compatibilidade.js";
import { avisar, mostrarFalha } from "../build/interface.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";

document.addEventListener("DOMContentLoaded", async () => {
  const main = document.querySelector("#catalog-main");
  try {
    const parametros = new URLSearchParams(location.search);
    const categoria = categoriaCatalogo(parametros.get("categoria") || "processador");
    if (!categoria) throw new Error("Categoria não encontrada.");
    const catalogo = await carregarCatalogo();
    let build = abrirBuild(new URLSearchParams({ id: parametros.get("build") || "" }));
    guardarRascunho(build);
    let pagina = 1;
    const tamanhoPagina = 12;
    const temPecas = Object.keys(build.componentes).length > 0;
    const produtos = catalogo.filter((p) => (categoria.tipos || [categoria.id]).includes(p.categoria));
    main.innerHTML = '<header class="builder-heading"><div><a class="builder-back font-1-xs" data-page-back href="./configuracao-build.html?id=' + encodeURIComponent(build.id) + '">' + iconeAnimado("arrow","back") + '<span data-back-label>Voltar à build</span></a><h1 class="font-1-xl">' + categoria.nome +
      '</h1><p class="font-2-s">Compare os modelos e selecione a peça para sua configuração.</p></div><span class="builder-demo font-1-xs">Catálogo demonstrativo</span></header>' +
      '<div class="catalog-toolbar glass-card"><label class="catalog-search font-1-xs">Buscar modelo<input class="input-text" id="component-search" type="search" placeholder="Marca ou modelo"></label>' +
      '<label class="font-1-xs">Marca<select id="brand-filter" class="input-text"><option value="">Todas</option>' + [...new Set(produtos.map((p) => p.fabricante))].sort().map((marca) => '<option>' + h(marca) + '</option>').join("") + '</select></label>' +
      '<label class="font-1-xs">Ordenar<select id="component-sort" class="input-text"><option value="preco-asc">Menor preço</option><option value="preco-desc">Maior preço</option><option value="nome">Nome</option></select></label>' +
      '</div><p class="catalog-context">' + (temPecas ? 'Mostrando apenas opções sem conflitos detectados com sua build. Modelos não identificados precisam de conferência.' : 'Selecione a primeira peça; as próximas categorias serão filtradas automaticamente.') + '</p>' +
      '<p id="catalog-count" class="font-2-xs summary-note" role="status"></p><section id="catalog-results" class="catalog-grid" aria-label="Peças da categoria"></section><nav class="catalog-pagination" aria-label="Páginas do catálogo"><button type="button" id="previous-products" class="btn-ghost">Anterior</button><span id="catalog-page" class="font-2-xs"></span><button type="button" id="next-products" class="btn-ghost">Próxima</button></nav>';
    const campoBusca = main.querySelector("#component-search");
    const marca = main.querySelector("#brand-filter"), ordem = main.querySelector("#component-sort");
    let filtrados = [];
    const normal = (v) => v.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    function renderizar() {
      filtrados = produtos.filter((p) => normal(nomePeca(p)).includes(normal(campoBusca.value)) &&
        !p.esgotado && (!marca.value || p.fabricante === marca.value) && (!temPecas || pecaCompativel(build,p,catalogo)));
      filtrados.sort((a,b) => ordem.value === "nome" ? nomePeca(a).localeCompare(nomePeca(b))
        : ordem.value === "preco-desc" ? b.preco-a.preco : a.preco-b.preco);
      const paginas = Math.max(1, Math.ceil(filtrados.length / tamanhoPagina));
      pagina = Math.min(pagina, paginas);
      main.querySelector("#catalog-count").textContent = filtrados.length + " opções encontradas · preços demonstrativos, sem atualização em tempo real.";
      main.querySelector("#catalog-results").innerHTML = filtrados.slice((pagina-1)*tamanhoPagina, pagina*tamanhoPagina).map((peca) => {
        const detalhes = "./peca.html?" + new URLSearchParams({ id: peca.id, build: build.id });
        const selecionada = peca.categoria === "memoria_ram" ? itensRam(build).some(r => r.id === peca.id) : build.componentes[peca.categoria]?.id === peca.id;
        const motivo = motivoSelecao(build,peca,catalogo);
        return '<article class="product-card glass-card"><a class="product-visual" href="' + detalhes + '" aria-label="Ver detalhes de ' + h(nomePeca(peca)) + '">' + imagemPeca(peca) +
          '</a><div class="product-card-body"><span class="component-category font-1-xs">' + h(peca.fabricante) + '</span><h2 class="font-1-m-b"><a href="' + detalhes + '">' + h(peca.modelo) +
          '</a></h2><ul class="product-highlights">' + fichaTecnica(peca).slice(3,6).map(([rotulo,valor]) => '<li class="font-2-xs">' + h(rotulo) + ': ' + h(valor) + '</li>').join("") +
          '</ul><strong class="product-price font-1-l">' + moeda(peca.preco) + '</strong><div class="product-actions"><a class="btn-ghost" href="' + detalhes +
          '">Detalhes</a><button type="button" class="btn-primary" data-add="' + peca.id + '" ' + (motivo ? 'disabled data-disabled-reason="' + h(motivo) + '"' : "") + '>' +
          iconeAnimado("plus") + (selecionada && peca.categoria === "memoria_ram" ? "Adicionar mais" : "Adicionar") + '</button></div></div></article>';
      }).join("") || '<div class="catalog-empty glass-card"><p class="font-2-s">' + (build.travada ? 'Build trancada: destranque-a antes de escolher componentes.' : 'Nenhuma opção está disponível com estes filtros e a configuração atual. Para trocar uma peça já selecionada, remova-a primeiro no editor.') + '</p></div>';
      iniciarIcones(main);
      main.querySelector("#catalog-page").textContent = pagina + " / " + paginas;
      main.querySelector("#previous-products").disabled = pagina <= 1;
      main.querySelector("#next-products").disabled = pagina >= paginas;
    }
    [campoBusca, marca, ordem].forEach((campo) => campo.addEventListener(campo === campoBusca ? "input" : "change", () => { pagina=1; renderizar(); }));
    main.querySelector("#previous-products").onclick = () => { pagina--; renderizar(); };
    main.querySelector("#next-products").onclick = () => { pagina++; renderizar(); };
    main.querySelector("#catalog-results").addEventListener("click", (event) => {
      const botao = event.target.closest("[data-add]");
      if (!botao || botao.disabled) return;
      try {
        build = selecionarPecaCompativel(build, catalogo.find((p) => p.id === botao.dataset.add), catalogo);
        guardarRascunho(build);
        location.href = "./configuracao-build.html?id=" + encodeURIComponent(build.id);
      } catch (erro) { avisar(erro.message); }
    });
    renderizar();
  } catch (erro) { mostrarFalha(main, erro); }
});
