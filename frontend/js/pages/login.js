// Entry point da página de login (pages/login.html).
import "../header.js";
import "../services-carousel.js";
import "../auth/auth.js";
import { login } from "../api/usuario/login.js";

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const emailInput = document.querySelector("#email");
    const senhaInput = document.querySelector("#senha");
    const botaoEntrar = document.querySelector("#btn-entrar");
    const formLogin = document.querySelector("#login-form");
    const erroTexto = document.querySelector("#login-erro");

    document.querySelectorAll(".toggle-senha").forEach((icone) => {
      icone.addEventListener("click", () => {
        const alvo = document.querySelector(`#${icone.dataset.target}`);
        const vendo = alvo.type === "text";

        alvo.type = vendo ? "password" : "text";
        icone.classList.toggle("fa-eye", !vendo);
        icone.classList.toggle("fa-eye-slash", vendo);
      });
    });

    function validarFormulario() {
      const camposPreenchidos =
        emailInput.value.trim() !== "" && senhaInput.value !== "";
      botaoEntrar.disabled = !camposPreenchidos;
    }

    emailInput.addEventListener("input", validarFormulario);
    senhaInput.addEventListener("input", validarFormulario);

    validarFormulario();

    formLogin.addEventListener("submit", async (e) => {
      e.preventDefault();

      erroTexto.textContent = "";

      const emailValue = emailInput.value.trim();
      const senhaValue = senhaInput.value.trim();

      botaoEntrar.disabled = true;

      try {
        const resposta = await login(emailValue, senhaValue);

        if (resposta.mensagem) {
          window.location.href = "./index.html";
          return;
        }
      } catch (erro) {
        console.error("Falha ao entrar:", erro);
        erroTexto.textContent =
          erro.message || "Não foi possível entrar. Tente novamente mais tarde.";
      } finally {
        botaoEntrar.disabled = false;
      }
    });
  } catch (erro) {
    console.error("Erro ao iniciar a página de login:", erro);
  }
});
