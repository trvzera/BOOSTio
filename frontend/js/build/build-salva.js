import { buscarBuild } from "../api/build/builds.js";
import { fetchComErro } from "../api/_shared/fetchComErro.js";
import { categorias, htmlSeguro, imagemPeca, moeda, ofertasPeca } from "./catalogo.js";
import { formatarDataHora } from "../utils/formatarData.js";
import { abrirCompraBuild, avisoCompraHtml } from "./acoes-build.js";
import { avisar } from "./interface.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";

function linhaPeca(peca) {
  const categoria = categorias.find(item => item.id === peca.tipo);
  const titulo = categoria?.nome || peca.tipo;
  const quantidade = Number(peca.quantidade) || 1;
  const oferta = ofertasPeca(peca)[0];

  return `<section class="component-group">
    <div class="component-group-heading"><h2>${htmlSeguro(titulo)}</h2><span class="component-count">${quantidade} ${quantidade === 1 ? "unidade" : "unidades"}</span></div>
    <article class="component-row component-selected glass-card build-saved-piece">
      <div class="component-selected-main">
        <div class="component-image">${imagemPeca({...peca, categoria:peca.tipo})}</div>
        <div class="component-copy"><h3 class="component-model font-1-m-b">${htmlSeguro(peca.nome)}</h3><p>${quantidade} × ${moeda(peca.preco)}</p></div>
        <div class="component-purchase">
          <a class="component-buy btn-primary" href="${htmlSeguro(oferta.url)}" target="_blank" rel="noopener noreferrer" aria-label="${oferta.direta ? "Comprar" : "Buscar"} ${htmlSeguro(peca.nome)} na ${htmlSeguro(oferta.loja)} em uma nova aba">${iconeAnimado("cart")}${oferta.direta ? "Comprar" : "Buscar"}</a>
          <strong>${moeda(peca.preco * quantidade)}</strong>
        </div>
      </div>
    </article>
  </section>`;
}

export async function mostrarBuildSalva(main, buildId, publico = false) {
  const { build } = publico
    ? await fetchComErro(`/build/${encodeURIComponent(buildId)}/publica`, {method:"GET"})
    : await buscarBuild(buildId);
  main.innerHTML = `<header class="builder-heading">
    <div><a class="builder-back font-1-xs" href="./builds.html" aria-label="Voltar para Minhas builds">← Minhas builds</a>
      <h1>${htmlSeguro(build.nome)}</h1>
      <p>Configuração salva na sua conta em ${htmlSeguro(formatarDataHora(build.criado_em))}.</p></div>
  </header>
  <div class="builder-layout">
    <div class="component-list">${build.componentes.map(linhaPeca).join("")}</div>
    <aside class="build-sidebar"><section class="build-summary glass-card">
      <span class="summary-eyebrow">Total das peças</span>
      <strong class="summary-total">${moeda(build.preco_total)}</strong>
      <p class="summary-note">Preços atuais cadastrados no banco de dados, sem frete.</p>
      <button class="btn-secondary" type="button" id="buy-configuration" aria-label="Comprar peças da build">${iconeAnimado("cart")}Comprar build</button>
      ${avisoCompraHtml()}
      <a class="btn-secondary build-saved-back" href="./builds.html" aria-label="Voltar às minhas builds">Voltar às minhas builds</a>
    </section></aside>
  </div>`;
  main.querySelector("#buy-configuration").onclick = () => {
    const componentes = Object.fromEntries(build.componentes.map(peca => [peca.tipo, { id: peca.id, quantidade: peca.quantidade }]));
    const catalogo = build.componentes.map(peca => ({
      ...peca,
      categoria: peca.tipo,
      ofertas: peca.link ? [{ loja: "kabum", url: peca.link, preco: peca.preco }] : [],
    }));
    try { abrirCompraBuild({ titulo: build.nome, componentes }, catalogo); }
    catch (erro) { avisar(erro.message); }
  };
  iniciarIcones(main);
}
