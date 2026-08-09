import { fetchComErro } from "../_shared/fetchComErro.js";

// Cria um novo usuário. Se o cadastro tiver sucesso o backend já loga o
// usuário (via cookie de sessão).
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
