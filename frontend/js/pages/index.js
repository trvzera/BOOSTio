// Entry point da página inicial (index.html).
import "../header.js";
import "../services-carousel.js";
import "../auth/auth.js";

document.addEventListener("DOMContentLoaded", () => {
  const videos = document.querySelectorAll(
    "#main-page video, #about-page video",
  );
  const visiveis = new Set();

  function atualizarReproducao() {
    videos.forEach((video) => {
      if (document.hidden || !visiveis.has(video)) {
        video.pause();
      } else if (video.paused) {
        video.play().catch(() => {});
      }
    });
  }

  const observador = new IntersectionObserver(
    (entradas) => {
      entradas.forEach(({ target, isIntersecting }) => {
        if (isIntersecting) visiveis.add(target);
        else visiveis.delete(target);
      });
      atualizarReproducao();
    },
    { threshold: 0.05 },
  );

  videos.forEach((video) => observador.observe(video));
  document.addEventListener("visibilitychange", atualizarReproducao);
});
