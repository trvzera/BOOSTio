import { fetchComErro } from "../_shared/fetchComErro.js";

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
