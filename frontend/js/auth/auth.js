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

export async function confirmaUsuario() {
  const resposta = await buscarUsuarioLogado();

  if (
    document.body.id === "login" ||
    document.body.id === "signin" ||
    document.body.id === "inicio"
  ) {
    if (resposta.auth) {
      // Atenção: caminhoDashboard() não existe em lugar nenhum do projeto
      // (bug pré-existente em scripts.js). Mantido igual ao original.
      window.location.href = caminhoDashboard();
      return;
    }
  } else {
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
