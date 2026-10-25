const CHAVE = "boostio:reduce-motion";
const ouvintes = new Set();
let manual = null;
let sistema, criarMedia;
function preferenciaSistema() {
  if (criarMedia !== globalThis.matchMedia && typeof globalThis.matchMedia === "function") {
    sistema?.removeEventListener?.("change", aplicar);
    criarMedia = globalThis.matchMedia;
    sistema = criarMedia("(prefers-reduced-motion: reduce)");
    sistema.addEventListener?.("change", aplicar);
  }
  return sistema;
}

export function resolverMovimentoReduzido(valor, sistemaReduzido = false) {
  return valor === "1" ? true : valor === "0" ? false : Boolean(sistemaReduzido);
}
export function movimentoReduzido() {
  return resolverMovimentoReduzido(manual, preferenciaSistema()?.matches);
}
export function observarMovimento(ouvinte) {
  ouvintes.add(ouvinte);
  return () => ouvintes.delete(ouvinte);
}
function aplicar() {
  const reduzido = movimentoReduzido();
  if (typeof document !== "undefined") {
    document.documentElement.dataset.reducedMotion = String(reduzido);
    if (reduzido) document.querySelectorAll("video").forEach(video => video.pause());
  }
  ouvintes.forEach(ouvinte => ouvinte(reduzido));
}
export function definirMovimentoReduzido(reduzido) {
  manual = reduzido ? "1" : "0";
  try { globalThis.localStorage?.setItem(CHAVE, manual); } catch { /* Preferência continua válida nesta página. */ }
  aplicar();
}
try { manual = globalThis.localStorage?.getItem(CHAVE) ?? null; } catch {}
globalThis.addEventListener?.("storage", evento => {
  if (evento.key !== CHAVE && evento.key !== null) return;
  manual = evento.newValue;
  aplicar();
});
aplicar();
