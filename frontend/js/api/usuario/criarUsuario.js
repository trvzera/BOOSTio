import { fetchComErro } from "../_shared/fetchComErro.js";

export async function criarUsuario(nome, email, senha) {
  return fetchComErro("/usuarios/", {
    method: "POST",
    body: JSON.stringify({
      nome,
      email,
      senha,
    }),
  });
}
