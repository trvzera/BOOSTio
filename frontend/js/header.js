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
    '<a class="profile-link profile-admin font-1-s" href="' + pagina("admin.html") + '" data-menu-admin hidden aria-label="Ir para a administração"><span class="site-menu-link-label">' + iconeAnimado("admin") + '<span>Administração</span></span></a>' +
    '<div class="site-menu-divider"></div><button type="button" class="profile-link font-1-s profile-logout" id="btn-logout" aria-label="Sair da conta">' +
    '<span class="site-menu-link-label">' + iconeAnimado("logout") + '<span>Sair</span></span></button></div></nav></div>' +
    '<div class="site-menu" data-site-menu' + (preview ? "" : " hidden") + '><nav id="site-menu-panel" class="site-menu-panel" aria-label="Navegação entre páginas" aria-hidden="true" inert>' +
    '<div class="site-menu-group">' + links(linksMenu) +
    '<a class="site-menu-link site-menu-telegram" href="https://t.me/boostioofertas" target="_blank" rel="noopener noreferrer" aria-label="Grupo de promoções da BOOSTio no Telegram (abre em nova aba)"><span class="site-menu-link-label"><svg class="site-menu-telegram-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg><span>Grupo de promoções</span></span>' + iconeAnimado("arrow","external") + '</a>' +
    '<div class="site-menu-divider"></div><button type="button" class="site-menu-link site-motion-toggle" aria-label="Reduzir animações e desativar vídeos" aria-pressed="false"><span>Reduzir animações</span>' + iconeAnimado("toggle") + '</button></div></nav>' +
    '<button type="button" class="site-menu-toggle" aria-label="Abrir menu" aria-expanded="false" aria-controls="site-menu-panel">' +
    '<span class="ui-lottie hamburger-animation" data-lottie="hamburger" aria-hidden="true"><span class="ui-icon-fallback hamburger-fallback"><span></span><span></span><span></span></span></span></button></div>';
  host.prepend(logo);
  const movimento = host.querySelector(".site-motion-toggle");
  const atualizarMovimento = () => {
    const reduzido = movimentoReduzido();
    movimento.setAttribute("aria-pressed", String(reduzido));

    movimento.title = reduzido ? "Vídeos e efeitos de página desativados. Ícones animados continuam ativos. Clique para reativar os efeitos." : "Desativar vídeos e reduzir os efeitos de página, mantendo os ícones animados.";
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

export function atualizarNavegacao(autenticado, administrador = false) {
  const {host, perfil, hamburger} = iniciarNavegacao();
  host.querySelector("[data-profile-guest]").hidden = Boolean(autenticado);
  host.querySelector("[data-profile-user]").hidden = !autenticado;
  host.querySelectorAll("[data-menu-auth]").forEach(link => { link.hidden = !autenticado; });
  host.querySelectorAll("[data-menu-admin]").forEach(link => { link.hidden = !(autenticado && administrador); });
  hamburger.container.hidden = false;
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
