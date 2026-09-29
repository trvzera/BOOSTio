export function avisar(mensagem) {
  let toast = document.querySelector("#builder-feedback");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "builder-feedback";
    toast.setAttribute("role", "status");
    document.body.append(toast);
  }
  toast.textContent = mensagem;
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
  container.innerHTML = '<section class="catalog-empty glass-card"><h1 class="font-1-l">Não foi possível abrir este conteúdo</h1><p class="font-2-s"></p><a class="btn-ghost" data-page-back href="./configuracao-build.html" aria-label="Voltar à build"><span data-back-label>Voltar à build</span></a></section>';
  container.querySelector("p").textContent = erro.message;
}
