import { API_BASE_URL } from "../../config.js";

export async function logar_usuario(email, senha) {
  const response = await fetch(`${API_BASE_URL}/auth/entrar`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      "email":email,
      "senha":senha,
    }),
  });

  return await response.json();
}
