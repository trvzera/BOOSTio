// Alterna as classes que mostram o menu de perfil logado ou deslogado.
export function atualizarMenu(autenticado) {
  const menuComLogin = document.querySelector("#profile-nav-list-signed-in");
  const menuSemLogin = document.querySelector("#profile-nav-list-signed-out");

  menuComLogin.classList.toggle("active", autenticado);
  menuSemLogin.classList.toggle("active", !autenticado);
}
