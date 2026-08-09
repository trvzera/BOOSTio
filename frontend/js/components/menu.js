// Alterna as classes que mostram o menu de perfil logado ou deslogado.
export function atualizarMenu(autenticado) {
  const menuComLogin = document.querySelector("#profile-nav-list-logado");
  const menuSemLogin = document.querySelector("#profile-nav-list-deslogado");

  menuComLogin.classList.toggle("ativo", autenticado);
  menuSemLogin.classList.toggle("ativo", !autenticado);
}
