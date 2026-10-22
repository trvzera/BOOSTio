import { API_PUBLICA } from "./config-publica.js";

export function resolverApiUrl(configurada, localizacao) {
  if (configurada) {
    const base = localizacao?.origin || "http://localhost";
    const url = new URL(configurada, base);
    if (!/^https?:$/.test(url.protocol) || url.username || url.password || url.search || url.hash
        || (localizacao?.protocol === "https:" && url.protocol !== "https:")) {
      throw new Error("Configure um endereço HTTP(S) válido e seguro para a API.");
    }
    return url.href.replace(/\/$/, "");
  }
  if (!localizacao) return "http://127.0.0.1:5000";
  if (["localhost", "127.0.0.1"].includes(localizacao.hostname)) {
    return `${localizacao.protocol}//${localizacao.hostname}:5000`;
  }
  return localizacao.origin;
}

export const API_URL = resolverApiUrl(
  API_PUBLICA,
  typeof window !== "undefined" ? window.location : undefined,
);
