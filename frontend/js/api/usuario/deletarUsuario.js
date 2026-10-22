import { fetchComErro } from "../_shared/fetchComErro.js";

// Exclui a conta do usuário informado.
export async function deletarUsuario(id, senhaAtual) {
  return fetchComErro(`/usuarios/${id}`, {
    method: "DELETE",
    body: JSON.stringify({ senha_atual: senhaAtual }),
  });
}
