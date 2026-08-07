
const containerProfile = document.querySelector("#profile");
const profileCheck = document.querySelector("#profile-check");
import { logar_usuario } from "./api/usuarios_api/usuario_login_api.js";

document.addEventListener("click", (e) => {
  if (!containerProfile.contains(e.target)) {
    profileCheck.checked = false;
  }
});


const emailInput = document.querySelector("#email");
const senhaInput = document.querySelector("#senha");
const botaoEntrar = document.querySelector("#btn-entrar");

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


formCriarConta.addEventListener("submit", async (e) => {
  e.preventDefault();

  const emailValue = emailInput.value.trim();
  const senhaValue = senhaInput.value.trim();

  botaoCriarConta.disabled = true;

  try {
    const resposta = await criar_usuario(emailValue, senhaValue);

    if (resposta.erro) {
      alert(resposta.erro);
      return;
    }

    if (resposta.mensagem){
      window.location.href = "../pages/configuracoes.html";
    }

  } catch (erro) {
    console.error("Falha ao criar conta:", erro);
    alert("Não foi possível criar a conta. Tente novamente mais tarde.");
  } finally {
    botaoCriarConta.disabled = false;
  }
});