// Entry point da página de criação de conta (pages/signin.html).
import "../header.js";
import "../services-carousel.js";
import "../auth/auth.js";
import { criarUsuario } from "../api/usuario/criarUsuario.js";
import { entrarComGoogle } from "../api/usuario/entrarComGoogle.js";
import { enviarEmailVerificar } from "../api/email/enviarEmailVerificar.js";
import { conferirEmailVerificar } from "../api/email/conferirEmailVerificar.js";
import { iniciarFluxoVerificacaoEmail } from "../components/verification-flow.js";
import {
  registrarAnimacao,
  destruirTodas,
} from "../components/lottie-controller.js";


document.addEventListener("DOMContentLoaded", async () => {
  try {
    const nomeInput = document.querySelector("#username");
    const emailInput = document.querySelector("#email");
    const senhaInput = document.querySelector("#primary-password");
    const confirmarSenhaInput = document.querySelector("#confirm-password");
    const senhaMatchText = document.querySelector("#password-match-text");
    senhaMatchText.style.display = "none";
    const termosCheck = document.querySelector("#terms");
    const botaoCriarConta = document.querySelector("#btn-create-account");
    const erroTexto = document.querySelector("#sign-up-error");
    erroTexto.style.display = "none";
    const botaoGoogle = document.querySelector("#btn-google-login");

    botaoGoogle.addEventListener("click", (e) => {
      e.preventDefault();
      entrarComGoogle();
    });
    const barra = document.querySelector(".strength-meter-bar");
    const textoStatus = document.querySelector("#status-text");
    const containerVerificacao = document.querySelector("#password-verification");

    const caracteres = document.querySelector("#password-length-rule");
    const maiusculas = document.querySelector("#uppercase-rule");
    const minusculas = document.querySelector("#lowercase-rule");
    const simbolos = document.querySelector("#symbol-rule");
    const numeros = document.querySelector("#number-rule");

    let ltCheck;
    registrarAnimacao(
      "terms-checkbox-animation",
      "../lottie/checkbox.json",
    ).then(animacao => {
      ltCheck = animacao;
      const pronto = () => {
        document.querySelector("#terms-checkbox-animation").setAttribute("data-ready", "");
        ltCheck?.goToAndStop(termosCheck.checked ? ltCheck.totalFrames - 1 : 0, true);
      };
      if (ltCheck?.isLoaded) pronto(); else ltCheck?.addEventListener("DOMLoaded",pronto);
    }).catch(() => {});

    termosCheck.addEventListener("click", () => {
      if (termosCheck.checked) {
        ltCheck?.setDirection(1);
        ltCheck?.play();
      } else {
        ltCheck?.setDirection(-1);
        ltCheck?.play();
      }
    });
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
    nomeInput.addEventListener("input", validarFormulario);
    emailInput.addEventListener("input", validarFormulario);
    termosCheck.addEventListener("change", validarFormulario);

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
        icone.setAttribute("aria-pressed",String(!vendo));
        const campo = icone.dataset.target === "confirm-password" ? "confirmação da senha" : "senha";
        icone.setAttribute("aria-label", (vendo ? "Mostrar " : "Ocultar ") + campo);
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

    // --- Modal de verificação de e-mail ---
    const modalVerificacao = document.querySelector("#verify-email-modal");
    const fluxoVerificacao = iniciarFluxoVerificacaoEmail({
      modal:modalVerificacao,enviar:enviarEmailVerificar,confirmar:conferirEmailVerificar,
      aoConfirmar:()=>{ window.location.href="./index.html"; },
    });
    const abrirModalVerificacao=usuario=>fluxoVerificacao.abrir(usuario);
    window.addEventListener("pagehide",()=>fluxoVerificacao.destruir(),{once:true});
    document.querySelector("#btn-verify-later").addEventListener("click",()=>{
      fluxoVerificacao.fechar();window.location.href="./index.html";
    });

    const formCriarConta = document.querySelector("#signin-form");

    formCriarConta.addEventListener("submit", async (e) => {
      e.preventDefault();

      erroTexto.textContent = "";
      erroTexto.style.display = "none";

      const userValue = nomeInput.value.trim();
      const emailValue = emailInput.value.trim();
      const senhaValue = senhaInput.value.trim();

      botaoCriarConta.disabled = true;
      botaoCriarConta.dataset.busy = "true";

      try {
        const resposta = await criarUsuario(userValue, emailValue, senhaValue);

        if (resposta.mensagem) {
          abrirModalVerificacao(resposta.usuario);
          return;
        }
      } catch (erro) {
        erroTexto.style.display = "block";
        console.error("Falha ao criar conta:", erro);
        erroTexto.textContent =
          erro.message ||
          "Não foi possível criar a conta. Tente novamente mais tarde.";
      } finally {
        delete botaoCriarConta.dataset.busy;
        botaoCriarConta.disabled = false;
      }
    });
  } catch (erro) {
    console.error("Erro ao iniciar a página de criação de conta:", erro);
  }
});
