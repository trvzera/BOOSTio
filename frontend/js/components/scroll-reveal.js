const observados = new Map();
let observador;
// Um único observador atende também os cards renderizados pelo JS.
export function iniciarScrollReveal(raiz = document, seletor = "[data-reveal]") {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches ||
      !("IntersectionObserver" in window)) return;
  observador ??= new IntersectionObserver((entradas) => {
    entradas.forEach(({ target, isIntersecting }) => {
      target.classList.toggle("is-visible", isIntersecting);
    });
  }, { threshold: 0.12, rootMargin: "60px 0px -32px 0px" });
  raiz.querySelectorAll(seletor).forEach((elemento) => {
    if (observados.has(elemento)) return;
    observados.set(elemento,true);
    elemento.style.setProperty("--reveal-delay", elemento.dataset.revealDelay || "0ms");
    elemento.classList.add("reveal-pending");
    const rect = elemento.getBoundingClientRect();
    elemento.classList.toggle("is-visible",rect.bottom > 0 && rect.top < innerHeight - 32);
    observador.observe(elemento);
  });
  for (const elemento of observados.keys()) if (!elemento.isConnected) { observador.unobserve(elemento); observados.delete(elemento); }
  return observador;
}
export function iniciarRevealsGlobais() {
  const seletores = "[data-reveal], footer, .component-group, .build-summary, .build-card, .settings-card, .developer-card, .developers-section-heading, .product-card, .product-stores, .product-specifications, .terms-clause, #questions, #login-container, #signin-container, #forgot-password-container, #reset-password-container, .error-card, .form-manual-build";
  const atualizar = () => iniciarScrollReveal(document,seletores);
  atualizar();
  let agendado = false;
  new MutationObserver(() => {
    if (agendado) return;
    agendado = true;
    requestAnimationFrame(() => { agendado = false; atualizar(); });
  }).observe(document.body,{childList:true,subtree:true});
}
