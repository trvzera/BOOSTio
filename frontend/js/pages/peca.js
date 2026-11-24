import "../header.js";
import "../auth/auth.js";
import { carregarCatalogo, categorias, htmlSeguro as h, nomePeca, imagemPeca, ofertasPeca, gruposFichaTecnica, informacoesPreco } from "../build/catalogo.js";
import { abrirBuild, guardarRascunho, itensCategoria, categoriasMultiplas } from "../build/estado.js";
import { selecionarPecaCompativel } from "../build/compatibilidade.js";
import { avisar, mostrarFalha } from "../build/interface.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";
import { navegarPara } from "../components/page-loading.js";
import { avisoCompraHtml } from "../build/acoes-build.js";
import { salvarAlteracaoLocal } from "../build/autosalvar.js";
import { carregarCatalogoConta, carregarBuildConta, salvarBuildConta } from "../build/conta.js";
import { ajudaCategorias } from "../build/uso-formulario.js";
import { cartoesOfertasHtml } from "../build/ofertas-peca.js";
import { carregarPerfil } from "../conta/perfil.js";
import { removerOferta } from "../api/admin/ofertas.js";
import { obterHistoricoDaPeca } from "../build/carregar-historico-precos.js";
import { historicoPrecosHtml, iniciarHistoricoPrecos, nomesLojas } from "../build/price-history.js";

