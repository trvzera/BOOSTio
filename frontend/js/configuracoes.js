// Lógica da página de configurações (pages/configuracoes.html):
// edição de perfil, troca de senha e exclusão de conta.

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

const usernameInput = document.getElementById("username-input");
const emailInput = document.getElementById("email-input");
const displayUsername = document.getElementById("display-username");
const displayEmail = document.getElementById("display-email");
const confirmUsernameTarget = document.getElementById(
  "confirm-username-target",
);

emailInput.addEventListener("input", () => {
  emailInput.classList.toggle("invalido", emailInput.value.length > 0 && !emailInput.checkValidity());
});

if (document.querySelector("#configs")) {
  document.getElementById("save-profile-btn").addEventListener("click", () => {
    const newUsername = usernameInput.value.trim();
    const newEmail = emailInput.value.trim();

    if (!newUsername || !newEmail) {
      showToast("Preencha nome e e-mail antes de salvar.", false);
      return;
    }

    if (!emailInput.checkValidity()) {
      showToast("Digite um e-mail válido.", false);
      emailInput.focus();
      return;
    }

    displayUsername.textContent = newUsername;
    displayEmail.textContent = newEmail;
    confirmUsernameTarget.textContent = newUsername;
    showToast("Perfil atualizado com sucesso.", true);
  });
}

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

  savePasswordBtn.addEventListener("click", () => {
    // aqui entraria a chamada real pra API de troca de senha
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
    strengthBars.forEach((bar) => (bar.className = "strength-bar"));
    matchHint.textContent = "";
    savePasswordBtn.disabled = true;
    showToast("Senha atualizada com sucesso.", true);
  });
}
const deleteModal = document.getElementById("delete-modal");
const openDeleteModalBtn = document.getElementById("open-delete-modal");
const cancelDeleteBtn = document.getElementById("cancel-delete-btn");
const confirmDeleteBtn = document.getElementById("confirm-delete-btn");
const deleteConfirmInput = document.getElementById("delete-confirm-input");

function openModal() {
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

  confirmDeleteBtn.addEventListener("click", () => {
    // aqui entraria a chamada real pra API de exclusão de conta, ex:
    // await fetch('/api/account', { method: 'DELETE' })
    closeModal();
    showToast("Conta excluída. Redirecionando...", true);
    // window.location.href = '/index.html';
  });
}
