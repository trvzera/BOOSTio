import "../header.js";
import "../auth/auth.js";
import { carregarCatalogo, categorias, moeda, htmlSeguro as h, nomePeca, imagemPeca, ofertasPeca, destaquesFichaTecnica, gruposFichaTecnica, informacoesPreco } from "../build/catalogo.js";
import { abrirBuild, guardarRascunho } from "../build/estado.js";
import { selecionarPecaCompativel } from "../build/compatibilidade.js";
import { avisar, mostrarFalha } from "../build/interface.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";
import { navegarPara } from "../components/page-loading.js";
import { avisoCompraHtml, abrirCompraBuild } from "../build/acoes-build.js";
import { salvarAlteracaoLocal } from "../build/autosalvar.js";
import { carregarCatalogoConta, carregarBuildConta, salvarBuildConta } from "../build/conta.js";
import { ajudaCategorias } from "../build/uso-formulario.js";
import { cartoesOfertasHtml } from "../build/ofertas-peca.js";
import { obterHistoricoDaPeca } from "../build/carregar-historico-precos.js";
import { historicoPrecosHtml, iniciarHistoricoPrecos } from "../build/price-history.js";

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
    const destaques = destaquesFichaTecnica(peca);
    const gruposTecnicos = gruposFichaTecnica(peca);
    const preco = informacoesPreco(peca,conta);
    if (conta && ofertasPeca(peca).some(o => o.marketplace)) {
      preco.rotulo = "Preço de referência da peça";
      preco.nota += " As ofertas das lojas podem ter valores diferentes.";
    }
    let motivo = "";
    try { selecionarPecaCompativel(build,peca,catalogo); } catch (erro) { motivo = erro.message; }
    document.title = nomePeca(peca) + " — BOOSTio";
    const categoriaVoltar = ["air_cooler","water_cooler"].includes(peca.categoria) ? "cooler"
      : ["ssd","hd"].includes(peca.categoria) ? "armazenamento" : ["cabo_rede","adaptador_wifi"].includes(peca.categoria) ? "rede" : peca.categoria;
    main.innerHTML = '<header class="builder-heading"><a class="builder-back icon-back btn-ghost" data-page-back data-back-destination href="./pecas.html?' + new URLSearchParams({ categoria: categoriaVoltar, build: build.id }) +
      '" aria-label="Voltar ao catálogo de ' + categoria.nome + '" title="Voltar à categoria">' + iconeAnimado("arrow","back") + '</a></header>' +
      '<section class="product-detail-layout"><div class="product-detail-visual glass-card">' + imagemPeca(peca) + (peca.imagem ? "" : '<span class="font-2-xs summary-note">Imagem ainda não cadastrada</span>') + '</div>' +
      '<div class="product-detail-copy"><span class="component-category font-1-xs">' + categoria.nome + '</span><h1 class="font-1-xl">' + h(nomePeca(peca)) +
      '</h1>' + (ajudaCategorias[peca.categoria] ? '<p class="font-2-xs summary-note">' + h(ajudaCategorias[peca.categoria]) + '</p>' : '') + '<ul class="product-detail-highlights">' + destaques.map(([rotulo,valor]) => '<li class="font-2-xs"><span>' + h(rotulo) + '</span><strong>' + h(valor) + '</strong></li>').join("") +
      '</ul><span class="summary-eyebrow font-1-xs">' + h(preco.rotulo) + '</span><strong class="summary-total font-1-xl">' + h(preco.valor) + '</strong><p class="font-2-xs summary-note">' + h(preco.nota) + '</p>' +
      '<button type="button" id="add-product" class="btn-primary" aria-label="Adicionar à build: ' + h(nomePeca(peca)) + '" ' + (motivo ? 'disabled data-disabled-reason="' + h(motivo) + '"' : "") + '>' + iconeAnimado("plus") + 'Adicionar à build</button>' +
      '<p class="font-2-xs summary-note">' + h(motivo || "Não encontramos novos problemas com as peças escolhidas nas verificações disponíveis. Quando faltar informação, confira com o fabricante.") + '</p></div></section>' +
      '<section class="product-stores" aria-labelledby="stores-title"><h2 class="font-1-l" id="stores-title">Onde comprar</h2><p class="font-2-xs summary-note">Confira preço, estoque e o modelo exato na loja. As buscas não representam ofertas confirmadas.</p><div class="store-grid">' +
      cartoesOfertasHtml(peca) + '</div></section>' +
      historicoPrecosHtml(peca) +
      '<section class="product-specifications glass-card" aria-labelledby="spec-title"><h2 class="font-1-l" id="spec-title">Informações técnicas</h2>' +
      '<p class="font-2-xs summary-note product-specifications-note">Estas são as informações cadastradas deste modelo. Usamos esses dados para verificar sua montagem. Se uma informação estiver faltando, não podemos confirmar que as peças combinam nesse ponto. O consumo de energia é uma estimativa, não uma medição do computador ligado.</p>' +
      gruposTecnicos.map((grupo, indice) => '<section class="product-specification-group" aria-labelledby="spec-group-' + indice + '"><h3 class="font-1-m-b" id="spec-group-' + indice + '">' + h(grupo.titulo) + '</h3><dl>' +
        grupo.campos.map(([rotulo,valor]) => '<div><dt class="font-2-xs">' + h(rotulo) + '</dt><dd class="font-1-xs">' + h(valor) + '</dd></div>').join("") + '</dl></section>').join("") +
      '</section>';
    main.querySelector(".product-stores > p").insertAdjacentHTML("afterend",avisoCompraHtml());
    main.querySelectorAll(".store-logo").forEach(img => img.addEventListener("error",() => { img.hidden = true; img.nextElementSibling.hidden = false; },{once:true}));
    main.querySelectorAll('.store-card').forEach((card,indice)=>card.querySelectorAll('a').forEach(link=>link.addEventListener('click',evento=>{
      if (ofertasPeca(peca)[indice].marketplace) return;
      evento.preventDefault();
      try { abrirCompraBuild({...build,componentes:{[peca.categoria]:{id:peca.id,quantidade:1}}},catalogo,{loja:ofertasPeca(peca)[indice].codigo}); }
      catch(erro) { avisar(erro.message); }
    })));
    iniciarIcones(main);
    iniciarHistoricoPrecos(main, peca);
    if (conta) {
      const ofertasMercado = ofertasPeca(peca).filter(o => o.marketplace);
      let seletor = null, consultaHistorico = 0;
      if (ofertasMercado.length) {
        main.querySelector("[data-price-history]").insertAdjacentHTML("beforebegin", '<div class="planning-help planning-field"><label for="history-offer">Histórico por loja e vendedor</label><select id="history-offer" class="input-text"><option value="kabum">KaBuM!</option>' +
          ofertasMercado.map(o => '<option value="' + o.id + '" data-loja="' + h(o.codigo) + '">' + h(o.loja) + ' · ' + h(o.vendedor) + ' · anúncio ' + h(o.produto_id_loja) + '</option>').join("") + '</select></div>');
        seletor = main.querySelector("#history-offer");
      }
      const carregarHistorico = async () => {
        const consultaAtual = ++consultaHistorico;
        const ofertaId = seletor && seletor.value !== "kabum" ? Number(seletor.value) : null;
        const secao = main.querySelector("[data-price-history]");
        secao.querySelectorAll("[data-history-period]").forEach(botao => { botao.disabled = true; });
        const escolhida = ofertaId ? ofertasMercado.find(o => o.id === ofertaId) : null;
        secao.querySelector(".price-history-store").textContent = escolhida ? escolhida.loja : "KaBuM!";
        secao.querySelector("[data-history-content]").innerHTML = '<p role="status">Carregando histórico de preços…</p>';
        try {
          const dados = await obterHistoricoDaPeca(peca, {conta:true, ofertaId, lojaOferta:escolhida?.codigo});
          if (consultaAtual !== consultaHistorico) return;
          secao.outerHTML = historicoPrecosHtml({...peca, ...dados});
          iniciarHistoricoPrecos(main, {...peca, ...dados});
        } catch (erro) {
          if (consultaAtual !== consultaHistorico) return;
          secao.querySelector("[data-history-content]").innerHTML = '<p role="status">' + h(erro.message || "Não foi possível carregar o histórico.") + '</p><button type="button" class="btn-secondary" data-history-retry aria-label="Tentar carregar o histórico novamente">Tentar novamente</button>';
          secao.querySelector("[data-history-retry]").onclick = carregarHistorico;
        }
      };
      if (seletor) seletor.onchange = carregarHistorico;
      carregarHistorico();
    }
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
