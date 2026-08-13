import {
  registrarAnimacao,
  destruirTodas,
} from "./components/lottie-controller.js";

const containerProfile = document.querySelector("#profile");
const profileCheck = document.querySelector("#profile-check");
const burgerMenu = document.querySelector("#burger-menu");
const burgerCheck = document.querySelector("#burger-check");

document.addEventListener("click", (e) => {
  if (!burgerMenu.contains(e.target)) {
    burgerCheck.checked = false;
  }
});

const listaDeslogado = document.querySelector("#profile-nav-list-deslogado");
listaDeslogado.classList.add("ativo");

async function iniciarAnimacoes() {
  const ltProfile = await registrarAnimacao(
    "profile",
    "../lottie/profile.json",
  );
  const ltLogon = await registrarAnimacao(
    "lottie-logon",
    "../lottie/logon.json",
  );
  const ltLogin = await registrarAnimacao(
    "lottie-login",
    "../lottie/login.json",
  );
  const ltLogout = await registrarAnimacao(
    "lottie-logout",
    "../lottie/logout-lt.json",
  );
  const ltUser = await registrarAnimacao("lottie-user", "../lottie/user.json");
  const ltBuild = await registrarAnimacao(
    "lottie-build",
    "../lottie/build.json",
  );
  const ltBurger = await registrarAnimacao(
    "lottie-burger",
    "../lottie/hamburger.json",
  );

  document.addEventListener("click", (e) => {
    if (!containerProfile.contains(e.target)) {
      profileCheck.checked = false;
      ltProfile.setDirection(-1);
      ltProfile.play();
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

  burgerCheck.addEventListener("click", () => {
    if (burgerCheck.checked) {
      ltBurger.setDirection(1);
      ltBurger.play();
    } else {
      ltBurger.setDirection(-1);
      ltBurger.play();
    }
  });
}

iniciarAnimacoes();

window.addEventListener("beforeunload", destruirTodas);
