const CHAVE_TOKEN = "boostio_token";

export function getToken() {
  return localStorage.getItem(CHAVE_TOKEN);
}

export function setToken(token) {
  localStorage.setItem(CHAVE_TOKEN, token);
}

export function removerToken() {
  localStorage.removeItem(CHAVE_TOKEN);
}

export function usuarioEstaLogado() {
  return getToken() !== null;
}