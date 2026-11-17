import { conteudoApresentacao, passosApresentacao } from "../components/onboarding-content.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";

export function abrirPreviaTutorial(tipo = "curto",origem = document.activeElement) {
  if (tipo !== "curto" || document.querySelector(".test-onboarding-dialog[open]")) return;
  let passo = 0, nivel = "";
  const dialogo = document.createElement("dialog");
  dialogo.className = "onboarding-dialog test-onboarding-dialog";
  dialogo.setAttribute("aria-labelledby","tutorial-preview-title");
  dialogo.setAttribute("aria-describedby","tutorial-preview-description");
  function desenhar() {
    const ultimo = passo === passosApresentacao.length - 1;
    dialogo.innerHTML = '<div class="onboarding-top"><span class="onboarding-progress">Prévia · apresentação · '+(passo+1)+' de '+passosApresentacao.length+'</span><button type="button" class="build-action-close" data-tutorial-action="fechar" aria-label="Fechar prévia do tutorial">×</button></div><div class="onboarding-content">'+conteudoApresentacao(passo,nivel,{previa:true})+'</div><div class="onboarding-actions"><button type="button" class="onboarding-skip" data-tutorial-action="fechar" aria-label="Pular prévia do tutorial">Pular prévia</button><div class="onboarding-steps">'+(passo ? '<button type="button" class="btn-secondary" data-tutorial-action="voltar" aria-label="Voltar ao passo anterior">'+iconeAnimado("arrow","back")+'Voltar</button>' : '')+'<button type="button" class="btn-primary" data-tutorial-action="avancar" aria-label="Avançar ou concluir a prévia">'+(ultimo ? 'Concluir prévia' : 'Continuar')+iconeAnimado("arrow")+'</button></div></div>';
    iniciarIcones(dialogo);
    dialogo.querySelector("h2").focus({preventScroll:true});
    dialogo.querySelector(".onboarding-content").scrollTop = 0;
  }
  dialogo.addEventListener("change",evento => { if (evento.target.name === "tutorial-preview-level") nivel = evento.target.value; });
  dialogo.addEventListener("click",evento => {
    const acao = evento.target.closest("[data-tutorial-action]")?.dataset.tutorialAction;
    if (acao === "fechar" || acao === "avancar" && passo === passosApresentacao.length - 1) { dialogo.close(); return; }
    if (acao === "avancar") passo++;
    else if (acao === "voltar" && passo > 0) passo--;
    else return;
    desenhar();
  });
  dialogo.addEventListener("close",() => { dialogo.remove(); if (origem?.isConnected) origem.focus({preventScroll:true}); },{once:true});
  document.body.append(dialogo); dialogo.showModal(); desenhar();
}

document.querySelectorAll("[data-preview-onboarding]").forEach(botao => {
  botao.addEventListener("click",() => abrirPreviaTutorial(botao.dataset.previewOnboarding,botao));
});
