const efeitos = {
  avancar: { url: new URL("../../../audios/avancarFORMS.wav", import.meta.url).href, volume: 0.38 },
  finalizar: { url: new URL("../../../audios/finalizarBUILD.wav", import.meta.url).href, volume: 0.56 },
};

export function criarSonsFormulario() {
  const sons = new Map();
  for (const [efeito, { url, volume }] of Object.entries(efeitos)) {
    const audio = new Audio(url);
    audio.preload = "auto";
    audio.volume = volume;
    sons.set(efeito, audio);
  }

  return function tocar(efeito) {
    const principal = sons.get(efeito);
    const audio = principal.paused && !principal.error ? principal : new Audio(principal.src);
    audio.volume = principal.volume;
    audio.currentTime = 0;
    void audio.play().catch((erro) => {
      console.warn("Falha ao reproduzir o som do formulário.", erro);
    });
  };
}
