import { fetchComErro } from "../_shared/fetchComErro.js";

// Verifica se existe um usuário logado na sessão atual.
// Retorna { auth: boolean, usuario: object|null }.
// Obs: o backend atual expõe esta rota em /auth/me (blueprint auth_bp),
// não em /usuarios/me. Mantido assim para não alterar o comportamento.
export async function buscarUsuarioLogado({signal} = {}) {
  return fetchComErro("/auth/me", {
    method: "GET",
    cache: "no-store",
    signal,
  });
}
