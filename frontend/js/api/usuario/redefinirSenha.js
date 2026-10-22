import { fetchComErro } from "../_shared/fetchComErro.js";

export async function redefinirSenha(token, novaSenha) {
  return fetchComErro("/usuarios/redefinir-senha", {
    method: "POST",
    body: JSON.stringify({ token, senha: novaSenha }),
  });
}
