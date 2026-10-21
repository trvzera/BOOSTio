import { carregarPerfil, limparPerfil } from "../conta/perfil.js";
import { logout } from "../api/usuario/logout.js";
import { atualizarMenu } from "../components/menu.js";
import { paginaPrivada, redirecionamentoSessao } from "../components/navigation-config.js";
import { acompanharCarregamento } from "../components/page-loading.js";
import { verificarEspacoBuild } from "../api/build/builds.js";

const privada = paginaPrivada(location.pathname.split("/").pop());
function bloquearConteudo() {
  if (!privada) return;
  document.body.dataset.sessionState = "checking";
  const main = document.querySelector("main");
  if (main) main.inert = true;
}

export function caminhoLogin() { return new URL("../../pages/login.html",import.meta.url).href; }
export async function confirmaUsuario() {
  const resposta = await carregarPerfil();
  const autenticado = Boolean(resposta?.auth);
  atualizarMenu(autenticado);
  const destino = redirecionamentoSessao(location.pathname.split("/").pop(),autenticado);
  if (destino) location.replace(new URL("../../pages/" + destino,import.meta.url).href);
  else {
    if (location.pathname.endsWith("/formulario.html")) {
      try { await verificarEspacoBuild(resposta); }
      catch (erro) {
        const pagina = erro.codigo === "email-nao-verificado" ? "configuracoes.html?verificar=1" : "builds.html?aviso=" + encodeURIComponent(erro.message);
        location.replace(new URL("../../pages/" + pagina,import.meta.url).href);
        return resposta;
      }
    }
    document.body.dataset.sessionState = "authorized";
    const main = document.querySelector("main");
    if (main) main.inert = false;
  }
  return resposta;
}
async function conferirSessao() {
  bloquearConteudo();
  try { await confirmaUsuario(); }
  catch (erro) {
    console.warn("Não foi possível consultar a sessão do usuário:",erro);
    atualizarMenu(false);
    if (privada) location.replace(caminhoLogin()); // Falha de sessão nunca libera páginas internas.
  }
}
const iniciarVerificacao = () => acompanharCarregamento(conferirSessao());
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded",iniciarVerificacao,{once:true});
else iniciarVerificacao();
window.addEventListener("pagehide",bloquearConteudo);
window.addEventListener("pageshow",e => { if (e.persisted) { limparPerfil(); conferirSessao(); } });
document.addEventListener("click",async e => {
  if (!e.target.closest("#btn-logout")) return;
  e.preventDefault();
  const botao = document.querySelector("#btn-logout");
  botao.disabled = true; botao.dataset.busy = "true";
  try { await logout(); limparPerfil(); location.href = caminhoLogin(); }
  catch (erro) {
    botao.disabled = false; delete botao.dataset.busy;
    const aviso = document.querySelector("#ui-tooltip");
    if (aviso) { aviso.textContent = erro.message || "Não foi possível sair."; aviso.hidden = false; }
  }
});
