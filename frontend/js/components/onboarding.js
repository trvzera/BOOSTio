import { preferenciasUso, tutorialPendente, nivelHardwareValido } from "../conta/preferencias-uso.js";
import { perfilAtual } from "../conta/perfil.js";
import { salvarPreferenciasDaConta } from "../conta/salvar-preferencias-uso.js";
import { conteudoApresentacao } from "./onboarding-content.js";
import { iconeAnimado, iniciarIcones } from "./ui.js";
import { avisar } from "../build/interface.js";

const vistos = new Set();
let dialogoAtivo = null, agendado = false;
const chave = id => "boostio:tutorial-v1:" + id;
function jaVisto(id) {
  try { return vistos.has(id) || sessionStorage.getItem(chave(id)) === "visto"; }
  catch { return vistos.has(id); }
}
function marcarVisto(id) {
  vistos.add(id);
  try { sessionStorage.setItem(chave(id),"visto"); } catch {   }
}
function telaLivre() {
  return document.body.classList.contains("page-ready") &&
    !document.querySelector('dialog[open], .modal-overlay.open, .modal-overlay.active, .modal-overlay.show');
}
export function oferecerTutorial(usuario) {
  if (agendado || dialogoAtivo || !tutorialPendente(usuario) || jaVisto(usuario.id)) return;
  agendado = true;
  const limpar = () => { observador.disconnect(); window.removeEventListener("pagehide",limpar); agendado = false; };
  const verificar = () => {
    const atual = perfilAtual();
    if (!atual.auth || atual.usuario?.id !== usuario.id) { limpar(); return; }
    if (!telaLivre()) return;
    limpar();
    if (tutorialPendente(atual.usuario)) abrirTutorial({automatico:true}).catch(() => {});
  };
  const observador = new MutationObserver(verificar);
  observador.observe(document.body,{attributes:true,childList:true,subtree:true,attributeFilter:["class","open"]});
  window.addEventListener("pagehide",limpar,{once:true});
  verificar();
}

export async function abrirTutorial({automatico = false} = {}) {
  if (dialogoAtivo) { dialogoAtivo.querySelector("h2")?.focus(); return; }
  const atual = perfilAtual();
  if (!atual.auth || !atual.usuario) throw new Error("Entre na sua conta para abrir o tutorial.");
  if (!telaLivre()) throw new Error("Feche a janela aberta antes de rever o tutorial.");
  const usuarioId = atual.usuario.id, origem = document.activeElement;
  let passo = 0, nivel = preferenciasUso(atual.usuario).nivel_hardware, nivelAlterado = false, ocupado = false;
  const dialogo = document.createElement("dialog");
  dialogo.className = "onboarding-dialog";
  dialogo.setAttribute("aria-labelledby","onboarding-title");
  dialogoAtivo = dialogo;
  marcarVisto(usuarioId);

  const conteudo = () => conteudoApresentacao(passo,nivel);

  function atualizarAvanco() {
    const botao = dialogo.querySelector('[data-onboarding="avancar"]');
    const faltaNivel = passo === 0 && !nivelHardwareValido(nivel);
    botao.disabled = ocupado || faltaNivel;
    if (faltaNivel) botao.dataset.disabledReason = "Escolha seu nível de conhecimento ou pule o tutorial.";
    else delete botao.dataset.disabledReason;
  }

  function desenhar() {
    dialogo.innerHTML = '<div class="onboarding-top"><span class="onboarding-progress">Conheça a BOOSTio · ' + (passo+1) + ' de 3</span><button type="button" class="build-action-close" data-onboarding="fechar" aria-label="Fechar tutorial">×</button></div>' +
      '<div class="onboarding-content">' + conteudo() + '</div><p class="onboarding-feedback" role="status" aria-live="polite"></p><div class="onboarding-actions"><button type="button" class="onboarding-skip" data-onboarding="pular" aria-label="Pular tutorial">Pular tutorial</button><div class="onboarding-steps">' +
      (passo ? '<button type="button" class="btn-secondary" data-onboarding="voltar" aria-label="Voltar ao passo anterior do tutorial">' + iconeAnimado("arrow","back") + 'Voltar</button>' : '') + '<button type="button" class="btn-primary" data-onboarding="avancar" aria-label="' + (passo === 2 ? 'Concluir tutorial' : 'Avançar no tutorial') + '">' + (passo === 2 ? 'Concluir' : 'Continuar') + iconeAnimado("arrow") + '</button></div></div>';
    iniciarIcones(dialogo);
    atualizarAvanco();
    dialogo.querySelector("h2").focus({preventScroll:true});
    dialogo.querySelector(".onboarding-content").scrollTop = 0;
  }
  function fechar() {
    if (!dialogo.isConnected) return;
    dialogo.close(); dialogo.remove(); dialogoAtivo = null;
    if (origem?.isConnected && !origem.closest('[inert],[hidden]')) origem.focus({preventScroll:true});
  }
  function pular() {
    fechar();
    if (!ocupado) void salvarPreferenciasDaConta(usuarioId,{tutorial:"pulado",...(nivelAlterado ? {nivel_hardware:nivel} : {})}).catch(erro => {
      if (perfilAtual().usuario?.id === usuarioId) avisar(erro.message + " Você pode rever o tutorial nas configurações.");
    });
  }
  dialogo.addEventListener("cancel",evento => { evento.preventDefault(); pular(); });
  dialogo.addEventListener("change",evento => { if (evento.target.name === "onboarding-level") { nivel = nivelHardwareValido(evento.target.value) ? evento.target.value : null; nivelAlterado = true; atualizarAvanco(); } });
  dialogo.addEventListener("click",async evento => {
    const acao = evento.target.closest("[data-onboarding]")?.dataset.onboarding;
    if (["pular","fechar"].includes(acao)) { pular(); return; }
    if (ocupado || !acao) return;
    if (acao === "voltar") { passo--; desenhar(); return; }
    if (acao !== "avancar") return;
    if (!nivelHardwareValido(nivel)) { passo = 0; desenhar(); return; }
    if (passo < 2) { passo++; desenhar(); return; }
    ocupado = true;dialogo.setAttribute("aria-busy","true");
    dialogo.querySelectorAll('.onboarding-steps button').forEach(b => { b.dataset.disabledReason = "Aguarde a confirmação do salvamento."; b.disabled = true; });
    const feedback = dialogo.querySelector(".onboarding-feedback");
    feedback.textContent = "Salvando suas preferências…";
    try {
      await salvarPreferenciasDaConta(usuarioId,{nivel_hardware:nivel,tutorial:"concluido"});
      fechar();avisar("Tudo pronto! Você pode rever o tutorial nas configurações.");
    } catch (erro) {
      if (!dialogo.isConnected) { if (perfilAtual().usuario?.id === usuarioId) avisar(erro.message); return; }
      feedback.textContent = erro.message;feedback.dataset.tone = "error";
    } finally {
      ocupado = false;dialogo.removeAttribute("aria-busy");
      dialogo.querySelectorAll('.onboarding-steps button').forEach(b => { b.disabled = false; delete b.dataset.disabledReason; });
      atualizarAvanco();
    }
  });
  const sessao = () => { if (!perfilAtual().auth || perfilAtual().usuario?.id !== usuarioId || automatico && !tutorialPendente(perfilAtual().usuario)) fechar(); };
  document.addEventListener("boostio:experience-changed",sessao);
  dialogo.addEventListener("close",() => document.removeEventListener("boostio:experience-changed",sessao),{once:true});
  document.body.append(dialogo);desenhar();dialogo.showModal();dialogo.querySelector("h2").focus({preventScroll:true});
}
