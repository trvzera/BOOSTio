let lottiePromise = null;
const dadosPorUrl = new Map();

function carregarLottie() {
  if (!lottiePromise) {
    // A distribuição SVG Light do lottie-web 5.13.0 expõe o player globalmente.
    lottiePromise = import("../vendor/lottie-web/lottie_light.min.js")
      .then(() => globalThis.lottie);
  }
  return lottiePromise;
}

function carregarDados(path) {
  const url = new URL(path, document.baseURI).href;
  if (!dadosPorUrl.has(url)) {
    dadosPorUrl.set(url, fetch(url).then(resposta => {
      if (!resposta.ok) throw new Error(`Não foi possível carregar a animação (${resposta.status}).`);
      return resposta.json();
    }).catch(erro => {
      dadosPorUrl.delete(url);
      throw erro;
    }));
  }
  return dadosPorUrl.get(url);
}

const animacoesCarregadas = new Map();

export async function registrarAnimacao(id, path, opcoes = {}) {
  const container = document.getElementById(id);

  if (!container) {
    console.warn(`Container #${id} não encontrado.`);
    return null;
  }

  const [lottie, dados] = await Promise.all([carregarLottie(), carregarDados(path)]);
  if (!container.isConnected || document.getElementById(id) !== container) return null;

  const animacao = lottie.loadAnimation({
    container,
    renderer: "svg",
    loop: false,
    autoplay: false,
    // Cada instância pode alterar seus dados internos durante a renderização.
    animationData: structuredClone(dados),
    ...opcoes,
  });

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
