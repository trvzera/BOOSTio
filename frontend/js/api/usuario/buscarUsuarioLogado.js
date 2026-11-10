import { fetchComErro } from "../_shared/fetchComErro.js";


export async function buscarUsuarioLogado({signal} = {}) {
  return fetchComErro("/auth/me", {
    method: "GET",
    cache: "no-store",
    signal,
  });
}
