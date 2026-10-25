// Entry point da página inicial (index.html).
import "../header.js";
import "../services-carousel.js";
import "../auth/auth.js";
import { iniciarScrollReveal } from "../components/scroll-reveal.js";
import { movimentoReduzido, observarMovimento } from "../components/motion-preference.js";

document.addEventListener("DOMContentLoaded", () => {
  iniciarScrollReveal();
  const videos = document.querySelectorAll(
    "#main-page video, #about-page video",
  );
  const visiveis = new Set();

  function atualizarReproducao() {
    videos.forEach((video) => {
      if (movimentoReduzido() || navigator.connection?.saveData || document.hidden || !visiveis.has(video)) {
        video.pause();
      } else if (video.paused) {
        const source = video.querySelector("source[data-src]");
        if (source) { source.src = source.dataset.src; source.removeAttribute("data-src"); video.load(); }
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

  // Retoma quando volta à tela; fora dela não consome reprodução. O menu permite
  // manter apenas os posters, inclusive nos próximos acessos.
  videos.forEach((video) => {
    video.loop = true;
    observador.observe(video);
  });
  observarMovimento(reduzido => {
    if (reduzido) videos.forEach(video => {
      video.pause();
      video.querySelectorAll("source[src]").forEach(source => {
        source.dataset.src = source.getAttribute("src");
        source.removeAttribute("src");
      });
      video.load(); // Retira os frames e mantém a imagem estática do poster.
    });
    atualizarReproducao();
  });
  document.addEventListener("visibilitychange", atualizarReproducao);
  navigator.connection?.addEventListener("change", atualizarReproducao);
});
