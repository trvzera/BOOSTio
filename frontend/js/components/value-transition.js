const animacoes = new WeakMap(), ativas = new Set();
let preferencia;
const numeroValido = valor => typeof valor === "number" && Number.isFinite(valor);
const lerValor = elemento => ({texto:elemento.textContent, numero:elemento.dataset.valueNumber == null ? null : Number(elemento.dataset.valueNumber)});

function movimentoReduzido() {
  if (!preferencia && typeof globalThis.matchMedia === "function") {
    preferencia = globalThis.matchMedia("(prefers-reduced-motion: reduce)");
    preferencia.addEventListener?.("change",evento => {
      if (evento.matches) for (const animacao of ativas) animacao.cancel();
    });
  }
  return preferencia?.matches;
}

// O número correto aparece imediatamente. Só sua apresentação é animada;
// não interpola preços nem duplica o texto lido por leitores de tela.
export function atualizarValor(elemento, texto, numero, anterior = elemento && lerValor(elemento)) {
  if (!elemento) return;
  elemento.classList.add("value-transition");
  if (elemento.textContent !== String(texto)) elemento.textContent = texto;
  if (numeroValido(numero)) elemento.dataset.valueNumber = String(numero);
  else delete elemento.dataset.valueNumber;
  if (movimentoReduzido()) { animacoes.get(elemento)?.cancel(); return; }
  if (!anterior || anterior.texto === String(texto) || !numeroValido(anterior.numero) ||
      !numeroValido(numero) || anterior.numero === numero || typeof elemento.animate !== "function") return;
  // Arrastar o slider não reinicia/empilha uma animação a cada evento de input.
  if (animacoes.has(elemento)) return;
  const distancia = numero > anterior.numero ? ".45em" : "-.45em";
  const animacao = elemento.animate([
    {opacity:.2,transform:`translateY(${distancia})`,filter:"blur(4px)"},
    {opacity:1,transform:"translateY(0)",filter:"blur(0px)"},
  ],{duration:360,easing:"cubic-bezier(.22,1,.36,1)"});
  animacoes.set(elemento,animacao); ativas.add(animacao);
  const limpar = () => {
    ativas.delete(animacao);
    if (animacoes.get(elemento) === animacao) animacoes.delete(elemento);
  };
  animacao.finished.then(limpar,limpar);
}

// Chaves estáveis preservam o valor anterior quando o editor recria seus cards.
export function capturarValores(raiz) {
  return new Map([...raiz.querySelectorAll("[data-value-key]")].map(elemento => [elemento.dataset.valueKey,lerValor(elemento)]));
}
export function transicionarValores(raiz, anteriores) {
  raiz.querySelectorAll("[data-value-key]").forEach(elemento => {
    const atual = lerValor(elemento);
    atualizarValor(elemento,atual.texto,atual.numero,anteriores.get(elemento.dataset.valueKey));
  });
}
