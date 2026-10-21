import { fetchComErro } from "../_shared/fetchComErro.js";
import { carregarPerfil } from "../../conta/perfil.js";

export const LIMITE_BUILDS = 3;
export async function verificarEspacoBuild(perfil) {
  const sessao = perfil || await carregarPerfil();
  if (!sessao.auth) throw Object.assign(new Error("Entre na sua conta para criar uma build."),{status:401});
  if (!sessao.usuario?.verificado) throw Object.assign(new Error("Verifique seu e-mail nas configurações do perfil antes de criar uma build."),{status:403,codigo:"email-nao-verificado"});
  const resposta = await listarBuilds();
  if (resposta.builds.length >= LIMITE_BUILDS) {
    const erro = new Error("Você atingiu o limite de três builds. Exclua uma para liberar espaço.");
    erro.codigo = "limite-builds";
    throw erro;
  }
}

export function criarBuild(dados) {
  return fetchComErro("/build/", { method: "POST", body: JSON.stringify(dados) });
}

export function listarBuilds() {
  return fetchComErro("/build/", { method: "GET" });
}

export function buscarBuild(id) {
  return fetchComErro(`/build/${encodeURIComponent(id)}`, { method: "GET" });
}

export function catalogoBuilds() {
  return fetchComErro("/build/catalogo", { method: "GET" });
}

export function criarBuildManual(dados) {
  return fetchComErro("/build/manual", { method: "POST", body: JSON.stringify(dados) });
}

export function atualizarBuild(id, dados) {
  return fetchComErro(`/build/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(dados) });
}

export function duplicarBuild(id) {
  return fetchComErro(`/build/${encodeURIComponent(id)}/duplicar`, { method: "POST" });
}

export function excluirBuild(id) {
  return fetchComErro(`/build/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function definirSetupAtual(id) {
  return fetchComErro(`/build/${encodeURIComponent(id)}/setup-atual`, { method: "POST" });
}
