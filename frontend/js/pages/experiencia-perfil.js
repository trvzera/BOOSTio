import { carregarPerfil, perfilAtual } from "../conta/perfil.js";
import { preferenciasUso } from "../conta/preferencias-uso.js";
import { salvarPreferenciasDaConta } from "../conta/salvar-preferencias-uso.js";
import { acompanharCarregamento } from "../components/page-loading.js";

document.addEventListener("DOMContentLoaded",() => {
  const form = document.querySelector("#experience-profile-form");
  if (!form) return;
  const nivel = form.querySelector("#profile-hardware-level"), botao = form.querySelector('[type="submit"]');
  const rever = form.querySelector("#replay-tutorial"), feedback = form.querySelector("#experience-feedback");
  let usuarioId = null, ocupado = false, sujo = false;
  function bloquear(valor) {
    ocupado = valor; form.setAttribute("aria-busy",String(valor));
    nivel.disabled = valor || !usuarioId;rever.disabled = valor || !usuarioId;botao.disabled = valor;
    botao.dataset.disabledReason = valor ? "Aguarde a consulta ou o salvamento das preferências." : "";
    rever.dataset.disabledReason = valor ? "Aguarde o carregamento das preferências." : !usuarioId ? "Consulte sua conta novamente para rever o tutorial." : "";
    botao.textContent = valor ? "Aguarde…" : usuarioId ? "Salvar preferências" : "Tentar novamente";
    botao.setAttribute("aria-label",botao.textContent);
  }
  function sincronizar() {
    const perfil = perfilAtual();
    const proximo = perfil.auth ? perfil.usuario?.id : null;
    if (proximo !== usuarioId) sujo = false;
    usuarioId = proximo;
    if (!sujo) nivel.value = preferenciasUso(perfil.usuario).nivel_hardware || "";
    if (!ocupado) bloquear(false);
  }
  async function carregar() {
    bloquear(true);
    try { await carregarPerfil(); sincronizar(); }
    catch (erro) { feedback.textContent = erro.message;usuarioId = null; }
    finally { bloquear(false); }
  }
  document.addEventListener("boostio:experience-changed",sincronizar);
  nivel.addEventListener("change",() => { sujo = true; });
  form.addEventListener("submit",async evento => {
    evento.preventDefault();if (ocupado) return;
    if (!usuarioId) { await carregar(); return; }
    bloquear(true);feedback.textContent = "Salvando…";
    try {
      const escolhido = nivel.value || null;
      await salvarPreferenciasDaConta(usuarioId,{nivel_hardware:escolhido});
      sujo = false;
      feedback.textContent = "Preferências salvas na sua conta. Você pode mudar quando quiser.";
    } catch (erro) { feedback.textContent = erro.message; }
    finally { bloquear(false); }
  });
  rever.addEventListener("click",async () => {
    try { const {abrirTutorial} = await import("../components/onboarding.js");await abrirTutorial(); }
    catch (erro) { feedback.textContent = erro.message; }
  });
  acompanharCarregamento(carregar());
  window.addEventListener("pageshow",evento => { if (evento.persisted) acompanharCarregamento(carregar()); });
});
