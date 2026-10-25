import { caminhoComparacao } from "./page-routes.js";

export function linkDaPaginaAtual(href,atual) {
  try {
    const pagina = new URL(atual), destino = new URL(href,pagina);
    // Ações (criar=1) e âncoras continuam disponíveis, mesmo na mesma página.
    return destino.origin === pagina.origin && !destino.search && !destino.hash
      && caminhoComparacao(destino.pathname) === caminhoComparacao(pagina.pathname);
  } catch { return false; }
}

export function marcarPaginaAtual(raiz = document,atual = location.href) {
  raiz.querySelectorAll('footer a[href],.site-menu-link[href],.profile-link[href]').forEach(link => {
    if (linkDaPaginaAtual(link.getAttribute("href"),atual)) link.setAttribute("aria-current","page");
    else if (link.getAttribute("aria-current") === "page") link.removeAttribute("aria-current");
  });
}
