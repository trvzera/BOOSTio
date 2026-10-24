import { idCompartilhamentoPublico } from './sessao-publica.js';

export const linksVisitante = [
  {pagina:"login.html",rotulo:"Entrar",icone:"login"},
  {pagina:"signin.html",rotulo:"Criar conta",icone:"signup"},
];
export const linksAutenticado = [
  {pagina:"index.html",rotulo:"Início",icone:"build"},
  {pagina:"builds.html",rotulo:"Minhas builds",icone:"build",autenticado:true},
  {pagina:"builds.html?criar=1",rotulo:"Criar build",icone:"plus"},
  {pagina:"termos.html",rotulo:"Termos e condições",icone:"download"},
  {pagina:"sobre.html",rotulo:"Sobre nós",icone:"user"},
];
export const paginasPublicas = new Set([
  "", "index.html", "termos.html", "sobre.html", "contato.html",
  "login.html", "signin.html", "esqueci-senha.html", "reset-senha.html", "erro.html",
]);
export function paginaPrivada(pagina,busca = '') {
  return !(pagina === 'configuracao-build.html' && idCompartilhamentoPublico(busca)) && !paginasPublicas.has(pagina);
}
export function redirecionamentoSessao(pagina,autenticado,busca = '') {
  if (autenticado && ["login.html","signin.html"].includes(pagina)) return "index.html";
  if (!autenticado && paginaPrivada(pagina,busca)) return "login.html";
  return null;
}
