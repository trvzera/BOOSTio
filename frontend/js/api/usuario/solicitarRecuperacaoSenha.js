import { fetchComErro } from "../_shared/fetchComErro.js";

export async function solicitarRecuperacaoSenha(email) {
  return fetchComErro("/usuarios/esqueci-senha", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}
