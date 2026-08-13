import lottie from "https://cdn.skypack.dev/lottie-web";

const animacoesCarregadas = new Map();

export function registrarAnimacao(id, path, opcoes = {}) {
  const container = document.querySelector(`#${id}`);

  if (!container) {
    console.warn(`Container #${id} não encontrado.`);
    return null;
  }

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
