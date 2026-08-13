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

export async function registrarAnimacao(id, path, opcoes = {}) {
  const container = document.querySelector(`#${id}`);

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

  animacoesCarregadas.set(id, animacao);
  return animacao;
}

export function obterAnimacao(id) {
  return animacoesCarregadas.get(id);
}

export function destruirTodas() {
  animacoesCarregadas.forEach((animacao) => animacao.destroy());
  animacoesCarregadas.clear();
}
