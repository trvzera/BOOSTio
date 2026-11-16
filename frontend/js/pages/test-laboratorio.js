import { iniciarIcones } from "../components/ui.js";

const navegacao = document.querySelector(".lab-preview-nav");
if (navegacao) {
  const abas = [...navegacao.querySelectorAll('a[href^="#"]')];
  const painelDe = aba => document.getElementById(aba.hash.slice(1));
  let equipePendente;

  async function carregarEquipe() {
    const alvo = document.querySelector("[data-lab-team-preview]");
    if (alvo.dataset.loaded) return;
    if (equipePendente) return equipePendente;
    alvo.innerHTML = '<p class="font-2-s" role="status">Carregando a prévia da equipe…</p>';
    const url = new URL("../../pages/sobre.html", import.meta.url);
    equipePendente = (async () => {
      try {
        const resposta = await fetch(url);
        if (!resposta.ok) throw new Error("Falha ao carregar a equipe");
        const documento = new DOMParser().parseFromString(await resposta.text(), "text/html");
        const equipe = documento.querySelector("#company-team");
        if (!equipe) throw new Error("Seção da equipe não encontrada");
        equipe.querySelectorAll("[src], [href]").forEach(elemento => {
          for (const atributo of ["src", "href"]) {
            const caminho = elemento.getAttribute(atributo);
            if (caminho) elemento.setAttribute(atributo, new URL(caminho, url).href);
          }
        });
        alvo.replaceChildren(equipe);
        alvo.dataset.loaded = "true";
        iniciarIcones(alvo);
      } catch {
        alvo.innerHTML = '<p class="font-2-s" role="status">Não foi possível carregar a prévia da equipe. Confira a conexão e tente novamente.</p><button type="button" class="btn-secondary" data-lab-team-retry aria-label="Tentar carregar a prévia da equipe novamente">Tentar novamente</button>';
        alvo.querySelector("[data-lab-team-retry]").addEventListener("click", carregarEquipe);
      } finally {
        equipePendente = null;
      }
    })();
    return equipePendente;
  }

  navegacao.setAttribute("role", "tablist");
  abas.forEach((aba, indice) => {
    aba.id = "lab-preview-tab-" + indice;
    aba.setAttribute("role", "tab");
    aba.setAttribute("aria-controls", painelDe(aba).id);
    const painel = painelDe(aba);
    painel.dataset.labPanel = "";
    painel.setAttribute("role", "tabpanel");
    painel.setAttribute("aria-labelledby", aba.id);
    painel.tabIndex = 0;
  });
  function selecionar(aba, {focar = false, atualizarUrl = false} = {}) {
    abas.forEach(item => {
      const ativa = item === aba;
      item.setAttribute("aria-selected", String(ativa));
      item.tabIndex = ativa ? 0 : -1;
      painelDe(item).hidden = !ativa;
    });
    if (atualizarUrl && location.hash !== aba.hash) history.pushState(null, "", aba.hash);
    if (focar) aba.focus();
    iniciarIcones(painelDe(aba));
    if (aba.hash === "#teste-equipe") void carregarEquipe();
  }
  const abaDaUrl = () => {
    const destino = document.getElementById(location.hash.slice(1));
    return abas.find(aba => aba.hash === location.hash || (destino && painelDe(aba).contains(destino))) || abas[0];
  };
  abas.forEach((aba, indice) => {
    aba.addEventListener("click", evento => {
      if (evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) return;
      evento.preventDefault(); selecionar(aba, {atualizarUrl: true});
    });
    aba.addEventListener("keydown", evento => {
      const destino = {ArrowRight: (indice + 1) % abas.length, ArrowLeft: (indice + abas.length - 1) % abas.length, Home: 0, End: abas.length - 1}[evento.key];
      if (destino === undefined) return;
      evento.preventDefault(); selecionar(abas[destino], {focar: true, atualizarUrl: true});
    });
  });
  selecionar(abaDaUrl());
  window.addEventListener("hashchange", () => selecionar(abaDaUrl()));
  window.addEventListener("popstate", () => selecionar(abaDaUrl()));
}
