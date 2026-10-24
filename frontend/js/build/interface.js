import { destinoBuild, rotuloVoltar } from "../components/navigation-back.js";
import { anunciarStatus } from "../components/status-messages.js";

export function avisar(mensagem, {urgente = false} = {}) {
  let toast = document.querySelector("#builder-feedback");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "builder-feedback";
    document.body.append(toast);
  }
  toast.textContent = mensagem;
  anunciarStatus(mensagem, {urgente, atraso:urgente ? 50 : 150});
  toast.classList.add("show");
  clearTimeout(avisar.timer);
  avisar.timer = setTimeout(() => toast.classList.remove("show"), 4500);
}

export async function copiarTexto(texto) {
  try {
    await navigator.clipboard.writeText(texto);
    avisar("Link copiado. Quem abrir poderá ver e importar uma cópia da configuração.");
  } catch {
    const campo = document.createElement("textarea");
    campo.value = texto;
    campo.setAttribute("aria-label", "Link para compartilhar");
    const dialogo = document.createElement("dialog");
    dialogo.className = "share-dialog glass-card";
    dialogo.innerHTML = '<h2 class="font-1-l">Compartilhar build</h2><p class="font-2-xs">Copie o link abaixo.</p>';
    const fechar = document.createElement("button");
    fechar.type = "button";
    fechar.className = "btn-ghost";
    fechar.setAttribute("data-ui-close", "");
    fechar.textContent = "Fechar";
    fechar.setAttribute("aria-label", "Fechar compartilhamento da build");
    fechar.onclick = () => { dialogo.close(); dialogo.remove(); };
    dialogo.append(campo, fechar);
    document.body.append(dialogo);
    dialogo.showModal();
    campo.select();
  }
}

export function mostrarFalha(container, erro) {
  const destino = destinoBuild(location.href), rotulo = rotuloVoltar(new URL(destino,location.href));
  container.innerHTML = '<section class="catalog-empty glass-card"><h1 class="font-1-l">Não foi possível abrir este conteúdo</h1><p class="font-2-s" role="alert"></p><a class="btn-ghost" data-page-back data-back-destination href="./builds.html" aria-label="Voltar para Minhas builds"><span data-back-label></span></a></section>';
  const voltar = container.querySelector("a");
  voltar.setAttribute("href",destino);
  voltar.setAttribute("aria-label",rotulo);
  voltar.querySelector("span").textContent = rotulo;
  container.querySelector("p").textContent = erro.message;
}
