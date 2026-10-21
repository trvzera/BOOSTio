let iniciada = false, sequencia = 0;
export function iniciarModaisAcessiveis() {
  if (iniciada) return;
  iniciada = true;
  const estados = new WeakMap();
  const focaveis = modal => [...modal.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]')]
    .filter(item => !item.closest("[inert]") && item.getClientRects().length && getComputedStyle(item).visibility !== "hidden");
  function sincronizar(modal) {
    const caixa = modal.querySelector(".modal-box");
    if (!caixa) return;
    let estado = estados.get(modal);
    if (!estado) {
      estado = {aberto:false,anterior:null}; estados.set(modal,estado);
      caixa.setAttribute("role","dialog"); caixa.setAttribute("aria-modal","true"); caixa.tabIndex = -1;
      const titulo = caixa.querySelector("h1,h2,h3");
      if (titulo) { titulo.id ||= "modal-title-" + (++sequencia); caixa.setAttribute("aria-labelledby",titulo.id); }
      else caixa.setAttribute("aria-label","Janela de confirmação");
      modal.addEventListener("keydown",evento => {
        if (!estado.aberto) return;
        if (evento.key === "Escape") {
          evento.preventDefault(); evento.stopPropagation();
          const fechar = modal.querySelector('[id*="cancel"],[id*="close"],[id*="later"],[data-ui-close]');
          if (fechar) fechar.click(); else modal.classList.remove("open");
        } else if (evento.key === "Tab") {
          const itens = focaveis(modal), primeiro = itens[0], ultimo = itens.at(-1);
          if (!primeiro) { evento.preventDefault(); caixa.focus(); }
          else if (evento.shiftKey && (document.activeElement === primeiro || document.activeElement === caixa)) { evento.preventDefault(); ultimo.focus(); }
          else if (!evento.shiftKey && document.activeElement === ultimo) { evento.preventDefault(); primeiro.focus(); }
        }
      });
    }
    const aberto = modal.classList.contains("open");
    modal.inert = !aberto; modal.setAttribute("aria-hidden",String(!aberto));
    if (aberto && !estado.aberto) {
      estado.anterior = document.activeElement;
      queueMicrotask(() => { if (modal.classList.contains("open")) (focaveis(modal)[0] || caixa).focus(); });
    } else if (!aberto && estado.aberto && estado.anterior?.isConnected) estado.anterior.focus({preventScroll:true});
    estado.aberto = aberto;
  }
  const atualizar = () => document.querySelectorAll(".modal-overlay").forEach(sincronizar);
  atualizar();
  new MutationObserver(registros => {
    if (registros.some(r => r.type === "childList" || r.target.matches?.(".modal-overlay"))) atualizar();
  }).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:["class"]});
}
