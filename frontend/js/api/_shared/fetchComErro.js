import { API_URL } from "../../config.js";

// Helper genérico de fetch: sempre envia cookies (credentials: 'include'),
// trata resposta não-ok lançando um Error com a mensagem vinda do backend,
// e devolve o JSON já parseado em caso de sucesso.
export async function fetchComErro(caminho, opcoes = {}) {
  const { headers, ...restoDasOpcoes } = opcoes;

  const resposta = await fetch(`${API_URL}${caminho}`, {
    credentials: "include",
    ...restoDasOpcoes,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  });

  const dados = await resposta.json();

  if (!resposta.ok) {
    throw new Error(dados.erro || "Erro ao comunicar com o servidor.");
  }

  return dados;
}
