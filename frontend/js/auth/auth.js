import { buscarUsuarioLogado } from "../api/usuario/buscarUsuarioLogado.js";
import { logout } from "../api/usuario/logout.js";
import { atualizarMenu } from "../components/menu.js";
import { redirecionamentoSessao } from "../components/navigation-config.js";

export function caminhoLogin() { return new URL("../../pages/login.html",import.meta.url).href; }
export async function confirmaUsuario() {
  const resposta = await buscarUsuarioLogado();
  const autenticado = Boolean(resposta?.auth);
  atualizarMenu(autenticado);
  const destino = redirecionamentoSessao(location.pathname.split("/").pop(),autenticado);
  if (destino) location.replace(new URL("../../pages/" + destino,import.meta.url).href);
  return resposta;
}
async function conferirSessao() {
  try { await confirmaUsuario(); }
  catch (erro) {
    console.warn("Não foi possível consultar a sessão do usuário:",erro);
    atualizarMenu(false); // Live Server/offline: o front continua utilizável.
  }
}
window.addEventListener("load",conferirSessao);
window.addEventListener("pageshow",e => { if (e.persisted) conferirSessao(); });
document.addEventListener("click",async e => {
  if (!e.target.closest("#btn-logout")) return;
  e.preventDefault();
  const botao = document.querySelector("#btn-logout");
  botao.disabled = true; botao.dataset.busy = "true";
  try { await logout(); location.href = caminhoLogin(); }
  catch (erro) {
    botao.disabled = false; delete botao.dataset.busy;
    const aviso = document.querySelector("#ui-tooltip");
    if (aviso) { aviso.textContent = erro.message || "Não foi possível sair."; aviso.hidden = false; }
  }
});
