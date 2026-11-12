import { fetchComErro } from "../_shared/fetchComErro.js";


export async function conferirEmailVerificar(id, codigo) {
  return fetchComErro(`/email/verificar/conferir/${id}`, {
    method: "POST",
    body: JSON.stringify({ codigo }),
  });
}
