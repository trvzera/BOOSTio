import { fetchComErro } from "../_shared/fetchComErro.js";


export async function login(email, senha) {
  return fetchComErro("/auth/entrar", {
    method: "POST",
    body: JSON.stringify({
      email,
      senha,
    }),
  });
}

export function confirmarAdmin(codigo) {
  return fetchComErro("/auth/admin/confirmar", {
    method: "POST",
    body: JSON.stringify({ codigo }),
  });
}
