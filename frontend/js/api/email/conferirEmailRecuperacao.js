import { fetchComErro } from "../_shared/fetchComErro.js";

// Confere o código de verificação de e-mail digitado pelo usuário logado.
export async function conferirEmailVerificar(email, codigo) {
  return fetchComErro(`/email/recuperar/conferir`, {
    method: "POST",
    body: JSON.stringify({ email, codigo }),
  });
}
