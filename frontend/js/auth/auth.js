import { buscarUsuarioLogado } from "../api/usuario/buscarUsuarioLogado.js";
import { logout } from "../api/usuario/logout.js";
import { atualizarMenu } from "../components/menu.js";

export function caminhoLogin() {
  const estaEmPages = window.location.pathname.includes("/pages/");
  return estaEmPages ? "./login.html" : "./pages/login.html";
}

export async function confirmaUsuario() {
  const resposta = await buscarUsuarioLogado();

  if (document.body.id === "login" || document.body.id === "signin") {
    // Páginas só para visitante: se já está logado, manda pro dashboard.
    if (resposta.auth) {
      window.location.href =  "./index.html";
      return;
    }
  } else if (!["inicio", "erro"].includes(document.body.id)) {
    // Páginas protegidas: se não está logado, manda pro login.
    // "inicio" (index.html) é pública, não entra nessa checagem.
    if (!resposta.auth) {
      window.location.href = caminhoLogin();
      return;
    }
  }

  atualizarMenu(resposta.auth);
}

window.addEventListener("load", async () => {
  try {
    await confirmaUsuario();
  } catch (erro) {
    // Permite visualizar o front com o Live Server mesmo quando a API
    // ainda não estiver em execução. Nesse caso, exibe o menu deslogado.
    console.warn("Não foi possível consultar a sessão do usuário:", erro);
    atualizarMenu(false);
  }
});

async function sairSessao() {
  await logout();
}

const btnSair = document.querySelector("#btn-logout");
if (btnSair) {
  btnSair.addEventListener("click", async (e) => {
    e.preventDefault();
    await sairSessao();
    window.location.href = caminhoLogin();
  });
}
