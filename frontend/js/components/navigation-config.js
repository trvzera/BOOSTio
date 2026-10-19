export const linksVisitante = [
  {pagina:"login.html",rotulo:"Entrar",icone:"login"},
  {pagina:"signin.html",rotulo:"Criar conta",icone:"signup"},
];
export const linksAutenticado = [
  {pagina:"index.html",rotulo:"Início"},
  {pagina:"configuracao-build.html",rotulo:"Montar build",icone:"plus"},
  {pagina:"builds.html",rotulo:"Minhas builds",icone:"build"},
  {pagina:"configuracoes-prontas.html",rotulo:"Builds prontas",icone:"build"},
  {pagina:"configuracoes.html",rotulo:"Perfil",icone:"user"},
];
export function redirecionamentoSessao(pagina,autenticado) {
  if (autenticado && ["login.html","signin.html"].includes(pagina)) return "index.html";
  if (!autenticado && ["builds.html","configuracoes.html"].includes(pagina)) return "login.html";
  return null;
}
