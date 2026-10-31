import { fetchComErro } from "../_shared/fetchComErro.js";

export async function atualizarPreferenciasUso(usuarioId, dados) {
  const controle = new AbortController(), timeout = setTimeout(() => controle.abort(),10000);
  try {
    return await fetchComErro(`/usuarios/${usuarioId}/preferencias-uso`,{
      method:"PUT",signal:controle.signal,body:JSON.stringify(dados),
    });
  } catch (erro) {
    if (erro.name === "AbortError") throw new Error("Não conseguimos confirmar o salvamento. Confira suas preferências no perfil antes de repetir.");
    throw erro;
  } finally { clearTimeout(timeout); }
}
