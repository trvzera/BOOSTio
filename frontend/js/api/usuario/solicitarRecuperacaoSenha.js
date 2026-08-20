// frontend/js/api/usuario/solicitarRecuperacaoSenha.js
import { API_URL } from "../../config.js";

export async function solicitarRecuperacaoSenha(email) {
  const response = await fetch(`${API_URL}/usuarios/esqueci-senha`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const erro = await response.json();
    throw new Error(erro.erro || "Falha ao solicitar recuperação de senha.");
  }

  return await response.json();
}