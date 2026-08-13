// Comportamento do header: menu de perfil e menu hambúrguer (mobile).
const containerProfile = document.querySelector("#profile");
const profileCheck = document.querySelector("#profile-check");
const ltProfile = registrarAnimacao("profile", "../lottie/profile.json");

document.addEventListener("click", (e) => {
  if (!containerProfile.contains(e.target)) {
    profileCheck.checked = false;
  }
});

containerProfile.addEventListener("mouseenter", () => {
  if (!profileCheck.checked) {
    ltProfile.setDirection(1);
    ltProfile.play();
  }
});

containerProfile.addEventListener("mouseleave", () => {
  if (!profileCheck.checked) {
    ltProfile.setDirection(-1);
    ltProfile.play();
  }
});

const burgerMenu = document.querySelector("#burger-menu");
const burgerCheck = document.querySelector("#burger-check");

document.addEventListener("click", (e) => {
  if (!burgerMenu.contains(e.target)) {
    burgerCheck.checked = false;
  }
});

// Sem controle de sessão no front (nada de token em localStorage), o menu de
// perfil sempre mostra as opções de "Entrar" / "Criar conta".
const listaDeslogado = document.querySelector("#profile-nav-list-deslogado");
listaDeslogado.classList.add("ativo");

// LOTTIE

import {
  registrarAnimacao,
  obterAnimacao,
} from "./components/lottie-controller.js";

const ltLogon = registrarAnimacao("lottie-logon", "../lottie/logon.json");
const ltLogin = registrarAnimacao("lottie-login", "../lottie/login.json");
const ltLogout = registrarAnimacao("lottie-logout", "../lottie/logout-lt.json");
const ltUser = registrarAnimacao("lottie-user", "../lottie/user.json");
const ltBuild = registrarAnimacao("lottie-build", "../lottie/build.json");

const btnLogon = document.getElementById("btn-logon");

btnLogon.addEventListener("mouseenter", () => {
  ltLogon.setDirection(1);
  ltLogon.play();
});

btnLogon.addEventListener("mouseleave", () => {
  ltLogon.setDirection(-1);
  ltLogon.play();
});

const btnLogin = document.getElementById("btn-login");

btnLogin.addEventListener("mouseenter", () => {
  ltLogin.setDirection(1);
  ltLogin.play();
});

btnLogin.addEventListener("mouseleave", () => {
  ltLogin.setDirection(-1);
  ltLogin.play();
});

const btnLogout = document.getElementById("btn-logout");

btnLogout.addEventListener("mouseenter", () => {
  ltLogout.setDirection(1);
  ltLogout.play();
});

btnLogout.addEventListener("mouseleave", () => {
  ltLogout.setDirection(-1);
  ltLogout.play();
});

const btnUser = document.getElementById("btn-user");

btnUser.addEventListener("mouseenter", () => {
  ltUser.setDirection(1);
  ltUser.play();
});

btnUser.addEventListener("mouseleave", () => {
  ltUser.setDirection(-1);
  ltUser.play();
});

const btnBuild = document.getElementById("btn-build");

btnBuild.addEventListener("mouseenter", () => {
  ltBuild.setDirection(1);
  ltBuild.play();
});

btnBuild.addEventListener("mouseleave", () => {
  ltBuild.setDirection(-1);
  ltBuild.play();
});

import { destruirTodas } from "./components/lottie-controller.js";

window.addEventListener("beforeunload", destruirTodas);
