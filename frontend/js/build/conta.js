import { buscarBuild, catalogoBuilds, atualizarBuild } from "../api/build/builds.js";
import { normalizarBuild, categoriasMultiplas } from "./estado.js";
import { carregarManifestoImagens, completarImagens } from "./imagens-produtos.js";

let catalogoPendente;
export function carregarCatalogoConta() {
  catalogoPendente ??= Promise.all([catalogoBuilds(),carregarManifestoImagens()])
    .then(([resposta,imagens]) => completarImagens(resposta.pecas,imagens)).catch(erro => {
    catalogoPendente = null;
    throw erro;
  });
  return catalogoPendente;
}

export function buildDaConta(dados) {
  const estado = dados.estado || {};
  const componentes = {};
  for (const [tipo, selecao] of Object.entries(estado.componentes || {})) {
    const converter = item => "id" in item
      ? {id:`${tipo}:${String(item.id).split(":").at(-1)}`,quantidade:item.quantidade}
      : item;
    componentes[tipo] = categoriasMultiplas.has(tipo)
      ? (Array.isArray(selecao) ? selecao : [selecao]).map(converter)
      : converter(selecao);
  }
  const build = normalizarBuild({
    ...estado,id:dados.id,titulo:dados.nome,descricao:dados.descricao,
    criadoEm:dados.criado_em,componentes,
  });
  if (["incompativel","nao_verificado","sem_conflitos"].includes(dados.compatibilidade?.status)) build.compatibilidade = dados.compatibilidade;
  return build;
}

export function estadoParaConta(build) {
  return {
    titulo:build.titulo,descricao:build.descricao,visibilidade:build.visibilidade,
    travada:build.travada,orcamento:build.orcamento,
    incluirPerifericos:build.incluirPerifericos,incluirRede:build.incluirRede,
    percentualPerifericos:build.percentualPerifericos || 0,
    rede:build.rede,pecasExtras:build.pecasExtras,componentes:build.componentes,
  };
}

export async function carregarBuildConta(id) {
  const resposta = await buscarBuild(id);
  return buildDaConta(resposta.build);
}

export function salvarBuildConta(build) {
  return atualizarBuild(build.id, estadoParaConta(build));
}

export function linkBuildConta(id) {
  const url = new URL("./configuracao-build.html", location.href);
  url.search = new URLSearchParams({compartilhar_id:id});
  return url.href;
}
