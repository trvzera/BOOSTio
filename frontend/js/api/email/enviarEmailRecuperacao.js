import { fetchComErro } from "../_shared/fetchComErro.js";

// Envia (ou reenvia) o código de verificação de e-mail para o usuário logado.
export async function enviarEmailVerificar(email) {
  return fetchComErro(`/email/recuperar/enviar`, {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}
