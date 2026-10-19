import { buildsLocais, guardarRascunho, salvarNoPerfilLocal } from "./estado.js";
import { avaliarBuild } from "./compatibilidade.js";

// Chamado somente após uma alteração, nunca ao apenas abrir uma build vazia.
export function salvarAlteracaoLocal(build,catalogo) {
  const salvas = buildsLocais(), existente = salvas.find(item => item.id === build.id);
  if (build.travada || existente?.travada) throw new Error("Destranque a build para salvar alterações.");
  guardarRascunho(build);
  if (!build.titulo.trim()) return {salvo:false,motivo:"Rascunho salvo. Informe um nome para salvar em Minhas builds."};
  if (!existente && salvas.length >= 3) return {salvo:false,motivo:"Rascunho salvo. Limite de três builds atingido; libere espaço para salvar em Minhas builds."};
  const resultado = avaliarBuild(build,catalogo);
  salvarNoPerfilLocal({...build,status:resultado.status,progresso:Math.round(resultado.preenchidos / resultado.total * 100)});
  return {salvo:true,motivo:"Salvo automaticamente neste navegador."};
}
