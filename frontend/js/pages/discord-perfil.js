import { fetchComErro } from "../api/_shared/fetchComErro.js";

const mensagens = new Map([
  ["conectado", "Discord conectado com sucesso."],
  ["cancelado", "A autorização foi cancelada."],
  ["expirado", "A solicitação expirou. Selecione Conectar Discord para tentar novamente."],
  ["conflito", "Esta conta do Discord já está vinculada ou o vínculo deste perfil mudou."],
  ["erro", "Não foi possível conectar o Discord. Tente novamente."],
]);

document.addEventListener("DOMContentLoaded", () => {
  const card = document.querySelector("#discord-settings");
  if (!card) return;

  const status = card.querySelector("#discord-status");
  const feedback = card.querySelector("#discord-feedback");
  const conectar = card.querySelector("#connect-discord");
  const desconectar = card.querySelector("#disconnect-discord");
  const repetir = card.querySelector("#retry-discord");
  const rota = "/auth/discord";

  async function carregarVinculo() {
    conectar.hidden = desconectar.hidden = repetir.hidden = true;
    status.textContent = "Consultando conexão com o Discord…";
    try {
      const {disponivel, nome} = await fetchComErro(rota, {cache:"no-store"});
      status.textContent = nome ? "Conectado como @" + nome
        : disponivel ? "Nenhuma conta Discord vinculada." : "A conexão com o Discord está indisponível.";
      conectar.hidden = Boolean(nome) || !disponivel;
      desconectar.hidden = !nome;
    } catch {
      status.textContent = "Não foi possível consultar a conexão com o Discord.";
      repetir.hidden = false;
    }
  }

  conectar.addEventListener("click", async () => {
    conectar.disabled = true;
    feedback.textContent = "Abrindo a autorização no Discord…";
    try {
      const resposta = await fetchComErro(rota + "/vincular", {method:"POST"});
      const destino = new URL(resposta.url);
      if (destino.origin !== "https://discord.com" || destino.pathname !== "/oauth2/authorize")
        throw new Error("Não foi possível abrir a autorização do Discord.");
      location.assign(destino);
    } catch (erro) {
      feedback.textContent = erro.message;
      conectar.disabled = false;
    }
  });

  desconectar.addEventListener("click", async () => {
    desconectar.disabled = true;
    feedback.textContent = "Desconectando o Discord…";
    try {
      await fetchComErro(rota, {method:"DELETE"});
      feedback.textContent = "Discord desconectado da BOOSTio.";
      await carregarVinculo();
      if (!conectar.hidden) conectar.focus();
    } catch (erro) {
      feedback.textContent = erro.message;
    } finally {
      desconectar.disabled = false;
    }
  });

  repetir.addEventListener("click", carregarVinculo);
  const url = new URL(location.href);
  const retorno = url.searchParams.get("discord");
  if (mensagens.has(retorno)) {
    feedback.textContent = mensagens.get(retorno);
    url.searchParams.delete("discord");
    history.replaceState(history.state, "", url);
  }
  void carregarVinculo();
  window.addEventListener("pageshow", evento => {
    if (evento.persisted) {
      conectar.disabled = false;
      void carregarVinculo();
    }
  });
});
