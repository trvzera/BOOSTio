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
  const encerrados = new WeakSet();
  const movimentoReduzido = matchMedia("(prefers-reduced-motion: reduce)");
  let pausado = movimentoReduzido.matches || Boolean(navigator.connection?.saveData);

  function atualizarReproducao() {
    videos.forEach((video) => {
      if (pausado || document.hidden || !visiveis.has(video) || encerrados.has(video)) {
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

  // Sem botão de pausa, a decoração não fica em loop: no máximo cinco segundos
  // de reprodução por vídeo. Movimento reduzido/economia de dados mantêm o poster.
  videos.forEach((video) => {
    let prazo;
    const encerrar = () => { encerrados.add(video); clearTimeout(prazo); video.pause(); };
    video.addEventListener("playing",() => {
      clearTimeout(prazo);
      if (encerrados.has(video)) { video.pause(); return; }
      prazo = setTimeout(encerrar,Math.max(0,5 - video.currentTime) * 1000);
    });
    video.addEventListener("pause",() => clearTimeout(prazo));
    video.addEventListener("ended",encerrar);
    video.addEventListener("timeupdate",() => { if (video.currentTime >= 5) encerrar(); });
    observador.observe(video);
  });
  document.addEventListener("visibilitychange", atualizarReproducao);
  movimentoReduzido.addEventListener("change",evento => { pausado = evento.matches || Boolean(navigator.connection?.saveData); atualizarReproducao(); });
});
