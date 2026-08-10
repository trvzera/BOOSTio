// Lógica de autenticação compartilhada por todas as páginas: confirma se
// existe sessão ativa, redireciona conforme a página atual e mantém o menu
// de perfil sincronizado. Equivale à antiga lógica de scripts.js, mas agora
// busca o usuário logado via api/usuario/buscarUsuarioLogado.js.
import { buscarUsuarioLogado } from "../api/usuario/buscarUsuarioLogado.js";
import { logout } from "../api/usuario/logout.js";
import { atualizarMenu } from "../components/menu.js";

export function caminhoLogin() {
  const estaEmPages = window.location.pathname.includes("/pages/");
  return estaEmPages ? "./login.html" : "./pages/login.html";
}

export function caminhoDashboard() {
  const estaEmPages = window.location.pathname.includes("/pages/");
  return estaEmPages ? "../index.html" : "./index.html";
}

export async function confirmaUsuario() {
  const resposta = await buscarUsuarioLogado();

  if (document.body.id === "login" || document.body.id === "signin") {
    // Páginas só para visitante: se já está logado, manda pro dashboard.
    if (resposta.auth) {
      window.location.href = caminhoDashboard();
      return;
    }
  } else if (document.body.id !== "inicio") {
    // Páginas protegidas: se não está logado, manda pro login.
    // "inicio" (index.html) é pública, não entra nessa checagem.
    if (!resposta.auth) {
      window.location.href = caminhoLogin();
      return;
    }
  }

  atualizarMenu(resposta.auth);
}

window.addEventListener("load", () => {
  confirmaUsuario();
});

async function sairSessao() {
  await logout();
}

const btnSair = document.querySelector("#btn-sair");
btnSair.addEventListener("click", async (e) => {
  e.preventDefault();
  await sairSessao();
  window.location.href = caminhoLogin();
});
