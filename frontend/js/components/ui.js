import { registrarAnimacao, destruirAnimacao } from "./lottie-controller.js";
import { iniciarVoltar, atualizarBotoesVoltar } from "./navigation-back.js";

const arquivos = {
  plus:"plus.json", trash:"buildTrash.json", cart:"cartshopping.json", import:"login.json",
  arrow:"arrow.json", chevron:"chavron.json", checkbox:"checkbox.json", hamburger:"hamburger.json",
  login:"login.json", signup:"logon.json", build:"build.json", user:"user.json", profile:"profile.json", logout:"logout-lt.json",
};
const alternativas = {plus:"+",trash:"×",cart:"↗",import:"→",arrow:"→",chevron:"⌄",checkbox:"✓",
  hamburger:"☰",login:"→",signup:"+",build:"▦",user:"●",
  profile:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="7" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3"/></svg>',logout:"←"};
const ativos = new Map();
let sequencia = 0, iniciada = false;

export function iconeAnimado(nome, direcao = "internal") {
  const orientacao = ["internal","external","back","up"].includes(direcao) ? direcao : "internal";
  return '<span class="ui-lottie" data-lottie="' + nome + '"' +
    (nome === "arrow" ? ' data-direction="' + orientacao + '"' : "") +
    ' aria-hidden="true"><span class="ui-icon-fallback">' + (alternativas[nome] || "") + '</span></span>';
}
export function iniciarIcones(raiz = document) {
  for (const [elemento, estado] of ativos) {
    if (!elemento.isConnected) {
      estado.limpar(); destruirAnimacao(elemento.id,estado.animacao); ativos.delete(elemento);
    }
  }
  raiz.querySelectorAll("[data-lottie]:not([data-lottie-initialized])").forEach(async elemento => {
    elemento.dataset.lottieInitialized = "";
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    elemento.id ||= "ui-lottie-" + (++sequencia);
    const arquivo = arquivos[elemento.dataset.lottie];
    if (!arquivo) return;
    try {
      const animacao = await registrarAnimacao(elemento.id,new URL("../../lottie/" + arquivo,import.meta.url).href);
      if (!animacao) return;
      if (!elemento.isConnected) { destruirAnimacao(elemento.id,animacao); return; }
      const controle = elemento.closest("button,a,label");
      const input = controle?.querySelector('input[type="checkbox"]');
      const alternavel = ["checkbox","chevron","hamburger","profile"].includes(elemento.dataset.lottie);
      const aberto = () => input ? input.checked : controle?.getAttribute("aria-expanded") === "true";
      const mover = direcao => {
        if (controle?.disabled || input?.disabled || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        animacao.setDirection(direcao); animacao.play();
      };
      const atualizarEstado = () => mover(aberto() ? 1 : -1);
      const entrar = () => { if (!alternavel || !aberto()) mover(1); };
      const sair = () => { if (!alternavel || !aberto()) mover(-1); };
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
        animacao.goToAndStop(alternavel && aberto() ? animacao.totalFrames - 1 : 0,true);
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
export function iniciarUI() {
  if (iniciada) return;
  iniciada = true;
  iniciarVoltar();
  const tooltip = document.createElement("div");
  tooltip.id = "ui-tooltip"; tooltip.role = "tooltip"; tooltip.hidden = true; document.body.append(tooltip);
  let atual;
  const esconder = () => { atual?.removeAttribute("aria-describedby"); atual = null; tooltip.hidden = true; };
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
    ancora.setAttribute("aria-describedby",tooltip.id); posicionar(ancora);
  }
  function atualizar() {
    atualizarBotoesVoltar();
    document.querySelectorAll("button").forEach(controle => {
      let ancora = controle.parentElement;
      if (!ancora) return;
      if (controle.disabled && !ancora.classList.contains("disabled-tip-anchor")) {
        ancora = document.createElement("span"); ancora.className = "disabled-tip-anchor"; ancora.tabIndex = 0;
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
