// Entry point do dashboard de administração (pages/admin.html).
// O conteúdo começa oculto e só aparece depois de confirmado o papel de administrador; o servidor
// confere de novo em cada rota, então esconder aqui é só para não atrapalhar quem não tem acesso.
import "../header.js";
import "../auth/auth.js";
import { carregarPerfil } from "../conta/perfil.js";
import { secoes } from "../admin/secoes.js";

// Quem não é administrador vê "página não encontrada": a área não aparece nem como existente.
const erro404 = () => new URL("./erro.html?codigo=404", new URL("../../pages/", import.meta.url)).href;
const iniciadas = new Set();

function mostrar(id) {
  document.querySelectorAll("[data-admin-secao]").forEach(secao => { secao.hidden = secao.dataset.adminSecao !== id; });
  document.querySelectorAll("[data-admin-menu]").forEach(botao => {
    const atual = botao.dataset.adminMenu === id;
    if (atual) botao.setAttribute("aria-current", "page"); else botao.removeAttribute("aria-current");
  });
  const secao = secoes.find(s => s.id === id);
  if (secao && !iniciadas.has(id)) {
    iniciadas.add(id);
    secao.iniciar(document.querySelector(`[data-admin-secao="${id}"]`));
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const perfil = await carregarPerfil();
    if (!perfil?.auth) return; // auth.js leva para o login
    if (!perfil.usuario?.administrador) { location.replace(erro404()); return; }
  } catch { return; } // auth.js mostra a falha de sessão e permite repetir
  document.title = "Administração — BOOSTio";
  document.getElementById("admin-page").hidden = false;
  document.querySelectorAll("[data-admin-menu]").forEach(botao =>
    botao.addEventListener("click", () => mostrar(botao.dataset.adminMenu)));
  mostrar(secoes[0].id);
});
