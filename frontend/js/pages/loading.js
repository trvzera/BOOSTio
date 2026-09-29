import "../header.js";
import "../auth/auth.js";
import { iniciarTratamentoGlobalDeErros } from "../components/error-handler.js";
import { iniciarUI } from "../components/ui.js";
import { iniciarEntradaPagina } from "../components/page-entry.js";
import { iniciarScrollReveal } from "../components/scroll-reveal.js";
import { aguardarCarregamentos, perfilLoading } from "../components/page-loading.js";

iniciarTratamentoGlobalDeErros();
let tela = document.querySelector("#loading-screen");
const video = document.querySelector("#loading-video");
let visitada = false, cache = false;
try {
  visitada = sessionStorage.getItem("boostio:visita-iniciada") === "1";
  cache = sessionStorage.getItem("boostio:catalogo-pronto") === "1";
  sessionStorage.setItem("boostio:visita-iniciada","1");
} catch {}
const home = /\/index\.html$/.test(location.pathname) || document.body.id === "inicio";
const frequente = /\/(configuracao-build|pecas|peca)\.html$/.test(location.pathname);
const pesada = document.body.classList.contains("settings-page-body") || document.body.dataset.loading === "heavy";
const perfil = perfilLoading({home,visitada,frequente,cache,formulario:document.body.classList.contains("form-page")});
const reduzido = matchMedia("(prefers-reduced-motion: reduce)").matches;
if (!tela) {
  tela = document.createElement("div"); tela.id = "loading-screen"; document.body.prepend(tela);
}
tela.classList.add("loading-" + perfil.modo);
tela.style.setProperty("--loading-fade",perfil.fadeMs + "ms");
tela.setAttribute("aria-hidden","true");
document.body.classList.add("loading-active");
if (perfil.modo === "fade" || reduzido) { video?.pause(); video?.remove(); }
else if (video) video.playbackRate = perfil.velocidade;

let finalizada = false;
let encerrada = false;
function revelar() {
  if (encerrada) return;
  encerrada = true;
  tela.remove();
  document.body.classList.remove("loading-active");
  document.body.classList.add("page-ready");
  if (!home) iniciarEntradaPagina();
  document.dispatchEvent(new Event("boostio:page-ready"));
}
function liberar() {
  if (finalizada) return;
  finalizada = true;
  document.body.classList.remove("loading-active");
  tela.classList.add("loading-dismissed"); // Nunca captura cliques enquanto desaparece.
  const duracao = reduzido ? 0 : perfil.fadeMs;
  tela.addEventListener("transitionend",e => { if (e.target === tela && e.propertyName === "opacity") revelar(); });
  setTimeout(revelar,duracao + 80);
}
const domPronto = document.readyState === "loading"
  ? new Promise(resolve => document.addEventListener("DOMContentLoaded",resolve,{once:true}))
  : Promise.resolve();
domPronto.then(() => {
  iniciarUI();
  iniciarScrollReveal(document, "footer");
}).catch(erro => { console.warn("Falha ao iniciar os controles:",erro); liberar(); });
const esperar = ms => new Promise(resolve => setTimeout(resolve,ms));
const videoPronto = !video || perfil.modo === "fade" || reduzido ? Promise.resolve()
  : Promise.race([new Promise(resolve => {
      if (video.ended || video.error) return resolve();
      video.addEventListener("ended",resolve,{once:true});
      video.addEventListener("error",resolve,{once:true});
      video.play().catch(resolve);
    }),esperar(3500)]);
const conteudoPronto = domPronto.then(async () => {
  await (document.fonts?.ready || Promise.resolve());
  await aguardarCarregamentos();
  // Só o fluxo editor/catálogo/peça acelera quando pronto. A home permanece em 1×.
  if (frequente && video && perfil.modo === "full") video.playbackRate = perfil.velocidadePronta;
});
const limite = pesada ? 8000 : perfil.modo === "full" ? 5000 : 5000;
const seguranca = setTimeout(liberar,limite);
Promise.all([conteudoPronto,videoPronto,esperar(reduzido ? 0 : perfil.minimoMs)]).then(() => {
  clearTimeout(seguranca); liberar();
}).catch(erro => {
  console.warn("O carregamento terminou com uma falha recuperável:",erro);
  clearTimeout(seguranca); liberar();
});
window.addEventListener("pageshow",e => { if (e.persisted) { finalizada = true; revelar(); document.body.classList.remove("loading-active"); } });
