import { fetchComErro } from "../_shared/fetchComErro.js";


export async function deletarUsuario(id, senhaAtual) {
  return fetchComErro(`/usuarios/${id}`, {
    method: "DELETE",
    body: JSON.stringify({ senha_atual: senhaAtual }),
  });
}
