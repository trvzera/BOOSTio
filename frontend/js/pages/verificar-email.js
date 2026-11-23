import { fetchComErro } from "../api/_shared/fetchComErro.js";

const token = new URLSearchParams(window.location.hash.slice(1)).get("token");
const status = document.querySelector("#confirmacao-status");
const erro = document.querySelector("#confirmacao-erro");
const botao = document.querySelector("#confirmar-email");
const voltar = document.querySelector("#continuar-boostio");

document.querySelector(".skip-link").addEventListener("click", evento => {
  evento.preventDefault();
  document.querySelector("#confirmacao-email").focus();
});

if (token) {
  botao.hidden = false;
  botao.addEventListener("click", async () => {
    botao.disabled = true;
    botao.textContent = "Confirmando…";
    erro.textContent = "";

    try {
      await fetchComErro("/email/verificar/link", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      window.history.replaceState(null, "", window.location.pathname);
      status.textContent = "E-mail confirmado. Você já pode usar sua conta BOOSTio.";
      botao.hidden = true;
      voltar.textContent = "Continuar na BOOSTio";
      voltar.setAttribute("aria-label", voltar.textContent);
      voltar.focus();
    } catch (falha) {
      erro.textContent = falha.message || "Não foi possível confirmar seu e-mail. Tente novamente.";
      botao.disabled = false;
      botao.textContent = "Confirmar e-mail";
    }
  });
} else {
  status.textContent = "Abra o botão no e-mail mais recente da BOOSTio para confirmar seu endereço.";
}
