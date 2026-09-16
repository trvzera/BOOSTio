document.body.classList.add("loading-active");

const loadingScreen = document.querySelector("#loading-screen");
const loadingVideo = document.querySelector("#loading-video");

function esconderLoading() {
  loadingScreen.classList.add("loading-dismissed");
  document.body.classList.remove("loading-active");

  loadingScreen.addEventListener(
    "transitionend",
    () => loadingScreen.remove(),
    { once: true },
  );
}

loadingVideo.addEventListener("ended", esconderLoading);

setTimeout(esconderLoading, 2500);