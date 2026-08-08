// Comportamento do header: menu de perfil e menu hambúrguer (mobile).
const containerProfile = document.querySelector("#profile");
const profileCheck = document.querySelector("#profile-check");

document.addEventListener("click", (e) => {
  if (!containerProfile.contains(e.target)) {
    profileCheck.checked = false;
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
