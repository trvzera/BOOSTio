import { criar_usuario } from "./api/usuarios_api/usuarios_singin_api.js";

const nomeInput = document.querySelector("#nome-usuario");
const emailInput = document.querySelector("#email");
const senhaInput = document.querySelector("#senha1");
const confirmarSenhaInput = document.querySelector("#senha2");
const senhaMatchText = document.querySelector("#senha-match-text");
const termosCheck = document.querySelector("#terms");
const botaoCriarConta = document.querySelector("#btn-criar-conta");

const barra = document.querySelector(".barra");
const textoStatus = document.querySelector("#status-text");
const containerVerificacao = document.querySelector("#verificacao-senha");

const caracteres = document.querySelector("#caracteres");
const maiusculas = document.querySelector("#maiusculas");
const minusculas = document.querySelector("#minusculas");
const simbolos = document.querySelector("#simbolos");
const numeros = document.querySelector("#numeros");

let forcaSenha = 0;

senhaInput.addEventListener("focus", () => {
  containerVerificacao.classList.add("aberto");
});

senhaInput.addEventListener("blur", () => {
  if (senhaInput.value.length === 0) {
    containerVerificacao.classList.remove("aberto");
  }
});

senhaInput.addEventListener("input", compararSenha);
confirmarSenhaInput.addEventListener("input", () => {
  verificarSenhasIguais();
  validarFormulario();
});
nomeInput.addEventListener("input", validarFormulario);
emailInput.addEventListener("input", validarFormulario);
termosCheck.addEventListener("change", validarFormulario);

function atualizarClasse(elemento, condicao, vazio) {
  if (vazio) {
    elemento.classList.remove("certo", "errado");
    return;
  }
  elemento.classList.toggle("certo", condicao);
  elemento.classList.toggle("errado", !condicao);
}

function compararSenha() {
  const textoInput = senhaInput.value;
  const vazio = textoInput.length === 0;

  const regras = [
    { condicao: textoInput.length >= 8, elemento: caracteres },
    { condicao: /[A-Z]/.test(textoInput), elemento: maiusculas },
    { condicao: /[a-z]/.test(textoInput), elemento: minusculas },
    { condicao: /\d/.test(textoInput), elemento: numeros },
    { condicao: /[^a-zA-Z0-9]/.test(textoInput), elemento: simbolos },
  ];

  let total = 0;

  for (const regra of regras) {
    atualizarClasse(regra.elemento, regra.condicao, vazio);
    if (regra.condicao) total += 20;
  }

  forcaSenha = total;

  const cor = corValor(total);
  barra.style.width = `${total}%`;
  barra.style.backgroundColor = cor;
  textoStatus.style.color = cor;
  textoStatus.textContent = textoValor(total);

  verificarSenhasIguais();
  validarFormulario();
}

function verificarSenhasIguais() {
  const senha2Vazia = confirmarSenhaInput.value.length === 0;

  if (senha2Vazia) {
    senhaMatchText.textContent = "";
    senhaMatchText.classList.remove("igual", "diferente");
    return;
  }

  const iguais = senhaInput.value === confirmarSenhaInput.value;

  senhaMatchText.textContent = iguais
    ? "As senhas coincidem"
    : "As senhas não coincidem";
  senhaMatchText.classList.toggle("igual", iguais);
  senhaMatchText.classList.toggle("diferente", !iguais);
}

function corValor(total) {
  if (total === 0) return "var(--cor-4)";
  if (total <= 20) return "var(--cor-d1)";
  if (total <= 40) return "var(--cor-d2)";
  if (total <= 60) return "var(--cor-d3)";
  if (total <= 80) return "var(--cor-d4)";
  return "var(--cor-d5)";
}

function textoValor(total) {
  if (total === 0) return "VAZIA";
  if (total <= 20) return "FRACA";
  if (total <= 40) return "MÉDIA";
  if (total <= 60) return "BOA";
  if (total <= 80) return "ÓTIMA";
  return "FORTE";
}

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
    nomeInput.value.trim() !== "" &&
    emailInput.value.trim() !== "" &&
    senhaInput.value !== "" &&
    confirmarSenhaInput.value !== "";

  const senhaCompleta = forcaSenha === 100;
  const senhasIguais = senhaInput.value === confirmarSenhaInput.value;
  const termosAceitos = termosCheck.checked;

  botaoCriarConta.disabled = !(
    camposPreenchidos &&
    senhaCompleta &&
    senhasIguais &&
    termosAceitos
  );
}

validarFormulario();

const formCriarConta = document.querySelector("#signin-form");

formCriarConta.addEventListener("submit", async (e) => {
  e.preventDefault();

  const userValue = nomeInput.value.trim();
  const emailValue = emailInput.value.trim();
  const senhaValue = senhaInput.value.trim();

  botaoCriarConta.disabled = true;

  try {
    const resposta = await criar_usuario(userValue, emailValue, senhaValue);

    if (resposta.erro) {
      alert(resposta.erro);
      return;
    }

    if (resposta.mensagem) {
      window.location.href = "./login.html";
    }
  } catch (erro) {
    console.error("Falha ao criar conta:", erro);
    alert("Não foi possível criar a conta. Tente novamente mais tarde.");
  } finally {
    botaoCriarConta.disabled = false;
  }
});