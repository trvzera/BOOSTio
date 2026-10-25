import { iconeAnimado, iniciarIcones } from "./components/ui.js";
import { linksVisitante, linksAutenticado } from "./components/navigation-config.js";
import { marcarPaginaAtual } from "./components/navigation-current.js";
import { movimentoReduzido, definirMovimentoReduzido, observarMovimento } from "./components/motion-preference.js";

let navegacao;
const pagina = nome => new URL("../pages/" + nome, import.meta.url).href;

export function iniciarNavegacao() {
  if (navegacao) return navegacao;
  const host = document.querySelector("[data-site-navigation]") || document.body.appendChild(document.createElement("div"));
  host.dataset.siteNavigation = "";
  host.setAttribute("role", "banner");
  host.setAttribute("aria-label", "Navegação da BOOSTio");
  const preview = host.hasAttribute("data-menu-preview");
  let logo = document.querySelector(".site-brand");
  if (!logo) {
    logo = document.createElement("a");
    logo.className = "site-brand";
    logo.href = pagina("index.html");
    logo.setAttribute("aria-label", "BOOSTio — página inicial");
    logo.innerHTML = '<img src="' + new URL("../imgs/logo.webp", import.meta.url).href + '" alt="BOOSTio" width="668" height="237" decoding="async">';
  }
  const links = (itens, perfil = false) => itens.map(item =>
    '<a class="' + (perfil ? 'profile-link font-1-s' : 'site-menu-link') + '" href="' + pagina(item.pagina) + '" aria-label="Ir para ' + item.rotulo + '"' +
    (item.autenticado ? ' data-menu-auth hidden' : '') +
    (location.pathname.endsWith("/" + item.pagina) ? ' aria-current="page"' : "") + '>' +
    '<span class="site-menu-link-label">' + (perfil && item.icone ? iconeAnimado(item.icone) : "") +
    '<span>' + item.rotulo + '</span></span>' + (perfil ? '' : iconeAnimado("arrow")) + '</a>'
  ).join("");
  const conta = [
    {pagina:"builds.html", rotulo:"Minhas builds", icone:"build"},
    {pagina:"configuracoes.html", rotulo:"Configurações", icone:"user"},
  ];
  const linksMenu = linksAutenticado;
  host.innerHTML =
    '<div id="profile" class="site-profile"><button type="button" class="profile-toggle" aria-label="Abrir menu do perfil" aria-expanded="false" aria-controls="profile-options">' +
    iconeAnimado("profile") + '</button><nav id="profile-options" class="profile-panel" aria-label="Menu do perfil" aria-hidden="true" inert>' +
    '<div class="site-menu-group" data-profile-guest>' + links(linksVisitante, true) + '</div>' +
    '<div class="site-menu-group" data-profile-user hidden>' + links(conta, true) +
    '<div class="site-menu-divider"></div><button type="button" class="profile-link font-1-s profile-logout" id="btn-logout" aria-label="Sair da conta">' +
    '<span class="site-menu-link-label">' + iconeAnimado("logout") + '<span>Sair</span></span></button></div></nav></div>' +
    '<div class="site-menu" data-site-menu' + (preview ? "" : " hidden") + '><nav id="site-menu-panel" class="site-menu-panel" aria-label="Navegação entre páginas" aria-hidden="true" inert>' +
    '<div class="site-menu-group">' + links(linksMenu) +
    '<div class="site-menu-divider"></div><button type="button" class="site-menu-link site-motion-toggle" aria-label="Reduzir animações e desativar vídeos" aria-pressed="false">Reduzir animações</button></div></nav>' +
    '<button type="button" class="site-menu-toggle" aria-label="Abrir menu" aria-expanded="false" aria-controls="site-menu-panel">' +
    '<span class="ui-lottie hamburger-animation" data-lottie="hamburger" aria-hidden="true"><span class="ui-icon-fallback hamburger-fallback"><span></span><span></span><span></span></span></span></button></div>';
  host.prepend(logo);
  const movimento = host.querySelector(".site-motion-toggle");
  const atualizarMovimento = () => {
    const reduzido = movimentoReduzido();
    movimento.setAttribute("aria-pressed", String(reduzido));
    // O nome do botão permanece estável; leitores de tela anunciam o estado pressionado.
    movimento.title = reduzido ? "Animações reduzidas. Clique para reativar." : "Desativar vídeos e reduzir os efeitos de movimento.";
  };
  movimento.addEventListener("click", () => definirMovimentoReduzido(!movimentoReduzido()));
  observarMovimento(atualizarMovimento);
  atualizarMovimento();

  const controles = [];
  function configurar(container, painel, botao, rotulo, hover = false) {
    let fixado = false, fechamento;
    const controle = {container, painel, botao, alternar(aberto) {
      clearTimeout(fechamento);
      if (!aberto) fixado = false;
      container.toggleAttribute("data-open", aberto);
      painel.inert = !aberto;
      painel.setAttribute("aria-hidden", String(!aberto));
      botao.setAttribute("aria-expanded", String(aberto));
      botao.setAttribute("aria-label", (aberto ? "Fechar " : "Abrir ") + rotulo);
      if (aberto) iniciarIcones(painel);
    }};
    const abrir = () => {
      controles.forEach(outro => { if (outro !== controle) outro.alternar(false); });
      controle.alternar(true);
    };
    botao.addEventListener("click", () => {
      const aberto = hover ? !fixado : !container.hasAttribute("data-open");
      if (aberto) { abrir(); fixado = hover; }
      else controle.alternar(false);
    });
    if (hover) {
      container.addEventListener("pointerenter", e => {
        if (e.pointerType === "mouse") abrir();
      });
      container.addEventListener("pointerleave", e => {
        if (e.pointerType !== "mouse" || fixado) return;
        fechamento = setTimeout(() => {
          if (!painel.contains(document.activeElement)) controle.alternar(false);
        }, 160);
      });
      container.addEventListener("focusin", abrir);
      container.addEventListener("focusout", e => {
        if (!fixado && !container.contains(e.relatedTarget) && !container.matches(":hover")) controle.alternar(false);
      });
    }
    painel.addEventListener("click", e => {
      if (e.target.closest(".site-motion-toggle")) return;
      if (e.target.closest("a,button")) controle.alternar(false);
    });
    controles.push(controle);
    return controle;
  }
  const perfil = configurar(host.querySelector(".site-profile"), host.querySelector("#profile-options"), host.querySelector(".profile-toggle"), "menu do perfil", true);
  const hamburger = configurar(host.querySelector(".site-menu"), host.querySelector("#site-menu-panel"), host.querySelector(".site-menu-toggle"), "menu");
  document.addEventListener("click", e => controles.forEach(c => { if (!c.container.contains(e.target)) c.alternar(false); }));
  document.addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    controles.forEach(c => { if (c.container.hasAttribute("data-open")) { c.botao.focus(); c.alternar(false); } });
  });
  hamburger.painel.querySelectorAll(".site-menu-link").forEach((link, indice) => link.style.setProperty("--menu-item-index", indice));
  marcarPaginaAtual();
  host.addEventListener("click",evento => {
    if (evento.target.closest('a[aria-current="page"]') && !evento.ctrlKey && !evento.metaKey && !evento.shiftKey && !evento.altKey) evento.preventDefault();
  });
  navegacao = {host, perfil, hamburger, preview};
  iniciarIcones(host);
  return navegacao;
}

export function atualizarNavegacao(autenticado) {
  const {host, perfil, hamburger} = iniciarNavegacao();
  host.querySelector("[data-profile-guest]").hidden = Boolean(autenticado);
  host.querySelector("[data-profile-user]").hidden = !autenticado;
  host.querySelectorAll("[data-menu-auth]").forEach(link => { link.hidden = !autenticado; });
  hamburger.container.hidden = false; // Visitantes também acessam a navegação pública.
  iniciarIcones(host);
  perfil.alternar(false);
  hamburger.alternar(false);
}
if (document.body) iniciarNavegacao();
else document.addEventListener("DOMContentLoaded", iniciarNavegacao, {once:true});
document.addEventListener("DOMContentLoaded",() => {
  marcarPaginaAtual();
  document.querySelectorAll("footer").forEach(footer => footer.addEventListener("click",evento => {
    if (evento.target.closest('a[aria-current="page"]') && !evento.ctrlKey && !evento.metaKey && !evento.shiftKey && !evento.altKey) evento.preventDefault();
  }));
},{once:true});
