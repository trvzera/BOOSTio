export function iniciarEntradaPagina() {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const seletores = "#main-title, #main-description, #main-page > .btn-primary, .builder-heading, .catalog-toolbar, .product-detail-layout, .builds-header, .builds-quota-card, .settings-header, .developers-hero, .terms-header, .error-card, #login-container, #signin-container, #forgot-password-container, #reset-password-container, #forms-header, #question-info, #question-content";
  [...document.querySelectorAll(seletores)].filter(el => {
    const r = el.getBoundingClientRect();
    return r.width && r.height && r.top < innerHeight && r.bottom > 0;
  }).slice(0,6).forEach((elemento,indice) => {
    elemento.style.setProperty("--entry-delay",indice * 70 + "ms");
    elemento.classList.add("page-entry");
    const limpar = () => elemento.classList.remove("page-entry");
    elemento.addEventListener("animationend",limpar,{once:true});
    setTimeout(limpar,1100 + indice * 70);
  });
}
