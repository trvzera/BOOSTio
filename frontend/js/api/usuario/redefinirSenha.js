// frontend/js/api/usuario/redefinirSenha.js
import { API_URL } from "../../config.js";

export async function redefinirSenha(token, novaSenha) {
  const response = await fetch(`${API_URL}/usuarios/redefinir-senha`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, senha: novaSenha }),
  });

  if (!response.ok) {
    const erro = await response.json();
    throw new Error(erro.erro || "Falha ao redefinir senha.");
  }

  return await response.json();
}