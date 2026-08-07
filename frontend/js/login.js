// Atenção: usei resposta.token porque é o padrão mais comum, mas não sei o formato real da resposta do seu endpoint /usuarios/entrar ainda. Quando implementar esse retorno no backend, ajuste esse campo pro nome exato que a API devolve.

import { logar_usuario } from "./api/usuarios_api/usuario_login_api.js";
import { setToken } from "./auth.js";

const emailInput = document.querySelector("#email");
const senhaInput = document.querySelector("#senha");
const botaoEntrar = document.querySelector("#btn-entrar");
const formLogin = document.querySelector("#login-form");

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
  const camposPreenchidos = emailInput.value.trim() !== "" && senhaInput.value !== "";
  botaoEntrar.disabled = !camposPreenchidos;
}

emailInput.addEventListener("input", validarFormulario);
senhaInput.addEventListener("input", validarFormulario);

validarFormulario();

formLogin.addEventListener("submit", async (e) => {
  e.preventDefault();

  const emailValue = emailInput.value.trim();
  const senhaValue = senhaInput.value.trim();

  botaoEntrar.disabled = true;

  try {
    const resposta = await logar_usuario(emailValue, senhaValue);

    if (resposta.erro) {
      alert(resposta.erro);
      return;
    }

    if (resposta.token) {
      setToken(resposta.token);
      window.location.href = "../index.html";
    }
  } catch (erro) {
    console.error("Falha ao entrar:", erro);
    alert("Não foi possível entrar. Tente novamente mais tarde.");
  } finally {
    botaoEntrar.disabled = false;
  }
});