import { fetchComErro } from "../_shared/fetchComErro.js";

export function consultarHistoricoPrecos(categoria, id, loja) {
  const filtro = loja ? `?loja=${encodeURIComponent(loja)}` : "";
  return fetchComErro(`/build/catalogo/${encodeURIComponent(categoria)}/${encodeURIComponent(id)}/historico-precos${filtro}`,
    {method:"GET", cache:"no-store"});
}

export function consultarHistoricoOferta(categoria, id, ofertaId) {
  return fetchComErro(`/build/catalogo/${encodeURIComponent(categoria)}/${encodeURIComponent(id)}/ofertas/${encodeURIComponent(ofertaId)}/historico-precos`,
    {method:"GET", cache:"no-store"});
}
