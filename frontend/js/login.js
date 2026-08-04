
const containerProfile = document.querySelector("#profile");
const profileCheck = document.querySelector("#profile-check");

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