import { API_URL } from "../../config.js";


export function entrarComGoogle() {
  window.location.href = `${API_URL}/auth/google/redirecionar`;
}
