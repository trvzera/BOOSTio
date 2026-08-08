import { API_BASE_URL } from "../../config.js";

export async function atualizar_usuario(usuario, email, senha, id, senha_atual) {
  const response = await fetch(`${API_BASE_URL}/usuarios/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      "nome": usuario,
      "email": email,
      "senha": senha,
      "senha_atual": senha_atual,
    }),
  });

  return await response.json();
}