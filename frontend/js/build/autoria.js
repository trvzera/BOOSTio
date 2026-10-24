import { htmlSeguro } from "./catalogo.js";

// Metadado da resposta da API: nunca é enviado como autoria numa gravação.
export function autoriaBuildHtml(build) {
  const nome = typeof build?.criador?.nome === "string" ? build.criador.nome.trim() : "";
  if (!nome) return "";
  return '<p class="build-author"><span>Criada por</span> <strong>' + htmlSeguro(nome.slice(0,30)) + '</strong></p>';
}
