// Entry point da página inicial (index.html).
import "../header.js";
import "../services-carousel.js";
import "../auth/auth.js";
import { iniciarScrollReveal } from "../components/scroll-reveal.js";

document.addEventListener("DOMContentLoaded", () => {
  iniciarScrollReveal();
  const videos = document.querySelectorAll(
    "#main-page video, #about-page video",
  );
  const visiveis = new Set();
  const movimentoReduzido = matchMedia("(prefers-reduced-motion: reduce)");
  const controleMovimento = document.querySelector(".video-motion-toggle");
  let pausado = movimentoReduzido.matches || Boolean(navigator.connection?.saveData);

  function atualizarControle() {
    const texto = pausado ? "Reproduzir animações" : "Pausar animações";
    const label = controleMovimento.querySelector("[data-motion-label]");
    if (label) label.textContent = texto;
    controleMovimento.setAttribute("aria-label",texto + " de fundo");
    controleMovimento.dataset.paused = String(pausado);
  }

  function atualizarReproducao() {
    videos.forEach((video) => {
      if (pausado || document.hidden || !visiveis.has(video)) {
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

  videos.forEach((video) => observador.observe(video));
  document.addEventListener("visibilitychange", atualizarReproducao);
  controleMovimento.addEventListener("click",() => { pausado = !pausado; atualizarControle(); atualizarReproducao(); });
  movimentoReduzido.addEventListener("change",evento => { pausado = evento.matches; atualizarControle(); atualizarReproducao(); });
  atualizarControle();
});
