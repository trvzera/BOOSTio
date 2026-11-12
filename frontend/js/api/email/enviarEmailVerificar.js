import { fetchComErro } from "../_shared/fetchComErro.js";


export async function enviarEmailVerificar(id) {
  return fetchComErro(`/email/verificar/enviar/${id}`, {
    method: "POST",
  });
}
