// Mantém o comportamento nativo do details e anima abertura e fechamento.
export function iniciarDetalhesAnimados(raiz = document) {
  raiz.querySelectorAll("details[data-animated-details]").forEach(details => {
    if (details.dataset.detailsReady) return;
    details.dataset.detailsReady = "true";
    const summary = details.querySelector("summary");
    let animacao, desejado = details.open;
    summary.setAttribute("aria-expanded", String(desejado));
    details.addEventListener("toggle", () => {
      if (!animacao) { desejado = details.open; summary.setAttribute("aria-expanded", String(desejado)); }
    });
    summary.addEventListener("click", evento => {
      evento.preventDefault();
      desejado = !desejado;
      const inicio = details.getBoundingClientRect().height;
      animacao?.cancel();
      summary.setAttribute("aria-expanded", String(desejado));
      if (matchMedia("(prefers-reduced-motion: reduce)").matches || !details.animate) {
        animacao = null; delete details.dataset.animating; details.open = desejado; return;
      }
      // Mede o tamanho natural já aberto; o conteúdo fica disponível ao teclado.
      details.open = true;
      const estilo = getComputedStyle(details);
      const fechado = summary.getBoundingClientRect().height + parseFloat(estilo.paddingTop) +
        parseFloat(estilo.paddingBottom) + parseFloat(estilo.borderTopWidth) + parseFloat(estilo.borderBottomWidth);
      const fim = desejado ? details.getBoundingClientRect().height : fechado;
      const atual = details.animate({height:[inicio + "px",fim + "px"]}, {
        duration:300,easing:"cubic-bezier(.22,1,.36,1)",
      });
      animacao = atual;
      details.dataset.animating = "true";
      atual.onfinish = () => {
        if (animacao !== atual) return;
        details.open = desejado;
        animacao = null; delete details.dataset.animating;
      };
    });
  });
}