document.addEventListener("DOMContentLoaded", async () => {
  const main = document.querySelector("#product-main");
  try {
    const parametros = new URLSearchParams(location.search);
    const conta = parametros.get("build")?.startsWith("s-");
    const catalogo = conta ? await carregarCatalogoConta({cache:"no-store"}) : await carregarCatalogo();
    const peca = catalogo.find((p) => p.id === parametros.get("id"));
    if (!peca) throw new Error("Peça não encontrada no catálogo.");
    const categoria = categorias.find((c) => c.id === peca.categoria);
    let build = conta ? await carregarBuildConta(parametros.get("build")) : abrirBuild(new URLSearchParams({ id: parametros.get("build") || "" }));
    if (!conta) guardarRascunho(build);
    const administrador = Boolean((await carregarPerfil().catch(() => null))?.usuario?.administrador);
    const gruposTecnicos = gruposFichaTecnica(peca);
    const preco = informacoesPreco(peca,conta);
    if (conta && ofertasPeca(peca).some(o => o.marketplace)) {
      preco.rotulo = "Preço de referência da peça";
      preco.nota += " As ofertas das lojas podem ter valores diferentes.";
    }
    document.title = nomePeca(peca) + " — BOOSTio";
    const categoriaVoltar = ["air_cooler","water_cooler"].includes(peca.categoria) ? "cooler"
      : ["ssd","hd"].includes(peca.categoria) ? "armazenamento" : ["cabo_rede","adaptador_wifi"].includes(peca.categoria) ? "rede" : peca.categoria;
    const buildUrl = "./configuracao-build.html?" + new URLSearchParams({[conta ? "build_id" : "id"]:build.id});
    const naBuild = itensCategoria(build,peca.categoria).some(item => item.id === peca.id);
    const voltar = naBuild ? buildUrl : "./pecas.html?" + new URLSearchParams({categoria:categoriaVoltar,build:build.id});
    const rotuloVoltar = naBuild ? "Voltar à build" : "Voltar ao catálogo";
    const podeAdicionar = !naBuild || categoriasMultiplas.has(peca.categoria);
    let motivo = "";
    if (podeAdicionar) {
      try { selecionarPecaCompativel(build,peca,catalogo); } catch (erro) { motivo = erro.message; }
    }
    const adicionar = naBuild ? "Adicionar mais" : "Adicionar à build";
    const titulo = h(nomePeca(peca));
    main.innerHTML = `
      <header class="product-detail-heading">
        <a class="builder-back font-1-xs" data-page-back data-back-destination href="${h(voltar)}" aria-label="${rotuloVoltar}">
          ${iconeAnimado("arrow","back")}<span data-back-label>${rotuloVoltar}</span>
        </a>
        <span class="component-category font-1-xs">${h(categoria.nome)}</span>
        <h1 class="font-1-xl">${titulo}</h1>
      </header>
      <div class="product-detail-layout">
        <div class="product-detail-media">
          <div class="product-detail-visual glass-card">${imagemPeca(peca)}${peca.imagem ? "" : '<span class="font-2-xs summary-note">Imagem ainda não cadastrada</span>'}</div>
          ${podeAdicionar ? `<div class="product-detail-selection">
            ${ajudaCategorias[peca.categoria] ? '<p class="font-2-xs summary-note">' + h(ajudaCategorias[peca.categoria]) + '</p>' : ""}
            <button type="button" id="add-product" class="btn-primary" aria-label="${adicionar} ${titulo}" ${motivo ? 'disabled data-disabled-reason="' + h(motivo) + '"' : ""}>${iconeAnimado("plus")}${adicionar}</button>
            ${motivo ? '<p class="font-2-xs summary-note">' + h(motivo) + '</p>' : ""}
          </div>` : ""}
        </div>
        <section class="product-stores" aria-labelledby="stores-title">
          <h2 class="font-1-l" id="stores-title">Onde comprar</h2>
          <p class="font-2-xs summary-note">Confira preço, estoque, frete e o modelo exato na loja.</p>
          <div class="store-grid">${cartoesOfertasHtml(peca,{administrador})}</div>
          <p class="planning-help product-reference-price"><strong>${h(preco.rotulo)} · ${h(preco.valor)}</strong> ${h(preco.nota)}</p>
          <details class="purchase-information"><summary class="font-2-xs">Sobre a compra nas lojas</summary>${avisoCompraHtml()}</details>
        </section>
        <section class="product-specifications glass-card" aria-labelledby="spec-title">
          <h2 class="font-1-l" id="spec-title">Especificações técnicas</h2>
          ${gruposTecnicos.map((grupo, indice) => '<section class="product-specification-group" aria-labelledby="spec-group-' + indice + '"><h3 class="font-1-xs" id="spec-group-' + indice + '">' + h(grupo.titulo) + '</h3><dl>' +
            grupo.campos.map(([rotulo,valor]) => '<div><dt class="font-2-xs">' + h(rotulo) + '</dt><dd class="font-1-xs">' + h(valor) + '</dd></div>').join("") + '</dl></section>').join("")}
          <p class="planning-help product-specifications-note">Se algum dado estiver ausente, consulte o fabricante. O consumo informado é uma estimativa.</p>
        </section>
        <div class="product-detail-history">${historicoPrecosHtml(peca)}</div>
      </div>`;
    main.querySelectorAll(".store-logo").forEach(img => img.addEventListener("error",() => { img.hidden = true; img.nextElementSibling.hidden = false; },{once:true}));
    main.querySelectorAll("[data-remover-oferta]").forEach(botao => botao.addEventListener("click", async () => {
      if (!confirm("Remover esta oferta do site? Ela deixa de aparecer, de contar no preço e de ser atualizada.")) return;
      botao.disabled = true;
      try {
        await removerOferta(botao.dataset.removerOferta);
        botao.closest(".store-card").remove();
        avisar("Oferta removida. O preço de referência é atualizado em até 1 minuto.");
      } catch (erro) { botao.disabled = false; avisar(erro.message || "Não foi possível remover a oferta."); }
    }));
    iniciarIcones(main);
    iniciarHistoricoPrecos(main, peca);
    if (conta) {
      let seletor = null, consultaHistorico = 0;
      const lojasHistorico = ["kabum", "mercado_livre", "shopee", "gigantec"].filter(l => (peca.ofertas || []).some(o => o.loja === l));
      if (lojasHistorico.length) {
        main.querySelector("[data-price-history]").insertAdjacentHTML("beforebegin", '<div class="planning-help planning-field"><label for="history-offer">Histórico por loja</label><select id="history-offer" class="input-text"><option value="todas">' + h(nomesLojas.todas) + '</option>' +
          lojasHistorico.map(l => '<option value="' + l + '">' + h(nomesLojas[l]) + '</option>').join("") + '</select></div>');
        seletor = main.querySelector("#history-offer");
      }
      const carregarHistorico = async () => {
        const consultaAtual = ++consultaHistorico;
        const loja = seletor ? seletor.value : "todas";
        const secao = main.querySelector("[data-price-history]");
        secao.querySelectorAll("[data-history-period]").forEach(botao => { botao.disabled = true; });
        secao.querySelector(".price-history-store").textContent = nomesLojas[loja];
        secao.querySelector("[data-history-content]").innerHTML = '<p role="status">Carregando histórico de preços…</p>';
        try {
          const dados = await obterHistoricoDaPeca(peca, {conta:true, loja});
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
    main.querySelector("#add-product")?.addEventListener("click", async () => {
      try {
        build = selecionarPecaCompativel(build, peca, catalogo);
        if (conta) await salvarBuildConta(build);
        else {
          const salvo = salvarAlteracaoLocal(build,catalogo);
          if (!salvo.salvo) { avisar(salvo.motivo); return; }
        }
        navegarPara(buildUrl);
      } catch (erro) { avisar(erro.message); }
    });
  } catch (erro) { mostrarFalha(main, erro); }
});
