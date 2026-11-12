import { fetchComErro } from "../_shared/fetchComErro.js";


export async function logout() {
  return fetchComErro("/auth/sair", {
    method: "POST",
  });
}
