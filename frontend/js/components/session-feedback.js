// Mantém o conteúdo privado bloqueado quando não é possível conferir a sessão.
export function mostrarFalhaSessao(erro,tentarNovamente) {
  let dialogo=document.querySelector("#session-connection-dialog");
  if(!dialogo) {
    dialogo=document.createElement("dialog");
    dialogo.id="session-connection-dialog";dialogo.className="session-connection-dialog";
    dialogo.setAttribute("aria-labelledby","session-connection-title");
    dialogo.setAttribute("aria-describedby","session-connection-message");
    dialogo.innerHTML='<h2 id="session-connection-title" class="font-1-m">Não conseguimos verificar sua conta</h2><p id="session-connection-message" class="font-2-xs" role="status"></p><div class="session-connection-actions"><button type="button" class="btn-primary" aria-label="Tentar verificar minha conta novamente">Tentar novamente</button><a class="btn-secondary" href="./index.html" aria-label="Voltar ao início">Ir para o início</a></div>';
    dialogo.querySelector("a").href=new URL("../../pages/index.html",import.meta.url).href;
    dialogo.addEventListener("cancel",evento=>evento.preventDefault());
    document.body.append(dialogo);
  }
  dialogo.querySelector("p").textContent=erro.message||"Confira sua conexão e tente novamente. O serviço também pode estar indisponível por alguns instantes.";
  const botao=dialogo.querySelector("button");
  botao.disabled=false;botao.textContent="Tentar novamente";
  botao.onclick=async()=>{botao.disabled=true;botao.textContent="Verificando…";await tentarNovamente();};
  if(!dialogo.open)dialogo.showModal();
  botao.focus();
}
export function limparFalhaSessao() {
  const dialogo=document.querySelector("#session-connection-dialog");
  if(dialogo?.open)dialogo.close();
  dialogo?.remove();
}
