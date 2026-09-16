import "../header.js";
import { solicitarRecuperacaoSenha } from "../api/usuario/solicitarRecuperacaoSenha.js";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#forgot-password-form");
  const emailInput = document.querySelector("#email");
  const botaoEnviar = document.querySelector("#btn-send-link");
  const erroTexto = document.querySelector("#forgot-password-error");
  erroTexto.style.display = "none";

  const containerSucesso = document.querySelector("#forgot-password-success");
  const emailConfirmado = document.querySelector("#email-confirmed");

  function validarFormulario() {
    botaoEnviar.disabled = emailInput.value.trim() === "";
  }

  emailInput.addEventListener("input", validarFormulario);
  validarFormulario();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    erroTexto.style.display = "none";
    erroTexto.textContent = "";

    const emailValue = emailInput.value.trim();
    botaoEnviar.disabled = true;

    try {
      await solicitarRecuperacaoSenha(emailValue);

      emailConfirmado.textContent = emailValue;
      form.classList.add("hidden");
      containerSucesso.classList.remove("hidden");
    } catch (erro) {
      console.error("Falha ao solicitar recuperação de senha:", erro);
      erroTexto.style.display = "block";
      erroTexto.textContent =
        erro.message ||
        "Não foi possível enviar o link. Tente novamente mais tarde.";
      botaoEnviar.disabled = false;
    }
  });
});
