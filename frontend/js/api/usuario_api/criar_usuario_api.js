import { API_BASE_URL } from "../../config.js";

export async function criar_usuario(usuario, email, senha) {
  const response = await fetch(`${API_BASE_URL}/usuarios/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      "nome": usuario,
      "email":email,
      "senha":senha,
    }),
  });

  return await response.json();
}