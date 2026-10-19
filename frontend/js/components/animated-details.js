const estados = new WeakMap();

function preparar(details) {
  if (estados.has(details)) return estados.get(details);
  const summary = details.querySelector("summary");
  if (!summary) return null;
  const estado = {summary,animacao:null,desejado:details.open};
  estados.set(details,estado);
  details.dataset.detailsReady = "true";
  summary.setAttribute("aria-expanded",String(details.open));
  details.addEventListener("toggle",() => {
    if (estado.animacao) return;
    estado.desejado = details.open;
    summary.setAttribute("aria-expanded",String(details.open));
  });
  summary.addEventListener("click",evento => {
    evento.preventDefault();
    definirDetalheAberto(details,!estado.desejado);
  });
  return estado;
}

// Também permite fechar por código sem deixar uma animação anterior reabrir o menu.
export function definirDetalheAberto(details,aberto,{animar = true} = {}) {
  const estado = preparar(details);
  if (!estado) return;
  const inicio = details.getBoundingClientRect().height;
  estado.animacao?.cancel();
  estado.animacao = null;
  estado.desejado = Boolean(aberto);
  estado.summary.setAttribute("aria-expanded",String(estado.desejado));
  delete details.dataset.animating;
  if (!animar || matchMedia("(prefers-reduced-motion: reduce)").matches || !details.animate) {
    details.open = estado.desejado;
    return;
  }
  // O JS mede a altura natural; duração e curva podem ser personalizadas no CSS.
  details.open = true;
  const estilo = getComputedStyle(details);
  const fechado = estado.summary.getBoundingClientRect().height + parseFloat(estilo.paddingTop) +
    parseFloat(estilo.paddingBottom) + parseFloat(estilo.borderTopWidth) + parseFloat(estilo.borderBottomWidth);
  const fim = estado.desejado ? details.getBoundingClientRect().height : fechado;
  const duracao = parseFloat(estilo.getPropertyValue("--details-duration"));
  const atual = details.animate({height:[inicio + "px",fim + "px"]},{
    duration:Number.isFinite(duracao) ? Math.max(0,duracao) : 300,
    easing:estilo.getPropertyValue("--details-easing").trim() || "cubic-bezier(.22,1,.36,1)",
  });
  estado.animacao = atual;
  details.dataset.animating = "true";
  atual.onfinish = () => {
    if (estado.animacao !== atual) return;
    details.open = estado.desejado;
    estado.animacao = null;
    delete details.dataset.animating;
  };
}

// Mantém o comportamento nativo do details, sem altura fixa nem listeners duplicados.
export function iniciarDetalhesAnimados(raiz = document) {
  raiz.querySelectorAll("details[data-animated-details]").forEach(preparar);
}
