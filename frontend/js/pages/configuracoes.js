// Entry point da página de configurações (pages/configuracoes.html):
// edição de perfil, troca de senha e exclusão de conta.
import "../header.js";
import "./budget-perfil.js";
import "../services-carousel.js";
import { caminhoLogin } from "../auth/auth.js";
import { carregarPerfil as buscarUsuarioLogado } from "../conta/perfil.js";
import { atualizarUsuario } from "../api/usuario/atualizarUsuario.js";
import { deletarUsuario } from "../api/usuario/deletarUsuario.js";
import { fetchComErro } from "../api/_shared/fetchComErro.js";
import { formatarMesAno } from "../utils/formatarData.js";
import { enviarEmailVerificar } from "../api/email/enviarEmailVerificar.js";
import { conferirEmailVerificar } from "../api/email/conferirEmailVerificar.js";
import { acompanharCarregamento } from "../components/page-loading.js";
import { iniciarFluxoVerificacaoEmail } from "../components/verification-flow.js";
import { listarBuilds } from "../api/build/builds.js";
import { textoBuildsSalvas } from "../conta/resumo-perfil.js";


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
        const campo = {"profile-current-password":"senha de confirmação do e-mail","current-password":"senha atual","new-password":"nova senha","confirm-password":"confirmação da senha"}[btn.dataset.target];
        btn.setAttribute("aria-label", (isPassword ? "Ocultar " : "Mostrar ") + campo);
        btn.setAttribute("aria-pressed", String(isPassword));
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
      const hasCurrent = usuarioAtual?.possui_senha === false || currentPassword.value.length > 0;
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
    if (document.body.classList.contains("settings-page-body")) {
      newPassword.addEventListener("input", () => {
        const score = checkPasswordStrength(newPassword.value);
        updateStrengthBars(score);
        validatePasswordForm();
      });
      currentPassword.addEventListener("input", validatePasswordForm);
      confirmPassword.addEventListener("input", validatePasswordForm);
    }

    const deleteModal = document.getElementById("delete-modal");
    document.querySelectorAll("[data-confirmar-google]").forEach(botao => {
      botao.addEventListener("click", async () => {
        botao.disabled = true;
        try {
          const resposta = await fetchComErro("/auth/google/confirmar", {method: "POST"});
          window.location.assign(resposta.url);
        } catch (erro) {
          showToast(erro.message, false);
          botao.disabled = false;
        }
      });
    });
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
      document.getElementById("delete-current-password").value = "";
      deleteModal.classList.remove("open");
    }
    if (document.body.classList.contains("settings-page-body")) {
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
          await deletarUsuario(dadosExclusao.usuario.id, document.getElementById("delete-current-password").value);
          closeModal();
          showToast("Conta desativada. Redirecionando...", true);
          window.location.href = "./index.html";
        } catch (erro) {
          console.error("Falha ao desativar conta:", erro);
          showToast(erro.message || "Não foi possível desativar a conta.", false);
        }
      });
    }

    const nomeConfigs = document.querySelector("#display-username");
    const emailConfigs = document.querySelector("#display-email");
    const inputNome = document.querySelector("#username-input");
    const inputEmail = document.querySelector("#email-input");
    const criadoEm = document.querySelector("#created-at");
    const btnSalvar = document.querySelector("#save-profile-btn");

    const pillVerificado = document.querySelector("#verified-pill");
    const iconeVerificado = document.querySelector("#verified-icon");
    const textoVerificado = document.querySelector("#verified-text");
    
    function atualizarPillVerificado(verificado) {
      pillVerificado.classList.toggle("verified", verificado);
      pillVerificado.classList.toggle("unverified", !verificado);
      iconeVerificado.classList.toggle("fa-circle-check", verificado);
      iconeVerificado.classList.toggle("fa-triangle-exclamation", !verificado);
      textoVerificado.textContent = verificado
        ? "E-mail verificado"
        : "E-mail não verificado";
    }

    let usuarioAtual = null;
    function atualizarAcesso() {
      const google=usuarioAtual?.google_vinculado===true,senha=usuarioAtual?.possui_senha!==false;
      document.querySelector("#google-access-status").textContent=google?"Conta vinculada ao Google" : "Google não vinculado";
      document.querySelector("#google-link-fields").hidden=google||!senha;
      document.querySelector(".profile-identity-confirmation").hidden=senha;
      document.querySelector("#profile-current-password").closest(".field").hidden=!senha;
      currentPassword.closest(".field").hidden=!senha;
      document.querySelector("#delete-current-password").closest(".field").hidden=!senha;
      document.querySelector('#delete-modal [data-confirmar-google]').hidden=senha;
      document.querySelector("#password-google-confirm").hidden=senha;
      document.querySelector("#password-settings-title").textContent=senha?"Alterar senha":"Criar senha de acesso";
      document.querySelector("#password-settings-description").textContent=senha?"Utilize esse campo para alterar a sua senha.":"Confirme sua identidade pelo Google e crie uma senha em até cinco minutos. Você continuará podendo entrar pelo Google.";
      validatePasswordForm();
    }
    document.querySelector("#link-google").addEventListener("click",async()=>{
      const botao=document.querySelector("#link-google"),campo=document.querySelector("#google-link-password"),feedback=document.querySelector("#google-link-feedback");
      if(!campo.value){feedback.textContent="Confirme sua senha atual antes de vincular.";campo.focus();return;}
      botao.disabled=true;feedback.textContent="Abrindo a confirmação do Google…";
      try{
        const resposta=await fetchComErro("/auth/google/vincular",{method:"POST",body:JSON.stringify({senha_atual:campo.value})});
        campo.value="";location.assign(resposta.url);
      }catch(erro){feedback.textContent=erro.message;botao.disabled=false;}
    });

    async function atualizarQuantidadeBuilds() {
      const resumo = document.querySelector("#profile-build-count");
      if (!resumo) return;
      const usuarioId = usuarioAtual?.id, controle = new AbortController();
      const timeout = setTimeout(() => controle.abort(),8000);
      resumo.textContent = "Carregando builds…";
      resumo.removeAttribute("title");
      try {
        const resposta = await listarBuilds({signal:controle.signal});
        if (usuarioAtual?.id === usuarioId) resumo.textContent = textoBuildsSalvas(resposta.builds);
      } catch {
        if (usuarioAtual?.id === usuarioId) {
          resumo.textContent = "Builds indisponíveis";
          resumo.title = "Não foi possível consultar suas builds. Recarregue a página para tentar novamente.";
        }
      } finally { clearTimeout(timeout); }
    }

    async function trocarDadosConfigs() {
      const resposta = await buscarUsuarioLogado();
      const dataFormatada = formatarMesAno(resposta.usuario.criado_em);

      usuarioAtual = resposta.usuario;
      atualizarAcesso();

      nomeConfigs.textContent = resposta.usuario.nome;
      emailConfigs.textContent = resposta.usuario.email;
      inputNome.value = resposta.usuario.nome;
      inputEmail.value = resposta.usuario.email;
      criadoEm.textContent = `Membro desde ${dataFormatada}`;
      atualizarPillVerificado(resposta.usuario.verificado);
      await atualizarQuantidadeBuilds();
    }

    // --- Modal de verificação de e-mail ---
    const modalVerificacao = document.querySelector("#verify-email-modal");
    const fluxoVerificacao = iniciarFluxoVerificacaoEmail({
      modal:modalVerificacao,enviar:enviarEmailVerificar,confirmar:conferirEmailVerificar,
      aoConfirmar:resposta=>{
        usuarioAtual=resposta.usuario;atualizarPillVerificado(true);
        showToast("E-mail verificado com sucesso.",true);
      },
    });
    const abrirModalVerificacao=()=>fluxoVerificacao.abrir(usuarioAtual);
    document.querySelector("#btn-verify-now").addEventListener("click",abrirModalVerificacao);
    document.querySelector("#btn-close-verification").addEventListener("click",()=>fluxoVerificacao.fechar());
    window.addEventListener("pagehide",()=>fluxoVerificacao.destruir(),{once:true});

    btnSalvar.addEventListener("click", atualizaDados);

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
                document.getElementById("profile-current-password").value,
              );

        nomeConfigs.textContent = valorNome;
        emailConfigs.textContent = valorEmail;
        confirmUsernameTarget.textContent = valorNome;
        showToast(resposta.mensagem || "Perfil atualizado com sucesso.", true);
        document.getElementById("profile-current-password").value = "";
        location.reload();
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
        showToast("Senha atualizada. Entre novamente para continuar.", true);
        window.location.href=caminhoLogin();
      } catch (erro) {
        showToast(erro.message, false);
        return;
      }
    }

    btnAtualizarSenha.addEventListener("click", () => {
      atualizaSenha();
    });

    await acompanharCarregamento(trocarDadosConfigs());
    const retornoGoogle=new URLSearchParams(location.search);
    if(retornoGoogle.has("google_erro")||retornoGoogle.get("google")==="vinculado"){
      document.querySelector("#google-link-feedback").textContent=retornoGoogle.get("google_erro")||"Google vinculado com sucesso.";
      retornoGoogle.delete("google_erro");retornoGoogle.delete("google");
      history.replaceState(null,"",location.pathname+(retornoGoogle.size?"?"+retornoGoogle:"")+location.hash);
    }
    window.addEventListener("pageshow",evento => { if (evento.persisted) acompanharCarregamento(trocarDadosConfigs()); });
    if (new URLSearchParams(location.search).has("verificar")) abrirModalVerificacao();
  } catch (erro) {
    console.error("Erro ao iniciar a página de configurações:", erro);
  }
});
