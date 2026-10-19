import { fetchComErro } from "../_shared/fetchComErro.js";

export async function atualizarBudgetUsuario(usuarioId, budget, usarBudget) {
  const controle = new AbortController(), timeout = setTimeout(() => controle.abort(),10000);
  try {
    return await fetchComErro(`/usuarios/${usuarioId}/budget`, {
      method:"PUT", signal:controle.signal,
      body:JSON.stringify({budget,usar_budget:usarBudget}),
    });
  } catch (erro) {
    if (erro.name === "AbortError") throw new Error("Não foi possível confirmar o salvamento. Recarregue para verificar o budget.");
    throw erro;
  } finally { clearTimeout(timeout); }
}
