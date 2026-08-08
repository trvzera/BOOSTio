import "./header.js";
import "./services-carousel.js";
import { confirmaLogin } from "./api/auth_api/me_auth.js";
import { fazerLogout } from "./api/auth_api/logout_auth.js";

const menuComLogin = document.querySelector("#profile-nav-list-logado");
const menuSemLogin = document.querySelector("#profile-nav-list-deslogado");
const btnSair = document.querySelector("#btn-sair");

export function caminhoLogin() {
  const estaEmPages = window.location.pathname.includes("/pages/");
  return estaEmPages ? "./login.html" : "./pages/login.html";
}

async function confirmaUsuario() {
  const resposta = await confirmaLogin();

  if (document.body.id === "login" || document.body.id === "signin" || document.body.id === "inicio") {
    if (resposta.auth) {
      window.location.href = caminhoDashboard();
      return;
    }
  } else {
    if (!resposta.auth) {
      window.location.href = caminhoLogin();
      return;
    }
  }

  menuComLogin.classList.toggle("ativo", resposta.auth);
  menuSemLogin.classList.toggle("ativo", !resposta.auth);
}

window.addEventListener("load", () => {
  confirmaUsuario();
});

async function sairSessao() {
  await fazerLogout();
}

btnSair.addEventListener("click", async (e) => {
  e.preventDefault();
  await sairSessao();
  window.location.href = caminhoLogin();
});