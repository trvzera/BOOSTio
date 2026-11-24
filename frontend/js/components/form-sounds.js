const efeitos = {
  avancar: new URL("../../audios/avancar-formulario-suave.mp3?v=3", import.meta.url).href,
  finalizar: new URL("../../audios/concluir-formulario-suave.mp3?v=3", import.meta.url).href,
};

export function criarSonsFormulario() {
  const sons = new Map();
  for (const [efeito, url] of Object.entries(efeitos)) {
    const audio = new Audio(url);
    audio.preload = "auto";
    sons.set(efeito, audio);
  }

  return function tocar(efeito) {
    const principal = sons.get(efeito);
    const audio = principal.paused && !principal.error ? principal : new Audio(principal.src);
    audio.currentTime = 0;
    void audio.play().catch((erro) => {
      console.warn("Falha ao reproduzir o som do formulário.", erro);
    });
  };
}
