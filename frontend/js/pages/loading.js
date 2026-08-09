document.body.classList.add("carregando");

const loadingScreen = document.querySelector("#loading-screen");
const loadingVideo = document.querySelector("#loading-video");

function esconderLoading() {
  loadingScreen.classList.add("escondido");
  document.body.classList.remove("carregando");

  loadingScreen.addEventListener(
    "transitionend",
    () => loadingScreen.remove(),
    { once: true },
  );
}

loadingVideo.addEventListener("ended", esconderLoading);

setTimeout(esconderLoading, 2500);