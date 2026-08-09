import { fetchComErro } from "../_shared/fetchComErro.js";

// Atualiza dados do usuário (nome, email e/ou senha). Campos não informados
// devem ser passados como undefined, exatamente como no backend atual.
export async function atualizarUsuario(id, nome, email, senha, senhaAtual) {
  return fetchComErro(`/usuarios/${id}`, {
    method: "PUT",
    body: JSON.stringify({
      nome,
      email,
      senha,
      senha_atual: senhaAtual,
    }),
  });
}
