import { API_URL } from "../../config.js";

// Login com Google não usa fetch: precisa de uma navegação de página inteira
// para o backend, que redireciona pro Google e depois volta com o cookie de
// sessão já setado (fluxo OAuth de authlib + flask-login).
export function entrarComGoogle() {
  window.location.href = `${API_URL}/auth/google/redirecionar`;
}
