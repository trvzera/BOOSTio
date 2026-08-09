import { fetchComErro } from "../_shared/fetchComErro.js";

// Autentica o usuário e inicia a sessão (cookie).
// Obs: o backend atual expõe esta rota em /auth/entrar (blueprint auth_bp),
// não em /usuarios/login. Mantido assim para não alterar o comportamento.
export async function login(email, senha) {
  return fetchComErro("/auth/entrar", {
    method: "POST",
    body: JSON.stringify({
      email,
      senha,
    }),
  });
}
