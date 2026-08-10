import { fetchComErro } from "../_shared/fetchComErro.js";

// Exclui a conta do usuário informado.
export async function deletarUsuario(id) {
  return fetchComErro(`/usuarios/${id}`, {
    method: "DELETE",
    body: JSON.stringify({ "id_usuario":id }),
  });
}
