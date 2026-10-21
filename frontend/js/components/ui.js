import { registrarAnimacao, destruirAnimacao } from "./lottie-controller.js";
import { iniciarVoltar, atualizarBotoesVoltar } from "./navigation-back.js";
import { iniciarImagens } from "../build/imagens-produtos.js";

const arquivos = {
  plus:"plus.json", trash:"buildTrash.json", cart:"cartshopping.json", import:"login.json",
  arrow:"arrow.json", chevron:"chavron.json", checkbox:"checkbox.json", hamburger:"hamburger.json",
  login:"login.json", signup:"logon.json", build:"build.json", user:"user.json", profile:"profile.json", logout:"logout-lt.json",
  circledot:"circledot.json", magnifying:"magnifying.json", magic:"magic.json", dots:"dots.json",
  gamepad:"gamepad.json", microchip:"microchip.json", handsparkle:"handsparkle.json", normalhand:"normalhand.json",
  lock:"buildLock.json", visibility:"buildPublic.json", pencil:"buildPencil.json", clone:"buildClone.json", copy:"buildCopy.json", download:"buildDownload.json",
};
const alternativas = {plus:"+",trash:"×",cart:"↗",import:"→",arrow:"→",chevron:"⌄",checkbox:"✓",
  lock:"▣",visibility:"◉",pencil:"✎",clone:"▢",copy:"⧉",download:"↓",
  dots:'<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="4" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="20" cy="12" r="2"/></svg>',
  hamburger:"☰",login:"→",signup:"+",build:"▦",
  user:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="6" r="4"/><path d="M2 21v-3a7 7 0 0 1 10-6.3M16 12v2m0 6v2m-5-5h2m6 0h2m-8.5-3.5 1.4 1.4m4.2 4.2 1.4 1.4m0-7-1.4 1.4m-4.2 4.2-1.4 1.4"/><circle cx="16" cy="17" r="3"/></svg>',
  profile:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="7" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3"/></svg>',logout:"←",
  circledot:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>',
  magnifying:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="10" r="6.5"/><path d="m15 15 6 6"/></svg>',
  gamepad:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7h10c2 0 3 2 3.5 4l1 6a2.5 2.5 0 0 1-4 2L15 17H9l-2.5 2a2.5 2.5 0 0 1-4-2l1-6C4 9 5 7 7 7Z"/><path d="M8 10v5m-2.5-2.5h5"/><circle cx="16" cy="11" r=".8" fill="currentColor"/><circle cx="18" cy="14" r=".8" fill="currentColor"/></svg>',
  microchip:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 9h6v6H9zM9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3"/></svg>',
  handsparkle:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20v-4h4l3-3h3a2 2 0 0 1 0 4h-2m-4 3h9l5-5a2 2 0 0 0-3-2l-3 3M5 3v4m-2-2h4m10-3 1.2 3.8L22 7l-3.8 1.2L17 12l-1.2-3.8L12 7l3.8-1.2Z"/></svg>',
  normalhand:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 12V5a1.5 1.5 0 0 1 3 0v6-8a1.5 1.5 0 0 1 3 0v8-6a1.5 1.5 0 0 1 3 0v7-4a1.5 1.5 0 0 1 3 0v8a6 6 0 0 1-6 6h-1a6 6 0 0 1-5-3L3 13a1.5 1.5 0 0 1 2-2l2 2"/></svg>',
  magic:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m4 20 12-12 4 4L8 24M4 3v6M1 6h6M18 1v6M15 4h6"/></svg>'};
const ativos = new Map();
let sequencia = 0, iniciada = false;

export function iconeAnimado(nome, direcao = "internal", {invertido = false} = {}) {
  const orientacao = ["internal","external","back","up"].includes(direcao) ? direcao : "internal";
  return '<span class="ui-lottie" data-lottie="' + nome + '"' +
    (nome === "arrow" ? ' data-direction="' + orientacao + '"' : "") +
    (invertido ? ' data-lottie-reversed="true"' : "") +
    ' aria-hidden="true"><span class="ui-icon-fallback">' + (alternativas[nome] || "") + '</span></span>';
}
export function iniciarIcones(raiz = document) {
  iniciarImagens(raiz);
  for (const [elemento, estado] of ativos) {
    if (!elemento.isConnected) {
      estado.limpar(); destruirAnimacao(elemento.id,estado.animacao); ativos.delete(elemento);
    }
  }
  raiz.querySelectorAll("[data-lottie]:not([data-lottie-initialized])").forEach(async elemento => {
    if (elemento.closest("[inert], [hidden]")) return;
    elemento.dataset.lottieInitialized = "";
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    elemento.id ||= "ui-lottie-" + (++sequencia);
    const arquivo = arquivos[elemento.dataset.lottie];
    if (!arquivo) return;
    try {
      // user.json usa uma composição 1000×1000 com o desenho concentrado no centro.
      // Enquadra a área útil, incluindo o giro da engrenagem, sem escalar o SVG via CSS
      // (o renderer aplica seu próprio transform inline) ou aumentar o espaço do menu.
      const opcoes = elemento.dataset.lottie === "user"
        ? {rendererSettings:{viewBoxSize:"175 170 750 750",preserveAspectRatio:"xMidYMid meet"}}
        : {};
      const animacao = await registrarAnimacao(elemento.id,new URL("../../lottie/" + arquivo,import.meta.url).href,opcoes);
      if (!animacao) return;
      if (!elemento.isConnected) { destruirAnimacao(elemento.id,animacao); return; }
      const controle = elemento.closest("button,a,label,summary");
      const input = controle?.querySelector('input[type="checkbox"]');
      const alternavel = ["checkbox","chevron","hamburger","profile","dots"].includes(elemento.dataset.lottie);
      const aberto = () => input ? input.checked : controle?.getAttribute("aria-expanded") === "true";
      const invertido = elemento.dataset.lottieReversed === "true";
      const mover = direcao => {
        if (controle?.disabled || input?.disabled || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        animacao.setDirection(direcao); animacao.play();
      };
      const atualizarEstado = () => {
        if (input?.disabled) { animacao.goToAndStop(aberto() ? animacao.totalFrames - 1 : 0,true); return; }
        mover(aberto() ? 1 : -1);
      };
      const entrar = () => { if (!alternavel || !aberto()) mover(invertido ? -1 : 1); };
      const sair = () => { if (!alternavel || !aberto()) mover(invertido ? 1 : -1); };
      let observador;
      if (alternavel) {
        input?.addEventListener("change",atualizarEstado);
        if (controle && !input) {
          observador = new MutationObserver(atualizarEstado);
          observador.observe(controle,{attributes:true,attributeFilter:["aria-expanded"]});
        }
      }
      if (!alternavel || elemento.dataset.lottie === "profile") {
        controle?.addEventListener("pointerenter",entrar);
        controle?.addEventListener("pointerleave",sair);
        controle?.addEventListener("focusin",entrar);
        controle?.addEventListener("focusout",sair);
      }
      const pronto = () => {
        if (!elemento.isConnected) return;
        elemento.setAttribute("data-ready","");
        animacao.goToAndStop(invertido || alternavel && aberto() ? animacao.totalFrames - 1 : 0,true);
      };
      animacao.isLoaded ? pronto() : animacao.addEventListener("DOMLoaded",pronto);
      ativos.set(elemento,{animacao,limpar:() => {
        observador?.disconnect();
        input?.removeEventListener("change",atualizarEstado);
        controle?.removeEventListener("pointerenter",entrar);
        controle?.removeEventListener("pointerleave",sair);
        controle?.removeEventListener("focusin",entrar);
        controle?.removeEventListener("focusout",sair);
      }});
    } catch { /* A animação é opcional; o controle mantém seu fallback e sua função. */ }
  });
}

const motivos = {
  "btn-create-build":"Você atingiu o limite de três builds salvas.",
  "btn-sign-in":"Preencha o e-mail e a senha para entrar.",
  "btn-create-account":"Preencha os campos, confirme a senha e aceite os termos de uso.",
  "btn-confirm-code":"Solicite o código e preencha seus quatro dígitos.",
  "btn-send-link":"Informe seu e-mail para receber o link.",
  "btn-reset-password":"As senhas precisam coincidir e atender aos requisitos.",
  "save-password-btn":"Informe a senha atual e confirme a nova senha de pelo menos oito caracteres.",
  "confirm-delete-btn":"Digite seu nome de usuário exatamente como indicado.",
  "next-question":"Selecione uma resposta e informe o modelo das peças que você já possui.",
  "previous-products":"Você está na primeira página do catálogo.",
  "next-products":"Você está na última página do catálogo.",
};
function motivo(controle) {
  if (controle.dataset.busy === "true") return "Aguarde a conclusão da solicitação atual.";
  if (controle.dataset.disabledReason) return controle.dataset.disabledReason;
  if (controle.id === "btn-send-code") return "Aguarde o tempo de reenvio ou conclua o envio atual.";
  if (controle.matches(".form-step")) return "Responda à etapa anterior para liberar esta pergunta.";
  if (controle.dataset.acao === "copiar-link") return "Torne a build pública para compartilhar o link.";
  if (controle.dataset.acao === "duplicar") return motivos["btn-create-build"];
  if (["visibilidade","editar"].includes(controle.dataset.acao)) return "Destranque a build para alterar estes detalhes.";
  if (controle.textContent.includes("Voltar")) return "Você está na primeira etapa.";
  return motivos[controle.id] || "Esta ação está indisponível no estado atual. Confira os campos e os avisos da página.";
}
// Evita mutação quando o texto é igual: o tooltip também está dentro do body observado.
export function definirTextoSeMudou(elemento,texto) {
  if (elemento.textContent !== texto) elemento.textContent = texto;
}
function padronizarControles() {
  document.querySelectorAll(".build-action-close, .compare-button-close, .test-dialog-close, [data-ui-close], #btn-close-verification").forEach(controle => {
    if (controle.classList.contains("ui-close-button")) return;
    controle.classList.add("ui-close-button");
    controle.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>';
  });
  document.querySelectorAll("[data-page-back], .builder-back, .page-back-link, .prontas-voltar, .company-back").forEach(controle => {
    controle.classList.add("ui-back-button");
    if (!controle.querySelector('[data-lottie="arrow"]')) controle.insertAdjacentHTML("afterbegin",iconeAnimado("arrow","back"));
  });
}
export function iniciarUI() {
  if (iniciada) return;
  iniciada = true;
  iniciarVoltar();
  const tooltip = document.createElement("div");
  tooltip.id = "ui-tooltip"; tooltip.role = "tooltip"; tooltip.hidden = true; document.body.append(tooltip);
  if (typeof tooltip.showPopover === "function") tooltip.setAttribute("popover","manual");
  let atual;
  const esconder = () => {
    atual?.removeAttribute("aria-describedby"); atual = null;
    if (typeof tooltip.hidePopover === "function" && tooltip.matches(":popover-open")) tooltip.hidePopover();
    tooltip.hidden = true;
  };
  function posicionar(ancora) {
    const vista = window.visualViewport;
    const esquerda = (vista?.offsetLeft || 0) + 12, topo = (vista?.offsetTop || 0) + 12;
    const largura = vista?.width || innerWidth, altura = vista?.height || innerHeight;
    tooltip.style.maxWidth = Math.max(0,Math.min(300,largura - 24)) + "px";
    const r = ancora.getBoundingClientRect();
    const y = r.top > topo + tooltip.offsetHeight + 8 ? r.top - tooltip.offsetHeight - 8 : r.bottom + 8;
    tooltip.style.left = Math.max(esquerda,Math.min(r.left,esquerda + largura - tooltip.offsetWidth - 24)) + "px";
    tooltip.style.top = Math.max(topo,Math.min(y,topo + altura - tooltip.offsetHeight - 24)) + "px";
  }
  function mostrar(ancora) {
    const controle = ancora.querySelector("button");
    if (!controle?.disabled) return;
    esconder(); atual = ancora; definirTextoSeMudou(tooltip,motivo(controle)); tooltip.hidden = false;
    if (tooltip.hasAttribute("popover")) tooltip.showPopover();
    ancora.setAttribute("aria-describedby",tooltip.id); posicionar(ancora);
  }
  function atualizar() {
    padronizarControles();
    atualizarBotoesVoltar();
    document.querySelectorAll("button").forEach(controle => {
      let ancora = controle.parentElement;
      if (!ancora) return;
      if (controle.disabled && !ancora.classList.contains("disabled-tip-anchor")) {
        ancora = document.createElement("span"); ancora.className = "disabled-tip-anchor"; ancora.tabIndex = 0;
        ancora.setAttribute("role","group");
        controle.before(ancora); ancora.append(controle);
        ancora.addEventListener("pointerenter",() => mostrar(ancora));
        ancora.addEventListener("pointerleave",esconder);
        ancora.addEventListener("focus",() => mostrar(ancora));
        ancora.addEventListener("blur",esconder);
      }
      if (controle.disabled) {
        const descricao = (controle.getAttribute("aria-label") || controle.textContent.trim()) + ". " + motivo(controle);
        if (ancora.getAttribute("aria-label") !== descricao) ancora.setAttribute("aria-label",descricao);
        if (atual === ancora) { definirTextoSeMudou(tooltip,motivo(controle)); posicionar(ancora); }
      } else if (ancora.classList.contains("disabled-tip-anchor")) {
        if (atual === ancora) esconder();
        ancora.replaceWith(controle);
      }
    });
    document.querySelectorAll('a[href*="github.com"],a[href*="linkedin.com"]').forEach(link => {
      if (link.querySelector(".social-logo")) return;
      const img = document.createElement("img"); img.className = "social-logo"; img.alt = "";
      img.src = new URL("../../svgs/" + (link.href.includes("github.com") ? "github.svg" : "linkedin.svg"),import.meta.url).href;
      link.prepend(img); link.classList.add("social-link");
    });
    iniciarIcones();
  }
  atualizar();
  let agendada = false;
  const observador = new MutationObserver(registros => {
    const relevante = registros.some(r => !r.target.closest?.("#ui-tooltip, [data-lottie]"));
    if (!relevante || agendada) return;
    agendada = true;
    requestAnimationFrame(() => { agendada = false; atualizar(); });
  });
  observador.observe(document.body,{childList:true,subtree:true,attributes:true,
    attributeFilter:["disabled","data-disabled-reason","data-busy"]});
  document.addEventListener("keydown",e => { if (e.key === "Escape") esconder(); });
  window.addEventListener("scroll",esconder,{passive:true});
  window.addEventListener("resize",esconder);
  window.visualViewport?.addEventListener("resize",esconder);
  window.visualViewport?.addEventListener("scroll",esconder,{passive:true});
}
