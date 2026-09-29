import { iconeAnimado, iniciarIcones } from "./components/ui.js";
import { linksVisitante, linksAutenticado } from "./components/navigation-config.js";

let navegacao;
const pagina = nome => new URL("../pages/" + nome, import.meta.url).href;

export function iniciarNavegacao() {
  if (navegacao) return navegacao;
  const host = document.querySelector("[data-site-navigation]") || document.body.appendChild(document.createElement("div"));
  host.dataset.siteNavigation = "";
  const preview = host.hasAttribute("data-menu-preview");
  if (!document.querySelector(".site-brand")) {
    const logo = document.createElement("a");
    logo.className = "site-brand";
    logo.href = pagina("index.html");
    logo.setAttribute("aria-label", "BOOSTio — página inicial");
    logo.innerHTML = '<img src="' + new URL("../imgs/logo.webp", import.meta.url).href + '" alt="BOOSTio" width="100" height="20">';
    document.body.prepend(logo);
  }
  const links = (itens, perfil = false) => itens.map(item =>
    '<a class="' + (perfil ? 'profile-link font-1-s' : 'site-menu-link') + '" href="' + pagina(item.pagina) + '" aria-label="Ir para ' + item.rotulo + '"' +
    (location.pathname.endsWith("/" + item.pagina) ? ' aria-current="page"' : "") + '>' +
    '<span class="site-menu-link-label">' + (item.icone ? iconeAnimado(item.icone) : "") +
    '<span>' + item.rotulo + '</span></span>' + (perfil ? "" : iconeAnimado("arrow")) + '</a>'
  ).join("");
  const conta = [
    {pagina:"builds.html", rotulo:"Builds", icone:"build"},
    {pagina:"configuracoes.html", rotulo:"Configurações", icone:"user"},
  ];
  const home = document.body.id === "inicio" || location.pathname.endsWith("/index.html");
  const linksMenu = home ? [...linksAutenticado,
    {pagina:"index.html#about-page",rotulo:"Sobre a BOOSTio"},
    {pagina:"index.html#services-page",rotulo:"Como funciona"},
    {pagina:"index.html#build-page",rotulo:"Começar montagem"},
  ] : linksAutenticado;
  host.innerHTML =
    '<div id="profile" class="site-profile"><button type="button" class="profile-toggle" aria-label="Abrir menu do perfil" aria-expanded="false" aria-controls="profile-options">' +
    iconeAnimado("profile") + '</button><nav id="profile-options" class="profile-panel" aria-label="Menu do perfil" aria-hidden="true" inert>' +
    '<div class="site-menu-group" data-profile-guest>' + links(linksVisitante, true) + '</div>' +
    '<div class="site-menu-group" data-profile-user hidden>' + links(conta, true) +
    '<div class="site-menu-divider"></div><button type="button" class="profile-link font-1-s profile-logout" id="btn-logout" aria-label="Sair da conta">' +
    '<span class="site-menu-link-label">' + iconeAnimado("logout") + '<span>Sair</span></span></button></div></nav></div>' +
    '<div class="site-menu" data-site-menu' + (preview ? "" : " hidden") + '><nav id="site-menu-panel" class="site-menu-panel" aria-label="Navegação entre páginas" aria-hidden="true" inert>' +
    '<div class="site-menu-group">' + links(linksMenu) + '</div></nav>' +
    '<button type="button" class="site-menu-toggle" aria-label="Abrir menu" aria-expanded="false" aria-controls="site-menu-panel">' +
    '<span class="ui-lottie hamburger-animation" data-lottie="hamburger" aria-hidden="true"><span class="ui-icon-fallback hamburger-fallback"><span></span><span></span><span></span></span></span></button></div>';

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
    painel.addEventListener("click", e => { if (e.target.closest("a,button")) controle.alternar(false); });
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
  navegacao = {host, perfil, hamburger, preview};
  iniciarIcones(host);
  return navegacao;
}

export function atualizarNavegacao(autenticado) {
  const {host, perfil, hamburger, preview} = iniciarNavegacao();
  host.querySelector("[data-profile-guest]").hidden = Boolean(autenticado);
  host.querySelector("[data-profile-user]").hidden = !autenticado;
  hamburger.container.hidden = !autenticado && !preview;
  perfil.alternar(false);
  hamburger.alternar(false);
}
if (document.body) iniciarNavegacao();
else document.addEventListener("DOMContentLoaded", iniciarNavegacao, {once:true});
