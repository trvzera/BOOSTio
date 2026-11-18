
import "../header.js";
import "../services-carousel.js";
import "../auth/auth.js";
import { login, confirmarAdmin } from "../api/usuario/login.js";
import { entrarComGoogle } from "../api/usuario/entrarComGoogle.js";

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const emailInput = document.querySelector("#email");
    const senhaInput = document.querySelector("#password");
    const botaoEntrar = document.querySelector("#btn-sign-in");
    const formLogin = document.querySelector("#login-form");
    const erroTexto = document.querySelector("#login-error");
    const botaoGoogle = document.querySelector("#btn-google-login");
    erroTexto.style.display = "none";


    const erroGoogle = new URLSearchParams(window.location.search).get("erro");
    if (erroGoogle) {
      erroTexto.style.display = "block";
      erroTexto.textContent = erroGoogle;
    }

    botaoGoogle.addEventListener("click", (e) => {
      e.preventDefault();
      entrarComGoogle();
    });

    document.querySelectorAll(".password-toggle").forEach((icone) => {
      icone.addEventListener("click", () => {
        const alvo = document.querySelector(`#${icone.dataset.target}`);
        const vendo = alvo.type === "text";

        alvo.type = vendo ? "password" : "text";
        icone.classList.toggle("fa-eye", !vendo);
        icone.classList.toggle("fa-eye-slash", vendo);
        icone.setAttribute("aria-pressed",String(!vendo));
        icone.setAttribute("aria-label",vendo ? "Mostrar senha" : "Ocultar senha");
      });
    });

    const fator = document.querySelector("#admin-factor");
    const codigo = document.querySelector("#admin-code");
    function mostrarAutenticador() {
      fator.hidden = false;
      codigo.disabled = false;
      codigo.required = true;
      emailInput.disabled = senhaInput.disabled = true;
      emailInput.style.display = senhaInput.parentElement.style.display = "none";
      senhaInput.value = "";
      botaoEntrar.textContent = "Confirmar código";
      botaoEntrar.setAttribute("aria-label", "Confirmar código");
      codigo.focus();
      validarFormulario();
    }

    function validarFormulario() {
      const camposPreenchidos =
        emailInput.value.trim() !== "" && senhaInput.value !== "";
      botaoEntrar.disabled = fator.hidden ? !camposPreenchidos : !/^[0-9]{6}$/.test(codigo.value);
    }

    emailInput.addEventListener("input", validarFormulario);
    senhaInput.addEventListener("input", validarFormulario);

    codigo.addEventListener("input", validarFormulario);
    if (new URLSearchParams(location.search).get("etapa") === "autenticador") mostrarAutenticador();
    validarFormulario();

    formLogin.addEventListener("submit", async (e) => {
      e.preventDefault();

      erroTexto.style.display = "none";
      erroTexto.textContent = "";

      const emailValue = emailInput.value.trim();
      const senhaValue = senhaInput.value.trim();

      botaoEntrar.disabled = true;
      botaoEntrar.dataset.busy = "true";

      try {
        const resposta = fator.hidden ? await login(emailValue, senhaValue) : await confirmarAdmin(codigo.value);
        if (resposta.segundo_fator) {
          mostrarAutenticador();
          return;
        }

        if (resposta.mensagem) {
          window.location.href = "./index.html";
          return;
        }
      } catch (erro) {
        console.error("Falha ao entrar:", erro);
        erroTexto.style.display = "block";
        erroTexto.textContent =
          erro.message ||
          "Não foi possível entrar. Tente novamente mais tarde.";
      } finally {
        delete botaoEntrar.dataset.busy;
        validarFormulario();
      }
    });
  } catch (erro) {
    console.error("Erro ao iniciar a página de login:", erro);
  }
});
