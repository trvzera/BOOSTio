import { fetchComErro } from "../_shared/fetchComErro.js";


export async function atualizarUsuario(id, nome, email, senha, senhaAtual) {
  return fetchComErro(`/usuarios/${id}`, {
    method: "PUT",
    body: JSON.stringify({
      nome,
      email,
      senha,
      senha_atual: senhaAtual,
    }),
  });
}
