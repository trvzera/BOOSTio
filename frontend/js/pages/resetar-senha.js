import "../header.js";
import { redefinirSenha } from "../api/usuario/redefinirSenha.js";

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");

  const form = document.querySelector("#resetar-senha-form");
  const containerSucesso = document.querySelector("#resetar-senha-sucesso");
  const containerInvalido = document.querySelector("#resetar-senha-invalido");

  if (!token) {
    form.classList.add("oculto");
    containerInvalido.classList.remove("oculto");
    return;
  }

  const senhaInput = document.querySelector("#senha1");
  const confirmarSenhaInput = document.querySelector("#senha2");
  const senhaMatchText = document.querySelector("#senha-match-text");
  senhaMatchText.style.display = "none";
  const botaoRedefinir = document.querySelector("#btn-redefinir-senha");
  const erroTexto = document.querySelector("#resetar-senha-erro");

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
      senhaMatchText.style.display = "none";
      senhaMatchText.textContent = "";
      senhaMatchText.classList.remove("igual", "diferente");
      return;
    }

    const iguais = senhaInput.value === confirmarSenhaInput.value;
    senhaMatchText.style.display = "block";
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

      form.classList.add("oculto");
      containerSucesso.classList.remove("oculto");
    } catch (erro) {
      console.error("Falha ao redefinir senha:", erro);
      erroTexto.textContent =
        erro.message || "Não foi possível redefinir a senha. Tente novamente.";
      botaoRedefinir.disabled = false;
    }
  });
});