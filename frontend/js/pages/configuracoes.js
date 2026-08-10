// Entry point da página de configurações (pages/configuracoes.html):
// edição de perfil, troca de senha e exclusão de conta.
import "../header.js";
import "../services-carousel.js";
import { caminhoLogin } from "../auth/auth.js";
import { buscarUsuarioLogado } from "../api/usuario/buscarUsuarioLogado.js";
import { atualizarUsuario } from "../api/usuario/atualizarUsuario.js";
import { deletarUsuario } from "../api/usuario/deletarUsuario.js";
import { formatarMesAno } from "../utils/formatarData.js";

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
      emailInput.classList.toggle("invalido", emailInput.value.length > 0 && !emailInput.checkValidity());
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
          deleteConfirmInput.value.trim() !== displayUsername.textContent.trim();
      });

      confirmDeleteBtn.addEventListener("click", async () => {
        try {
          const dadosExclusao = await buscarUsuarioLogado();
          await deletarUsuario(dadosExclusao.usuario.id);
          closeModal();
          showToast("Conta excluída. Redirecionando...", true);
          window.location.href = "../index.html";
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

    async function trocarDadosConfigs() {
      const resposta = await buscarUsuarioLogado();
      const dataFormatada = formatarMesAno(resposta.usuario.criado_em);

      nomeConfigs.textContent = resposta.usuario.nome;
      emailConfigs.textContent = resposta.usuario.email;
      inputNome.value = resposta.usuario.nome;
      inputEmail.value = resposta.usuario.email;
      criadoEm.textContent = `Membro desde ${dataFormatada}`;
    }

    btnSalvar.addEventListener("click", () => {
      atualizaDados();
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
            ? await atualizarUsuario(dados.usuario.id, valorNome, undefined, undefined)
            : await atualizarUsuario(dados.usuario.id, valorNome, valorEmail, undefined);

        nomeConfigs.textContent = valorNome;
        emailConfigs.textContent = valorEmail;
        confirmUsernameTarget.textContent = valorNome;
        showToast(resposta.mensagem || "Perfil atualizado com sucesso.", true);
      } catch (erro) {
        console.error("Falha ao atualizar dados:", erro);
        showToast(erro.message || "Não foi possível atualizar o perfil.", false);
      }
    }

    const btnAtualizarSenha = document.querySelector("#save-password-btn");

    async function atualizaSenha() {
      const valorSenhaAtual = currentPassword.value;
      const valorSenhaNova = newPassword.value;
      const dados = await buscarUsuarioLogado();

      try {
        await atualizarUsuario(dados.usuario.id, undefined, undefined, valorSenhaNova, valorSenhaAtual);

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
