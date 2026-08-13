import { fetchComErro } from "../_shared/fetchComErro.js";

// Envia (ou reenvia) o código de verificação de e-mail para o usuário logado.
export async function enviarEmailVerificar(id) {
  return fetchComErro(`/email/enviar/verificar/${id}`, {
    method: "POST",
  });
}
