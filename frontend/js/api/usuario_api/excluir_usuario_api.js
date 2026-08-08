import { API_BASE_URL } from "../../config.js";

export async function excuir_usuario(usuario_id) {
  const response = await fetch(`${API_BASE_URL}/usuarios/${usuario_id}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      "id":usuario_id,
    }),
  });

  return await response.json();
}