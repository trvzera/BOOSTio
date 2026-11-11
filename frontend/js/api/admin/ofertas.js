import { fetchComErro } from "../_shared/fetchComErro.js";

export async function removerOferta(id) {
  return fetchComErro(`/admin/ofertas/${encodeURIComponent(id)}/remover`, {method: "POST", body: JSON.stringify({})});
}
