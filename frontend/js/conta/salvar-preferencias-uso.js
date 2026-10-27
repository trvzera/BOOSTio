import { atualizarPreferenciasUso } from "../api/usuario/atualizarPreferenciasUso.js";
import { atualizarPerfil, perfilAtual, revisaoPerfil } from "./perfil.js";

export async function salvarPreferenciasDaConta(usuarioId, dados) {
  if (!perfilAtual().auth || perfilAtual().usuario?.id !== usuarioId)
    throw new Error("Entre novamente na sua conta para salvar as preferências.");
  const versao = revisaoPerfil();
  const resposta = await atualizarPreferenciasUso(usuarioId,dados);
  if (resposta?.usuario?.id !== usuarioId || Object.entries(dados).some(([campo,valor]) => resposta.usuario.preferencias_uso?.[campo] !== valor))
    throw new Error("Não conseguimos confirmar suas preferências na resposta. Recarregue para conferir.");
  if (!atualizarPerfil(resposta.usuario,versao))
    throw new Error("A conta ou as preferências mudaram durante o salvamento. Recarregue para conferir.");
  return resposta.usuario;
}
