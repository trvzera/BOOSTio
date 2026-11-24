import { movimentoReduzido } from "./motion-preference.js";

export function criarFundoFormulario(video) {
  if (!video) return () => {};

  video.addEventListener("playing", () => video.setAttribute("data-playing", ""));
  for (const evento of ["pause", "ended", "error"]) {
    video.addEventListener(evento, () => video.removeAttribute("data-playing"));
  }

  return function reproduzirFundo() {
    if (movimentoReduzido()) return;
    video.currentTime = 0;
    void video.play().catch(() => {});
  };
}
