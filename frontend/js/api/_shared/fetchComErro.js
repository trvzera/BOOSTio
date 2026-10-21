import { API_URL } from "../../config.js";

// Helper genérico de fetch: sempre envia cookies (credentials: 'include'),
// trata resposta não-ok lançando um Error com a mensagem vinda do backend,
// e devolve o JSON já parseado em caso de sucesso.
export async function fetchComErro(caminho, opcoes = {}) {
  const { headers, ...restoDasOpcoes } = opcoes;

  let resposta;
  try { resposta = await fetch(`${API_URL}${caminho}`, {
    credentials: "include",
    ...restoDasOpcoes,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  }); } catch (causa) {
    if (causa.name === "AbortError") throw causa;
    const offline = typeof navigator !== "undefined" && navigator.onLine === false;
    throw Object.assign(new Error(offline ? "Você está sem internet. Reconecte-se e tente novamente; suas alterações não foram enviadas." : "Não foi possível conectar à BOOSTio. Confira sua conexão e se o servidor está disponível e tente novamente."),{codigo:offline ? "offline" : "conexao",cause:causa});
  }

  if (resposta.status === 204) {
    if (!resposta.ok) {
      throw new Error("Erro ao comunicar com o servidor.");
    }
    return null;
  }
  let dados;
  try { dados = await resposta.json(); }
  catch {
    const erro = new Error("O servidor retornou uma resposta inválida. Tente novamente mais tarde.");
    erro.status = resposta.status;
    throw erro;
  }


  if (!resposta.ok) {
    const erro = new Error(dados.erro || "Erro ao comunicar com o servidor.");
    erro.status = resposta.status;
    erro.codigo = dados.codigo;
    erro.espera = Number.isFinite(dados.espera) && dados.espera > 0 ? dados.espera : 0;
    throw erro;
  }

  return dados;
}
