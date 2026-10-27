import { preferenciasUso, niveisHardware, tutorialPendente } from "../conta/preferencias-uso.js";
import { perfilAtual } from "../conta/perfil.js";
import { salvarPreferenciasDaConta } from "../conta/salvar-preferencias-uso.js";
import { htmlSeguro as h } from "../build/catalogo.js";
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
  try { sessionStorage.setItem(chave(id),"visto"); } catch { /* A preferência principal fica na conta. */ }
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

  const conteudo = () => passo === 0
    ? '<h2 id="onboarding-title" tabindex="-1">Qual é seu nível de conhecimento sobre peças de computador?</h2><p>Conte o quanto você já conhece sobre as peças e a montagem de um PC. Você pode atualizar essa informação no perfil quando quiser.</p>' +
      '<fieldset class="onboarding-levels"><legend class="sr-only">Seu conhecimento sobre peças de computador (opcional)</legend>' + niveisHardware.map(([valor,nome,descricao]) =>
        '<label class="onboarding-level"><input type="radio" name="onboarding-level" value="' + valor + '"' + (nivel === valor ? ' checked' : '') + '><span><strong>' + h(nome) + '</strong><span>' + h(descricao) + '</span></span></label>').join("") + '</fieldset><p>Não precisa escolher agora. Todas as ferramentas ficam disponíveis em qualquer nível.</p>'
    : passo === 1
      ? '<h2 id="onboarding-title" tabindex="-1">Duas formas de montar seu PC</h2><p>Quando for montar sua build, você poderá escolher entre duas opções.</p><ul class="onboarding-list"><li><h3>Montagem inteligente</h3><p>Responda sobre seu uso, quanto pode gastar e o que já possui. A BOOSTio sugere as peças para você.</p></li><li><h3>Montagem manual</h3><p>Escolha peça por peça no catálogo e acompanhe o preço e os avisos de compatibilidade.</p></li></ul><p>Para criar uma build, confirme seu e-mail. Se já tiver três builds salvas, será preciso liberar um espaço.</p>'
      : '<h2 id="onboarding-title" tabindex="-1">Acompanhe e guarde sua montagem</h2><ul class="onboarding-list"><li><h3>Preço e compatibilidade</h3><p>Veja o total das peças e o consumo estimado. Confira os avisos e os itens ainda não verificados. O frete não entra no total.</p></li><li><h3>Minhas builds</h3><p>As alterações são salvas na conta. Pelo perfil, acesse suas builds para comparar, buscar melhorias ou compartilhar as públicas.</p></li><li><h3>Seu orçamento e seu perfil</h3><p>Em Configurações, registre seu orçamento, atualize seu nível de conhecimento ou reveja este tutorial.</p></li></ul>';

  function desenhar() {
    dialogo.innerHTML = '<div class="onboarding-top"><span class="onboarding-progress">Conheça a BOOSTio · ' + (passo+1) + ' de 3</span><button type="button" class="build-action-close" data-onboarding="fechar" aria-label="Fechar tutorial">×</button></div>' +
      '<div class="onboarding-content">' + conteudo() + '</div><p class="onboarding-feedback" role="status" aria-live="polite"></p><div class="onboarding-actions"><button type="button" class="onboarding-skip" data-onboarding="pular" aria-label="Pular tutorial">Pular tutorial</button><div class="onboarding-steps">' +
      (passo ? '<button type="button" class="btn-secondary" data-onboarding="voltar" aria-label="Voltar ao passo anterior do tutorial">Voltar</button>' : '') + '<button type="button" class="btn-primary" data-onboarding="avancar" aria-label="' + (passo === 2 ? 'Concluir tutorial' : 'Avançar no tutorial') + '">' + (passo === 2 ? 'Concluir' : 'Avançar') + '</button></div></div>';
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
  dialogo.addEventListener("change",evento => { if (evento.target.name === "onboarding-level") { nivel = evento.target.value; nivelAlterado = true; } });
  dialogo.addEventListener("click",async evento => {
    const acao = evento.target.closest("[data-onboarding]")?.dataset.onboarding;
    if (["pular","fechar"].includes(acao)) { pular(); return; }
    if (ocupado || !acao) return;
    if (acao === "voltar") { passo--; desenhar(); return; }
    if (acao !== "avancar") return;
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
    }
  });
  const sessao = () => { if (!perfilAtual().auth || perfilAtual().usuario?.id !== usuarioId || automatico && !tutorialPendente(perfilAtual().usuario)) fechar(); };
  document.addEventListener("boostio:experience-changed",sessao);
  dialogo.addEventListener("close",() => document.removeEventListener("boostio:experience-changed",sessao),{once:true});
  document.body.append(dialogo);desenhar();dialogo.showModal();dialogo.querySelector("h2").focus({preventScroll:true});
}
