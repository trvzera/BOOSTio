import { carregarPerfil, atualizarPerfil, limparPerfil, revisaoPerfil } from "../conta/perfil.js";
import { atualizarBudgetUsuario } from "../api/usuario/atualizarBudgetUsuario.js";
import { acompanharCarregamento } from "../components/page-loading.js";
import { moeda } from "../build/catalogo.js";

document.addEventListener("DOMContentLoaded",() => {
  const form = document.querySelector("#budget-profile-form");
  if (!form) return;
  const input = form.querySelector("#profile-budget"), usar = form.querySelector("#profile-budget-use");
  const feedback = form.querySelector("#profile-budget-feedback"), botao = form.querySelector("button[type=submit]");
  let usuarioId = null, ocupado = false;
  const aviso = (mensagem,tom) => { feedback.textContent = mensagem; feedback.dataset.tone = tom; };
  function autorizarUso() {
    const positivo = input.value !== "" && input.validity.valid && Number(input.value) > 0;
    usar.disabled = ocupado || !usuarioId || !positivo;
    if (!positivo) usar.checked = false;
  }
  function bloquear(valor) {
    ocupado = valor;
    form.setAttribute("aria-busy",String(valor));
    input.disabled = valor || !usuarioId;
    botao.disabled = valor;
    botao.dataset.disabledReason = valor ? "Aguarde a consulta ou o salvamento do budget." : "";
    botao.textContent = valor ? "Aguarde…" : usuarioId ? "Salvar budget" : "Tentar novamente";
    botao.setAttribute("aria-label",botao.textContent);
    autorizarUso();
  }
  async function carregar() {
    usuarioId = null; input.value = ""; usar.checked = false;
    bloquear(true);
    try {
      const resposta = await carregarPerfil();
      if (!resposta?.auth || !resposta.usuario) throw new Error("Entre na sua conta para configurar o budget.");
      usuarioId = resposta.usuario.id;
      input.value = resposta.usuario.budget ?? "";
      usar.checked = resposta.usuario.usar_budget === true;
      aviso("Budget sincronizado com sua conta.","info");
    } catch (erro) {
      usuarioId = null; input.value = ""; usar.checked = false;
      aviso(erro.message || "Não foi possível carregar o budget. Tente novamente.","error");
    } finally { bloquear(false); }
  }
  input.addEventListener("input",autorizarUso);
  form.addEventListener("submit",async evento => {
    evento.preventDefault();
    if (ocupado) return;
    if (!usuarioId) { await carregar(); return; }
    if (!form.reportValidity()) return;
    const budget = input.value.trim() === "" ? null : Number(input.value), permitido = usar.checked, versao = revisaoPerfil();
    bloquear(true);
    try {
      const resposta = await atualizarBudgetUsuario(usuarioId,budget,permitido);
      if (resposta?.usuario?.id !== usuarioId) throw new Error("Resposta inválida ao salvar o budget. Recarregue a página.");
      if (!atualizarPerfil(resposta.usuario,versao)) {
        usuarioId = null; input.value = ""; usar.checked = false;
        throw new Error("A sessão mudou durante o salvamento. Consulte o budget novamente.");
      }
      aviso(budget == null ? "Budget removido da sua conta." : moeda(budget) + " salvos na sua conta. O valor não é descontado automaticamente.","success");
    } catch (erro) {
      if ([401,403].includes(erro.status)) { limparPerfil(); usuarioId = null; input.value = ""; usar.checked = false; }
      aviso(erro.message || "Não foi possível salvar o budget. Tente novamente.","error");
    } finally { bloquear(false); }
  });
  acompanharCarregamento(carregar());
  window.addEventListener("pageshow",evento => { if (evento.persisted) acompanharCarregamento(carregar()); });
});
