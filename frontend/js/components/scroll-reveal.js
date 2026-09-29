// A classe é retirada ao sair da viewport, como no portfólio.
export function iniciarScrollReveal(raiz = document, seletor = "[data-reveal]") {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches ||
      !("IntersectionObserver" in window)) return;
  const observer = new IntersectionObserver((entradas) => {
    entradas.forEach(({ target, isIntersecting }) => {
      target.classList.toggle("is-visible", isIntersecting);
    });
  }, { threshold: 0.12, rootMargin: "60px 0px -32px 0px" });
  raiz.querySelectorAll(seletor).forEach((elemento) => {
    elemento.style.setProperty("--reveal-delay", elemento.dataset.revealDelay || "0ms");
    elemento.classList.add("reveal-pending");
    observer.observe(elemento);
  });
  return observer;
}
