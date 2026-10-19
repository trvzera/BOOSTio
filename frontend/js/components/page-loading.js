const pendentes = new Set();
export function escolherModoLoading({home,visitada}) { return home || !visitada ? "full" : "fade"; }
export function perfilLoading({home,visitada,frequente=false,cache=false,formulario=false}) {
  return {
    modo:escolherModoLoading({home,visitada}),
    velocidade:frequente && cache && !home ? 2.2 : 1,
    velocidadePronta:frequente && !home ? 2.2 : 1,
    fadeMs:home ? 480 : formulario ? 700 : frequente ? (cache ? 360 : 460) : 600,
    minimoMs:home ? 0 : formulario ? 800 : frequente && cache ? 160 : 320,
  };
}
let saindo = false;
export function navegarPara(destino) {
  const url = new URL(destino,location.href);
  transicionarSaida(() => { location.href = url.href; },url.origin !== location.origin);
}
export function transicionarSaida(acao,externo = false) {
  if (saindo) return;
  const reduzido = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduzido || externo) { acao(); return; }
  saindo = true;
  const tela = document.createElement("div");
  tela.className = "navigation-fade"; tela.setAttribute("aria-hidden","true");
  document.body.appendChild(tela);
  requestAnimationFrame(() => requestAnimationFrame(() => tela.classList.add("navigation-leaving")));
  setTimeout(acao,280);
}
export function iniciarTransicaoLinks() {
  document.addEventListener("click",evento => {
    const link = evento.target.closest("a[href]");
    if (!link || evento.defaultPrevented || evento.button !== 0 || evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey || link.download || link.target === "_blank" || link.hasAttribute("data-page-back")) return;
    const url = new URL(link.href,location.href);
    if (url.origin !== location.origin || !/\.html$/.test(url.pathname) || (url.pathname === location.pathname && url.search === location.search)) return;
    evento.preventDefault(); navegarPara(url.href);
  });
  window.addEventListener("pageshow",() => { saindo = false; document.querySelectorAll(".navigation-fade").forEach(tela => tela.remove()); });
}
export function acompanharCarregamento(promise) {
  pendentes.add(promise);
  // Não cria uma promise rejeitada sem consumidor.
  promise.then(() => pendentes.delete(promise),() => pendentes.delete(promise));
  return promise;
}
export async function aguardarCarregamentos() {
  // Dá aos outros módulos de DOMContentLoaded tempo para registrar suas tarefas.
  await new Promise(resolve => setTimeout(resolve,40));
  while (pendentes.size) await Promise.allSettled([...pendentes]);
}
