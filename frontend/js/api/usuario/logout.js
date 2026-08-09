import { fetchComErro } from "../_shared/fetchComErro.js";

// Encerra a sessão do usuário logado.
// Obs: o backend atual expõe esta rota em /auth/sair (blueprint auth_bp),
// não em /usuarios/logout. Mantido assim para não alterar o comportamento.
export async function logout() {
  return fetchComErro("/auth/sair", {
    method: "POST",
  });
}
