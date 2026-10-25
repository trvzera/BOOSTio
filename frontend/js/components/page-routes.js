// Os arquivos continuam em pages/. O Nginx publica os mesmos documentos sem .html.
export const paginas = new Set([
  "index.html", "login.html", "signin.html", "esqueci-senha.html", "reset-senha.html",
  "formulario.html", "builds.html", "configuracoes.html", "configuracoes-prontas.html",
  "configuracao-build.html", "pecas.html", "peca.html", "sobre.html", "termos.html", "erro.html", "testes.html",
]);
export function nomePagina(caminho) {
  if (String(caminho).endsWith("/pages/")) return "index.html";
  const nome = String(caminho).replace(/\/$/, "").split("/").pop();
  if (!nome) return "index.html";
  return paginas.has(nome + ".html") ? nome + ".html" : nome;
}
export function caminhoComparacao(caminho) {
  const nome = nomePagina(caminho);
  if (!paginas.has(nome)) return caminho;
  const base = String(caminho).replace(/\/$/, "").replace(/\/[^/]*$/, "").replace(/\/pages$/, "");
  return base + "/" + (nome === "index.html" ? "" : nome.replace(/\.html$/, ""));
}
export function paginaDoSite(caminho) {
  return paginas.has(nomePagina(caminho));
}
