import { iniciarTratamentoGlobalDeErros } from "../components/error-handler.js";

iniciarTratamentoGlobalDeErros();

document.body.classList.add("loading-active");

const loadingScreen = document.querySelector("#loading-screen");
const loadingVideo = document.querySelector("#loading-video");
let loadingEncerrado = false;

function esconderLoading() {
  if (loadingEncerrado) return;
  loadingEncerrado = true;
  loadingScreen.classList.add("loading-dismissed");
  document.body.classList.remove("loading-active");

  loadingScreen.addEventListener(
    "transitionend",
    () => loadingScreen.remove(),
    { once: true },
  );
}

const videoPronto = new Promise((resolve) => {
  if (loadingVideo.ended) {
    resolve();
    return;
  }

  loadingVideo.addEventListener("ended", resolve, { once: true });
  loadingVideo.addEventListener("error", resolve, { once: true });
});

const fontesProntas = document.fonts?.ready || Promise.resolve();
const tempoMaximo = new Promise((resolve) => setTimeout(resolve, 2500));

Promise.race([
  Promise.all([videoPronto, fontesProntas]),
  tempoMaximo,
]).then(esconderLoading);
