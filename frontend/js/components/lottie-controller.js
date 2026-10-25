import { movimentoReduzido, observarMovimento } from "./motion-preference.js";

let lottiePromise = null;

function carregarLottie() {
  if (!lottiePromise) {
    lottiePromise =
      import("https://cdn.jsdelivr.net/npm/lottie-web@5.12.2/+esm").then(
        (mod) => mod.default,
      );
  }
  return lottiePromise;
}

const animacoesCarregadas = new Map();
observarMovimento(reduzido => {
  if (reduzido) animacoesCarregadas.forEach(animacao => animacao.pause());
});

export async function registrarAnimacao(id, path, opcoes = {}) {
  const container = document.getElementById(id);

  if (!container) {
    console.warn(`Container #${id} não encontrado.`);
    return null;
  }

  const lottie = await carregarLottie();

  const animacao = lottie.loadAnimation({
    container,
    renderer: "svg",
    loop: false,
    autoplay: false,
    path,
    ...opcoes,
  });

  const reproduzir = animacao.play.bind(animacao);
  animacao.play = (...argumentos) => {
    if (movimentoReduzido()) {
      animacao.goToAndStop(animacao.playDirection < 0 ? 0 : animacao.totalFrames - 1, true);
      return;
    }
    return reproduzir(...argumentos);
  };

  animacoesCarregadas.set(id, animacao);
  return animacao;
}

export function obterAnimacao(id) {
  return animacoesCarregadas.get(id);
}

export function destruirAnimacao(id, animacao) {
  if (animacoesCarregadas.get(id) !== animacao) return;
  animacao.destroy();
  animacoesCarregadas.delete(id);
}

export function destruirTodas() {
  animacoesCarregadas.forEach((animacao) => animacao.destroy());
  animacoesCarregadas.clear();  
}
