import "../header.js";
import { redefinirSenha } from "../api/usuario/redefinirSenha.js";

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");

  const form = document.querySelector("#reset-password-form");
  const containerSucesso = document.querySelector("#reset-password-success");
  const containerInvalido = document.querySelector("#reset-password-invalid");

  if (!token) {
    form.classList.add("hidden");
    containerInvalido.classList.remove("hidden");
    return;
  }

  const senhaInput = document.querySelector("#primary-password");
  const confirmarSenhaInput = document.querySelector("#confirm-password");
  const senhaMatchText = document.querySelector("#password-match-text");
  senhaMatchText.style.display = "none";
  const botaoRedefinir = document.querySelector("#btn-reset-password");
  const erroTexto = document.querySelector("#reset-password-error");

  const barra = document.querySelector(".strength-meter-bar");
  const textoStatus = document.querySelector("#status-text");
  const containerVerificacao = document.querySelector("#password-verification");

  const caracteres = document.querySelector("#password-length-rule");
  const maiusculas = document.querySelector("#uppercase-rule");
  const minusculas = document.querySelector("#lowercase-rule");
  const simbolos = document.querySelector("#symbol-rule");
  const numeros = document.querySelector("#number-rule");

  let forcaSenha = 0;

  senhaInput.addEventListener("focus", () => {
    containerVerificacao.classList.add("open");
  });

  senhaInput.addEventListener("blur", () => {
    if (senhaInput.value.length === 0) {
      containerVerificacao.classList.remove("open");
    }
  });

  senhaInput.addEventListener("input", compararSenha);
  confirmarSenhaInput.addEventListener("input", () => {
    verificarSenhasIguais();
    validarFormulario();
  });

  function atualizarClasse(elemento, condicao, vazio) {
    if (vazio) {
      elemento.classList.remove("valid", "invalid");
      return;
    }
    elemento.classList.toggle("valid", condicao);
    elemento.classList.toggle("invalid", !condicao);
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
      senhaMatchText.style.display = "none";
      senhaMatchText.textContent = "";
      senhaMatchText.classList.remove("matching", "mismatched");
      return;
    }

    const iguais = senhaInput.value === confirmarSenhaInput.value;
    senhaMatchText.style.display = "block";
    senhaMatchText.textContent = iguais
      ? "As senhas coincidem"
      : "As senhas não coincidem";
    senhaMatchText.classList.toggle("matching", iguais);
    senhaMatchText.classList.toggle("mismatched", !iguais);
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

  document.querySelectorAll(".password-toggle").forEach((icone) => {
    icone.addEventListener("click", () => {
      const alvo = document.querySelector(`#${icone.dataset.target}`);
      const vendo = alvo.type === "text";

      alvo.type = vendo ? "password" : "text";
      icone.classList.toggle("fa-eye", !vendo);
      icone.classList.toggle("fa-eye-slash", vendo);
    });
  });

  function validarFormulario() {
    const camposPreenchidos = senhaInput.value !== "" && confirmarSenhaInput.value !== "";
    const senhaCompleta = forcaSenha === 100;
    const senhasIguais = senhaInput.value === confirmarSenhaInput.value;

    botaoRedefinir.disabled = !(camposPreenchidos && senhaCompleta && senhasIguais);
  }

  validarFormulario();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    erroTexto.textContent = "";
    const novaSenha = senhaInput.value.trim();
    botaoRedefinir.disabled = true;

    try {
      await redefinirSenha(token, novaSenha);

      form.classList.add("hidden");
      containerSucesso.classList.remove("hidden");
    } catch (erro) {
      console.error("Falha ao redefinir senha:", erro);
      erroTexto.textContent =
        erro.message || "Não foi possível redefinir a senha. Tente novamente.";
      botaoRedefinir.disabled = false;
    }
  });
});