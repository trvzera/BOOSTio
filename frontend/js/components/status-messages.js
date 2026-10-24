// Uma mensagem contextual após a pausa, não um anúncio por movimento do controle.
// A fila pura permite testar o tempo/deduplicação sem DOM nem leitor de tela.
export function criarAnunciadorStatus({publicar, agendar = setTimeout, cancelar = clearTimeout}) {
  let timer, ultima = "";
  const limpar = (reiniciar = false) => {
    cancelar(timer); timer = undefined;
    if (reiniciar) ultima = "";
  };
  return {
    cancelar: limpar,
    anunciar(texto, {urgente = false, atraso = urgente ? 50 : 700} = {}) {
      limpar();
      const mensagem = String(texto ?? "").trim();
      const chave = String(urgente) + ":" + mensagem;
      if (!mensagem || chave === ultima) return;
      timer = agendar(() => {
        timer = undefined;
        if (publicar(mensagem, urgente) !== false) ultima = chave;
      }, Math.max(50, Number.isFinite(atraso) ? atraso : 700));
    },
  };
}

const porRaiz = new WeakMap(), ativos = new Set();
let observarSaida = false;
const raizAtiva = () => [...document.querySelectorAll("dialog[open]")].at(-1) || document.body;

function obterAnunciador(raiz) {
  if (porRaiz.has(raiz)) return porRaiz.get(raiz);
  // As regiões vazias existem antes da alteração de texto. Ficam dentro do modal
  // ativo para não serem tornadas inertes pelo showModal(). Nunca recebem foco.
  const regioes = ["status", "alert"].map(papel => {
    const regiao = document.createElement("div");
    regiao.className = "sr-only";
    regiao.dataset.statusAnnouncer = papel;
    regiao.setAttribute("role", papel);
    regiao.setAttribute("aria-live", papel === "alert" ? "assertive" : "polite");
    regiao.setAttribute("aria-atomic", "true");
    raiz.append(regiao);
    return regiao;
  });
  const anunciador = criarAnunciadorStatus({publicar(texto, urgente) {
    if (!raiz.isConnected || raiz !== raizAtiva()) return false;
    regioes[urgente ? 0 : 1].textContent = "";
    regioes[urgente ? 1 : 0].textContent = texto;
  }});
  porRaiz.set(raiz, anunciador); ativos.add(anunciador);
  if (raiz.tagName === "DIALOG") raiz.addEventListener("close", () => {
    anunciador.cancelar(); ativos.delete(anunciador); porRaiz.delete(raiz);
    regioes.forEach(regiao => regiao.remove());
  }, {once:true});
  if (!observarSaida) {
    observarSaida = true;
    window.addEventListener("pagehide", () => ativos.forEach(item => item.cancelar()));
  }
  return anunciador;
}

export function anunciarStatus(texto, opcoes = {}) {
  obterAnunciador(raizAtiva()).anunciar(texto, opcoes);
}

export function cancelarAnuncioStatus({reiniciar = false} = {}) {
  const raiz = raizAtiva();
  porRaiz.get(raiz)?.cancelar(reiniciar);
  if (reiniciar) raiz.querySelectorAll(":scope > [data-status-announcer]").forEach(regiao => regiao.textContent = "");
}
