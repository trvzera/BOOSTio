import { fetchComErro } from "../_shared/fetchComErro.js";

// Rotas de administração das pendências de ofertas (backend: /admin/pendencias).
// O backend recusa quem não é administrador (403); aqui só montamos os pedidos.
export function montarConsultaPendencias({status = "em_revisao", loja = "", categoria = "", depoisId = 0, limite = 20} = {}) {
  const parametros = new URLSearchParams({status, limite: String(limite)});
  if (loja) parametros.set("loja", loja);
  if (categoria) parametros.set("categoria", categoria);
  if (depoisId > 0) parametros.set("depois_id", String(depoisId));
  return parametros.toString();
}

export async function listarPendencias(filtros = {}, {signal} = {}) {
  return fetchComErro("/admin/pendencias?" + montarConsultaPendencias(filtros), {method: "GET", cache: "no-store", signal});
}

export async function detalharPendencia(id, {signal} = {}) {
  return fetchComErro(`/admin/pendencias/${encodeURIComponent(id)}`, {method: "GET", cache: "no-store", signal});
}

export async function aceitarPendencia(id, peca) {
  return fetchComErro(`/admin/pendencias/${encodeURIComponent(id)}/aceitar`, {
    method: "POST", body: JSON.stringify({peca}),
  });
}

export async function rejeitarPendencia(id, motivo = "") {
  return fetchComErro(`/admin/pendencias/${encodeURIComponent(id)}/rejeitar`, {
    method: "POST", body: JSON.stringify({motivo}),
  });
}

export async function descartarCandidato(id, peca) {
  return fetchComErro(`/admin/pendencias/${encodeURIComponent(id)}/candidatos/descartar`, {
    method: "POST", body: JSON.stringify({peca}),
  });
}

export async function enviarPendenciasParaIA(ids) {
  return fetchComErro("/admin/pendencias/enviar-ia", {method: "POST", body: JSON.stringify({ids})});
}
