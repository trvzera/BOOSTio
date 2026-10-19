import { htmlSeguro as h } from "./catalogo.js";
let aberto, fechamentoExternoIniciado = false;

export function indicadorBuild(resultado,id) {
  const dicas = resultado.dicas || [];
  const faltam = resultado.faltam.map(p => "Falta adicionar: " + p + ".");
  const pendencias = [...resultado.erros,...faltam,...resultado.avisos,...dicas];
  const problemas = resultado.erros.length + faltam.length + resultado.avisos.length;
  const tom = resultado.erros.length ? "erro" : problemas ? "aviso" : "ok";
  const nome = tom === "erro" ? "Ver incompatibilidades" : problemas ? "Ver pendências da build" : "Ver dicas da build";
  return '<div class="compatibility-popover build-indicator ' + tom + '">' +
    (pendencias.length ? '<button type="button" class="compatibility-trigger" aria-label="' + nome + '" aria-controls="' + h(id) + '" aria-expanded="false"></button>' +
      '<div id="' + h(id) + '" class="compatibility-details glass-card" role="region" aria-label="Compatibilidade da build" aria-hidden="true" inert>' +
      '<h3>' + (problemas ? 'O que precisa de atenção' : 'Dicas para conferir') + '</h3><ul class="compatibility-messages">' + pendencias.map((texto,i) => '<li class="' + (i < resultado.erros.length ? 'error' : i < problemas ? 'warning' : 'tip') + '">' + h(texto) + '</li>').join("") +
      '</ul></div>'
      : '<span class="compatibility-marker" aria-label="Sem conflitos detectados"></span>') + '</div>';
}
export function iniciarIndicadores(raiz) {
  if (!fechamentoExternoIniciado) {
    fechamentoExternoIniciado = true;
    document.addEventListener("pointerdown",e => { if (aberto && !aberto.box.contains(e.target)) aberto.fechar(); });
  }
  raiz.querySelectorAll(".build-indicator").forEach(box => {
    const botao = box.querySelector("button"), painel = box.querySelector(".compatibility-details");
    if (!botao) return;
    let fixo = false;
    const mostrar = aberto => {
      box.toggleAttribute("data-open",aberto);
      botao.setAttribute("aria-expanded",String(aberto));
      painel.setAttribute("aria-hidden",String(!aberto)); painel.inert = !aberto;
    };
    const fechar = () => { fixo = false; mostrar(false); };
    const abrir = () => { if (aberto?.box !== box) aberto?.fechar(); aberto = {box,fechar}; mostrar(true); };
    box.addEventListener("pointerenter",e => { if (e.pointerType !== "touch") abrir(); });
    box.addEventListener("pointerleave",() => { if (!fixo && !box.contains(document.activeElement)) mostrar(false); });
    box.addEventListener("focusin",abrir);
    box.addEventListener("focusout",e => { if (!box.contains(e.relatedTarget)) { fixo = false; mostrar(false); } });
    botao.onclick = e => { e.stopPropagation(); fixo = !fixo; if (fixo) abrir(); else mostrar(false); };
    box.addEventListener("keydown",e => {
      if (e.key === "Escape") { e.stopPropagation(); fixo = false; botao.focus(); mostrar(false); }
    });
  });
}
