import { carregarCatalogo, gruposFichaTecnica, htmlSeguro as h, imagemPeca, nomePeca } from "../build/catalogo.js";
import { cartoesOfertasHtml } from "../build/ofertas-peca.js";
import { historicoPrecosHtml, iniciarHistoricoPrecos } from "../build/price-history.js";
import { iniciarImagens } from "../build/imagens-produtos.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";

document.addEventListener("DOMContentLoaded", async () => {
  const raiz = document.querySelector("#test-price-history-preview");
  if (!raiz) return;

  const build = raiz.querySelector(".test-product-build");
  const detalhe = raiz.querySelector("#teste-peca-detalhes");
  const carregando = raiz.querySelector("[data-test-product-loading]");
  const hrefDetalhe = "#" + detalhe.id;
  const agora = Date.now();
  const preco = 699.90;
  let peca;
  try {
    const catalogo = await carregarCatalogo();
    const original = catalogo.find(item => item.id === "SEED-CPU-02");
    if (!original) throw new Error("Peça de exemplo ausente.");
    peca = {
      ...original,
      ofertas: [{loja:"kabum", preco}],
      historico_precos: [
        [120, 899.90], [100, 849.90], [85, 879.90], [65, 799.90],
        [45, 829.90], [28, 749.90], [14, 779.90], [7, 729.90], [0, preco],
      ].map(([diasAtras, preco]) => ({
        data: new Date(agora - diasAtras * 86400000).toISOString().slice(0, 10),
        preco,
        loja: "kabum",
      })),
    };
  } catch {
    carregando.textContent = "Não foi possível carregar a peça de exemplo. Recarregue a página para tentar novamente.";
    return;
  }

  const nome = h(nomePeca(peca));
  carregando.hidden = true;
  build.querySelector("[data-test-product-component]").innerHTML = `
    <article class="test-product-build-component">
      <div class="test-product-build-image">${imagemPeca(peca)}</div>
      <div><span class="component-category font-1-xs">Processador</span><h4 class="font-1-m-b">${nome}</h4></div>
      <div class="test-product-build-actions">
        <a class="btn-secondary" href="${hrefDetalhe}" aria-label="Ver peça ${nome}">Ver peça</a>
        <a class="btn-primary" href="${hrefDetalhe}" aria-label="Comprar ${nome}">${iconeAnimado("cart")}Comprar</a>
      </div>
    </article>`;

  detalhe.innerHTML = `
    <header class="product-detail-heading">
      <a class="builder-back font-1-xs" href="#teste-historico-precos" aria-label="Voltar à build de exemplo">${iconeAnimado("arrow", "back")}Voltar à build</a>
      <span class="component-category font-1-xs">Processador</span>
      <h3 class="font-1-xl" id="test-product-title" tabindex="-1">${nome}</h3>
    </header>
    <div class="product-detail-layout">
      <div class="product-detail-visual glass-card">${imagemPeca(peca)}</div>
      <section class="product-stores" aria-labelledby="test-product-stores-title">
        <h4 class="font-1-l" id="test-product-stores-title">Onde comprar</h4>
        <p class="font-2-xs summary-note">Preços ilustrativos, sem frete. Confira o valor e o estoque na loja.</p>
        <div class="store-grid">${cartoesOfertasHtml(peca)}</div>
      </section>
      <section class="product-specifications glass-card" aria-labelledby="test-product-specs-title">
        <h4 class="font-1-l" id="test-product-specs-title">Especificações técnicas</h4>
        ${gruposFichaTecnica(peca).map(grupo => `
          <section class="product-specification-group">
            <h5 class="font-1-xs">${h(grupo.titulo)}</h5>
            <dl>${grupo.campos.map(([rotulo, valor]) => `
              <div><dt class="font-2-xs">${h(rotulo)}</dt><dd class="font-1-xs">${h(valor)}</dd></div>`).join("")}</dl>
          </section>`).join("")}
      </section>
      ${historicoPrecosHtml(peca, agora)}
    </div>`;

  function atualizarVista(focar = false) {
    const aberta = location.hash === hrefDetalhe;
    const mudou = build.hidden !== aberta;
    build.hidden = aberta;
    detalhe.hidden = !aberta;
    const visivel = aberta ? detalhe : build;
    iniciarIcones(visivel);
    iniciarImagens(visivel);
    if (aberta) iniciarHistoricoPrecos(detalhe, peca, agora);
    if (focar && mudou) visivel.querySelector("[tabindex='-1']").focus({preventScroll:true});
  }

  atualizarVista();
  window.addEventListener("hashchange", () => {
    atualizarVista([hrefDetalhe, "#teste-historico-precos"].includes(location.hash));
  });
});
