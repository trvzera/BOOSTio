// Entry point da página de configurações (pages/configuracoes.html):
// edição de perfil, troca de senha e exclusão de conta.
import "../header.js";
import "../services-carousel.js";
import { caminhoLogin } from "../auth/auth.js";
import { buscarUsuarioLogado } from "../api/usuario/buscarUsuarioLogado.js";
import { atualizarUsuario } from "../api/usuario/atualizarUsuario.js";
import { deletarUsuario } from "../api/usuario/deletarUsuario.js";
import { formatarMesAno } from "../utils/formatarData.js";
import { enviarEmailVerificar } from "../api/email/enviarEmailVerificar.js";
import { conferirEmailVerificar } from "../api/email/conferirEmailVerificar.js";

const SEGUNDOS_REENVIO = 30;

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const toast = document.getElementById("toast");
    const toastText = document.getElementById("toast-text");
    const toastIcon = document.getElementById("toast-icon");
    function showToast(message, icon) {
      toastText.textContent = message;
      toast.classList.add("show");
      if (icon == true) {
        toastIcon.style.display = "block";
      } else {
        toastIcon.style.display = "none";
      }
      setTimeout(() => toast.classList.remove("show"), 2600);
    }

    const emailInput = document.getElementById("email-input");
    const displayUsername = document.getElementById("display-username");
    const confirmUsernameTarget = document.getElementById(
      "confirm-username-target",
    );

    emailInput.addEventListener("input", () => {
      emailInput.classList.toggle(
        "invalido",
        emailInput.value.length > 0 && !emailInput.checkValidity(),
      );
    });

    document.querySelectorAll(".toggle-password").forEach((btn) => {
      btn.addEventListener("click", () => {
        const input = document.getElementById(btn.dataset.target);
        const icon = btn.querySelector("i");
        const isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";
        icon.classList.toggle("fa-eye");
        icon.classList.toggle("fa-eye-slash");
      });
    });

    const currentPassword = document.getElementById("current-password");
    const newPassword = document.getElementById("new-password");
    const confirmPassword = document.getElementById("confirm-password");
    const strengthBars = document.querySelectorAll(".strength-bar");
    const matchHint = document.getElementById("password-match-hint");
    const savePasswordBtn = document.getElementById("save-password-btn");

    function checkPasswordStrength(value) {
      let score = 0;
      if (value.length >= 8) score++;
      if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score++;
      if (/\d/.test(value) && /[^A-Za-z0-9]/.test(value)) score++;
      return score; // 0 a 3
    }

    function updateStrengthBars(score) {
      const filledBars = newPassword.value.length > 0 ? Math.max(score, 1) : 0;
      const levelClass = ["weak", "weak", "medium", "strong"][score];

      strengthBars.forEach((bar, i) => {
        bar.className = "strength-bar";
        if (i < filledBars) {
          bar.classList.add(levelClass);
        }
      });
    }

    function validatePasswordForm() {
      const hasCurrent = currentPassword.value.length > 0;
      const newVal = newPassword.value;
      const confirmVal = confirmPassword.value;
      const strongEnough = newVal.length >= 8;
      const match = confirmVal.length > 0 && newVal === confirmVal;

      if (confirmVal.length === 0) {
        matchHint.textContent = "";
      } else if (match) {
        matchHint.textContent = "As senhas coincidem.";
        matchHint.style.color = "var(--cor-d5)";
      } else {
        matchHint.textContent = "As senhas não coincidem.";
        matchHint.style.color = "var(--cor-d1)";
      }

      savePasswordBtn.disabled = !(hasCurrent && strongEnough && match);
    }
    if (document.querySelector("#configs")) {
      newPassword.addEventListener("input", () => {
        const score = checkPasswordStrength(newPassword.value);
        updateStrengthBars(score);
        validatePasswordForm();
      });
      currentPassword.addEventListener("input", validatePasswordForm);
      confirmPassword.addEventListener("input", validatePasswordForm);
    }

    const deleteModal = document.getElementById("delete-modal");
    const openDeleteModalBtn = document.getElementById("open-delete-modal");
    const cancelDeleteBtn = document.getElementById("cancel-delete-btn");
    const confirmDeleteBtn = document.getElementById("confirm-delete-btn");
    const deleteConfirmInput = document.getElementById("delete-confirm-input");

    function openModal() {
      confirmUsernameTarget.textContent = displayUsername.textContent;
      deleteModal.classList.add("open");
      deleteConfirmInput.value = "";
      confirmDeleteBtn.disabled = true;
      setTimeout(() => deleteConfirmInput.focus(), 250);
    }
    function closeModal() {
      deleteModal.classList.remove("open");
    }
    if (document.querySelector("#configs")) {
      openDeleteModalBtn.addEventListener("click", openModal);
      cancelDeleteBtn.addEventListener("click", closeModal);
      deleteModal.addEventListener("click", (e) => {
        if (e.target === deleteModal) closeModal();
      });

      deleteConfirmInput.addEventListener("input", () => {
        confirmDeleteBtn.disabled =
          deleteConfirmInput.value.trim() !==
          displayUsername.textContent.trim();
      });

      confirmDeleteBtn.addEventListener("click", async () => {
        try {
          const dadosExclusao = await buscarUsuarioLogado();
          await deletarUsuario(dadosExclusao.usuario.id);
          closeModal();
          showToast("Conta excluída. Redirecionando...", true);
          window.location.href = "./index.html";
        } catch (erro) {
          console.error("Falha ao excluir conta:", erro);
          showToast(erro.message || "Não foi possível excluir a conta.", false);
        }
      });
    }

    const nomeConfigs = document.querySelector("#display-username");
    const emailConfigs = document.querySelector("#display-email");
    const inputNome = document.querySelector("#username-input");
    const inputEmail = document.querySelector("#email-input");
    const criadoEm = document.querySelector("#criado-em");
    const btnSalvar = document.querySelector("#save-profile-btn");

    const pillVerificado = document.querySelector("#verificado-pill");
    const iconeVerificado = document.querySelector("#verificado-icone");
    const textoVerificado = document.querySelector("#verificado-texto");
    
    function atualizarPillVerificado(verificado) {
      pillVerificado.classList.toggle("verificado", verificado);
      pillVerificado.classList.toggle("nao-verificado", !verificado);
      iconeVerificado.classList.toggle("fa-circle-check", verificado);
      iconeVerificado.classList.toggle("fa-triangle-exclamation", !verificado);
      textoVerificado.textContent = verificado
        ? "E-mail verificado"
        : "E-mail não verificado";
    }

    let usuarioAtual = null;

    async function trocarDadosConfigs() {
      const resposta = await buscarUsuarioLogado();
      const dataFormatada = formatarMesAno(resposta.usuario.criado_em);

      usuarioAtual = resposta.usuario;

      nomeConfigs.textContent = resposta.usuario.nome;
      emailConfigs.textContent = resposta.usuario.email;
      inputNome.value = resposta.usuario.nome;
      inputEmail.value = resposta.usuario.email;
      criadoEm.textContent = `Membro desde ${dataFormatada}`;
      atualizarPillVerificado(resposta.usuario.verificado);
    }

    // --- Modal de verificação de e-mail ---
    const modalVerificacao = document.querySelector("#verificar-email-modal");
    const alvoEmail = document.querySelector("#verificar-email-alvo");
    const botaoAbrirVerificacao = document.querySelector(
      "#btn-verificar-agora",
    );
    const botaoEnviarCodigo = document.querySelector("#btn-enviar-codigo");
    const inputsCodigo = Array.from(document.querySelectorAll(".input-codigo"));
    const erroVerificacao = document.querySelector("#verificar-email-erro");
    const botaoConfirmarCodigo = document.querySelector(
      "#btn-confirmar-codigo",
    );
    const botaoFecharVerificacao = document.querySelector(
      "#btn-fechar-verificacao",
    );

    let temporizadorReenvio = null;

    function alternarInputsCodigo(habilitado) {
      inputsCodigo.forEach((input) => {
        input.disabled = !habilitado;
      });
    }

    function validarCodigoCompleto() {
      const codigo = inputsCodigo.map((input) => input.value).join("");
      botaoConfirmarCodigo.disabled = codigo.length !== 4;
    }

    function iniciarContagemReenvio() {
      let restante = SEGUNDOS_REENVIO;
      botaoEnviarCodigo.disabled = true;

      clearInterval(temporizadorReenvio);
      temporizadorReenvio = setInterval(() => {
        restante -= 1;

        if (restante <= 0) {
          clearInterval(temporizadorReenvio);
          botaoEnviarCodigo.disabled = false;
          botaoEnviarCodigo.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Reenviar código`;
          return;
        }

        botaoEnviarCodigo.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Reenviar em ${restante}s`;
      }, 1000);
    }

    function fecharModalVerificacao() {
      clearInterval(temporizadorReenvio);
      modalVerificacao.classList.remove("open");
    }

    function abrirModalVerificacao() {
      if (!usuarioAtual) return;

      alvoEmail.textContent = usuarioAtual.email;
      erroVerificacao.textContent = "";
      inputsCodigo.forEach((input) => (input.value = ""));
      alternarInputsCodigo(false);
      botaoConfirmarCodigo.disabled = true;
      botaoEnviarCodigo.disabled = false;
      botaoEnviarCodigo.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Enviar código`;
      modalVerificacao.classList.add("open");
    }

    botaoAbrirVerificacao.addEventListener("click", abrirModalVerificacao);

    botaoEnviarCodigo.addEventListener("click", async () => {
      if (!usuarioAtual) return;

      erroVerificacao.textContent = "";
      botaoEnviarCodigo.disabled = true;

      try {
        await enviarEmailVerificar(usuarioAtual.id);
        alternarInputsCodigo(true);
        inputsCodigo[0].focus();
        iniciarContagemReenvio();
      } catch (erro) {
        console.error("Falha ao enviar código de verificação:", erro);
        erroVerificacao.textContent =
          erro.message || "Não foi possível enviar o código. Tente novamente.";
        botaoEnviarCodigo.disabled = false;
      }
    });

    inputsCodigo.forEach((input, indice) => {
      input.addEventListener("input", () => {
        input.value = input.value.replace(/\D/g, "").slice(0, 1);

        if (input.value && indice < inputsCodigo.length - 1) {
          inputsCodigo[indice + 1].focus();
        }

        validarCodigoCompleto();
      });

      input.addEventListener("keydown", (e) => {
        if (e.key === "Backspace" && !input.value && indice > 0) {
          inputsCodigo[indice - 1].focus();
        }
      });

      input.addEventListener("paste", (e) => {
        e.preventDefault();
        const colado = (e.clipboardData || window.clipboardData)
          .getData("text")
          .replace(/\D/g, "")
          .slice(0, inputsCodigo.length);

        colado.split("").forEach((digito, i) => {
          if (inputsCodigo[i]) inputsCodigo[i].value = digito;
        });

        const proximo =
          inputsCodigo[Math.min(colado.length, inputsCodigo.length - 1)];
        proximo.focus();
        validarCodigoCompleto();
      });
    });

    botaoConfirmarCodigo.addEventListener("click", async () => {
      if (!usuarioAtual) return;

      const codigo = inputsCodigo.map((input) => input.value).join("");
      erroVerificacao.textContent = "";
      botaoConfirmarCodigo.disabled = true;

      try {
        const resposta = await conferirEmailVerificar(usuarioAtual.id, codigo);
        usuarioAtual = resposta.usuario;
        atualizarPillVerificado(true);
        fecharModalVerificacao();
        showToast("E-mail verificado com sucesso.", true);
      } catch (erro) {
        console.error("Falha ao verificar código:", erro);
        erroVerificacao.textContent =
          erro.message ||
          "Não foi possível verificar o código. Tente novamente.";
        botaoConfirmarCodigo.disabled = false;
      }
    });

    botaoFecharVerificacao.addEventListener("click", fecharModalVerificacao);
    modalVerificacao.addEventListener("click", (e) => {
      if (e.target === modalVerificacao) fecharModalVerificacao();
    });

    btnSalvar.addEventListener("click", () => {
      atualizaDados();
      setTimeout(() => {
        location.reload();
      }, 500);
    });

    async function atualizaDados() {
      const valorNome = inputNome.value.trim();
      const valorEmail = inputEmail.value.trim();

      if (!valorNome || !valorEmail) {
        showToast("Preencha nome e e-mail antes de salvar.", false);
        return;
      }

      if (!inputEmail.checkValidity()) {
        showToast("Digite um e-mail válido.", false);
        inputEmail.focus();
        return;
      }

      try {
        const dados = await buscarUsuarioLogado();

        const resposta =
          dados.usuario.email == valorEmail
            ? await atualizarUsuario(
                dados.usuario.id,
                valorNome,
                undefined,
                undefined,
              )
            : await atualizarUsuario(
                dados.usuario.id,
                valorNome,
                valorEmail,
                undefined,
              );

        nomeConfigs.textContent = valorNome;
        emailConfigs.textContent = valorEmail;
        confirmUsernameTarget.textContent = valorNome;
        showToast(resposta.mensagem || "Perfil atualizado com sucesso.", true);
      } catch (erro) {
        console.error("Falha ao atualizar dados:", erro);
        showToast(
          erro.message || "Não foi possível atualizar o perfil.",
          false,
        );
      }
    }

    const btnAtualizarSenha = document.querySelector("#save-password-btn");

    async function atualizaSenha() {
      const valorSenhaAtual = currentPassword.value;
      const valorSenhaNova = newPassword.value;
      const dados = await buscarUsuarioLogado();

      try {
        await atualizarUsuario(
          dados.usuario.id,
          undefined,
          undefined,
          valorSenhaNova,
          valorSenhaAtual,
        );

        currentPassword.value = "";
        newPassword.value = "";
        confirmPassword.value = "";
        strengthBars.forEach((bar) => (bar.className = "strength-bar"));
        matchHint.textContent = "";
        savePasswordBtn.disabled = true;
        showToast("Senha atualizada com sucesso.", true);
      } catch (erro) {
        showToast(erro.message, false);
        return;
      }
    }

    btnAtualizarSenha.addEventListener("click", () => {
      atualizaSenha();
    });

    trocarDadosConfigs();
  } catch (erro) {
    console.error("Erro ao iniciar a página de configurações:", erro);
  }
});
