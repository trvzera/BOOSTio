import { navegarPara,transicionarSaida } from "./page-loading.js";
import { nomePagina, caminhoComparacao } from "./page-routes.js";
const rotulos = {
  "index.html":"Voltar ao início", "formulario.html":"Voltar ao formulário",
  "configuracao-build.html":"Voltar à build", "builds.html":"Voltar para Minhas builds",
  "configuracoes-prontas.html":"Voltar para Builds prontas",
  "pecas.html":"Voltar ao catálogo", "peca.html":"Voltar à peça",
  "sobre.html":"Voltar à página Sobre nós", "configuracoes.html":"Voltar ao perfil",
  "login.html":"Voltar ao login", "signin.html":"Voltar ao cadastro",
  "esqueci-senha.html":"Voltar à recuperação de senha", "testes.html":"Voltar aos testes",
};

// Mantém a URL completa (build, categoria, filtros e posição na página).
export function destinoAnterior(atual, origem, padrao, contextual = false) {
  const base = new URL(atual);
  function valido(valor) {
    if (!valor) return null;
    try {
      const url = new URL(valor, base);
      if (url.origin !== base.origin || url.protocol !== base.protocol ||
          !["http:","https:","file:"].includes(url.protocol) ||
          nomePagina(url.pathname) === "erro.html" ||
          (caminhoComparacao(url.pathname) === caminhoComparacao(base.pathname) && url.search === base.search)) return null;
      return url.href;
    } catch { return null; }
  }
  const anterior = valido(origem), destino = valido(padrao);
  if (contextual && destino) {
    // Um retorno à build/categoria não pode apontar ao início ou a outra build.
    // Preserva filtros e posição do histórico somente dentro do mesmo contexto.
    const esperado = new URL(destino), historico = anterior && new URL(anterior);
    const mesmoContexto = historico && caminhoComparacao(esperado.pathname) === caminhoComparacao(historico.pathname) &&
      ["build","build_id","id","categoria"].every(chave => esperado.searchParams.get(chave) === historico.searchParams.get(chave));
    return mesmoContexto ? anterior : destino;
  }
  return anterior || destino || new URL("./index.html", base).href;
}

// Nunca retorna o editor sem ID: essa URL inicia a criação de uma nova build.
export function destinoBuild(atual) {
  const url = new URL(atual), id = url.searchParams.get("build");
  if (!["pecas.html", "peca.html"].includes(nomePagina(url.pathname)) || !id?.trim()) return "./builds.html";
  return "./configuracao-build.html?" + new URLSearchParams({[id.startsWith("s-") ? "build_id" : "id"]:id});
}
export function rotuloVoltar(destino) {
  return rotulos[nomePagina(new URL(destino).pathname)] || "Voltar à página anterior";
}

function retorno(controle) {
  const nav = window.navigation;
  const entrada = nav?.entries().find(e => e.index === nav.currentEntry.index - 1);
  // A Navigation API identifica a entrada real mesmo após back/forward ou replace.
  const origem = nav ? entrada?.url : document.referrer;
  const padrao = controle.dataset.backFallback || controle.getAttribute("href") || "./index.html";
  const destino = destinoAnterior(location.href, origem, padrao, controle.hasAttribute("data-back-destination"));
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
