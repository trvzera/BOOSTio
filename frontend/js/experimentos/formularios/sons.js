const efeitos = {
  avancar: { url: new URL("../../../audios/avancarFORMS.wav", import.meta.url).href, volume: 0.45 },
  finalizar: { url: new URL("../../../audios/finalizarBUILD.wav", import.meta.url).href, volume: 0.65 },
};

export function criarSonsFormulario() {
  let audio;
  let contexto;
  let ganho;

  return function tocar(efeito) {
    const { url, volume } = efeitos[efeito];

    if (!audio) {
      audio = new Audio();
      try {
        contexto = new AudioContext();
        ganho = contexto.createGain();
        ganho.connect(contexto.destination);
        contexto.createMediaElementSource(audio).connect(ganho);
      } catch {
        ganho = null;
      }
    }

    audio.pause();
    if (audio.src === url) audio.currentTime = 0;
    else audio.src = url;

    if (ganho) {
      ganho.gain.value = volume;
      if (contexto.state !== "running") void contexto.resume().catch(() => {});
    } else {
      audio.volume = volume;
    }

    void audio.play().catch(() => {});
  };
}
