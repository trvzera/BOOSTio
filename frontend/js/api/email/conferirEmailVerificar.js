import { fetchComErro } from "../_shared/fetchComErro.js";

// Confere o código de verificação de e-mail digitado pelo usuário logado.
export async function conferirEmailVerificar(id, codigo) {
  return fetchComErro(`/email/conferir/verificar/${id}`, {
    method: "POST",
    body: JSON.stringify({ codigo }),
  });
}
