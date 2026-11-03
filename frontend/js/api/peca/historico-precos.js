import { fetchComErro } from "../_shared/fetchComErro.js";

export function consultarHistoricoPrecos(categoria, id) {
  return fetchComErro(`/build/catalogo/${encodeURIComponent(categoria)}/${encodeURIComponent(id)}/historico-precos`,
    {method:"GET", cache:"no-store"});
}
