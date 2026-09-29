import { navegarPara,transicionarSaida } from "./page-loading.js";
const rotulos = {
  "index.html":"Voltar ao início", "formulario.html":"Voltar ao formulário",
  "configuracao-build.html":"Voltar à build", "builds.html":"Voltar às suas builds",
  "pecas.html":"Voltar ao catálogo", "peca.html":"Voltar à peça",
  "desenvolvedores.html":"Voltar à equipe", "configuracoes.html":"Voltar ao perfil",
  "login.html":"Voltar ao login", "signin.html":"Voltar ao cadastro",
  "esqueci-senha.html":"Voltar à recuperação de senha", "testes.html":"Voltar aos testes",
};

// Mantém a URL completa (build, categoria, filtros e posição na página).
export function destinoAnterior(atual, origem, padrao) {
  const base = new URL(atual);
  function valido(valor) {
    if (!valor) return null;
    try {
      const url = new URL(valor, base);
      if (url.origin !== base.origin || url.protocol !== base.protocol ||
          !["http:","https:","file:"].includes(url.protocol) ||
          url.pathname.endsWith("/erro.html") ||
          (url.pathname === base.pathname && url.search === base.search)) return null;
      return url.href;
    } catch { return null; }
  }
  return valido(origem) || valido(padrao) || new URL("./index.html", base).href;
}
export function rotuloVoltar(destino) {
  return rotulos[new URL(destino).pathname.split("/").pop()] || "Voltar à página anterior";
}

function retorno(controle) {
  const nav = window.navigation;
  const entrada = nav?.entries().find(e => e.index === nav.currentEntry.index - 1);
  // A Navigation API identifica a entrada real mesmo após back/forward ou replace.
  const origem = nav ? entrada?.url : document.referrer;
  const padrao = controle.dataset.backFallback || controle.getAttribute("href") || "./index.html";
  const destino = destinoAnterior(location.href, origem, padrao);
  return {destino, historico:Boolean(origem && destino === origem && (nav ? entrada : history.length > 1))};
}
export function atualizarBotoesVoltar() {
  document.querySelectorAll("[data-page-back]").forEach(controle => {
    controle.dataset.backFallback ||= controle.getAttribute("href") || "./index.html";
    const {destino} = retorno(controle), rotulo = rotuloVoltar(destino);
    if (controle.tagName === "A" && controle.href !== destino) controle.href = destino;
    if (controle.title !== rotulo) controle.title = rotulo;
    if (controle.getAttribute("aria-label") !== rotulo) controle.setAttribute("aria-label",rotulo);
    const texto = controle.querySelector("[data-back-label]");
    if (texto && texto.textContent !== rotulo) texto.textContent = rotulo;
  });
}
let iniciado = false;
export function iniciarVoltar() {
  if (iniciado) return;
  iniciado = true;
  document.addEventListener("click",evento => {
    const controle = evento.target.closest("[data-page-back]");
    if (!controle || evento.defaultPrevented || evento.button !== 0 || evento.ctrlKey ||
        evento.metaKey || evento.shiftKey || evento.altKey || controle.target === "_blank") return;
    evento.preventDefault();
    const {destino,historico} = retorno(controle);
    if (historico) transicionarSaida(() => history.back());
    else navegarPara(destino);
  });
  window.addEventListener("pageshow",atualizarBotoesVoltar);
}
