const efeitos = {
  avancar: { url: new URL("../../../audios/avancarFORMS.wav", import.meta.url).href, volume: 0.33 },
  finalizar: { url: new URL("../../../audios/finalizarBUILD.wav", import.meta.url).href, volume: 0.50 },
};

export function criarSonsFormulario() {
  let contexto;
  try {
    contexto = new AudioContext();
  } catch {
    return () => {};
  }

  const sons = new Map();
  for (const [efeito, { url, volume }] of Object.entries(efeitos)) {
    const ganho = contexto.createGain();
    ganho.gain.value = volume;
    ganho.connect(contexto.destination);

    const som = { ganho, buffer: null };
    som.carregamento = fetch(url)
      .then(async (resposta) => {
        if (resposta.ok) som.buffer = await contexto.decodeAudioData(await resposta.arrayBuffer());
      })
      .catch(() => {});
    sons.set(efeito, som);
  }

  return function tocar(efeito) {
    const som = sons.get(efeito);
    if (contexto.state !== "running") void contexto.resume().catch(() => {});

    function reproduzir() {
      if (!som.buffer) return;
      const fonte = contexto.createBufferSource();
      fonte.buffer = som.buffer;
      fonte.connect(som.ganho);
      fonte.addEventListener("ended", () => fonte.disconnect(), { once: true });
      fonte.start();
    }

    if (som.buffer) reproduzir();
    else void som.carregamento.then(reproduzir);
  };
}
