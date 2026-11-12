import { consultarHistoricoPrecos, consultarHistoricoOferta } from "../api/peca/historico-precos.js";

export async function obterHistoricoDaPeca(peca, {conta = false, consultar = consultarHistoricoPrecos, ofertaId = null, consultarOferta = consultarHistoricoOferta, lojaOferta = "mercado_livre", loja = null} = {}) {

  if (!conta) return {historico_precos:[], historico_precos_incompleto:false};
  const partes = /^([a-z_]+):([1-9]\d*)$/.exec(peca?.id || "");
  if (!partes || partes[1] !== peca.categoria) throw new Error("Identificação da peça inválida.");
  if (loja !== null) {
    if (!["todas", "kabum", "mercado_livre", "shopee"].includes(loja)) throw new Error("Loja inválida.");
    const dados = await consultar(partes[1], partes[2], loja);
    if (dados?.peca_id !== peca.id || dados?.loja !== loja || !Array.isArray(dados.historico_precos) || typeof dados.tem_mais !== "boolean")
      throw new Error("Resposta do histórico de preços inválida.");
    return {historico_precos:dados.historico_precos, historico_precos_incompleto:dados.tem_mais, historico_loja:loja};
  }
  const mercado = ofertaId !== null;
  if (mercado && (!Number.isSafeInteger(ofertaId) || ofertaId <= 0)) throw new Error("Oferta inválida.");
  if (mercado && !["mercado_livre", "shopee"].includes(lojaOferta)) throw new Error("Loja da oferta inválida.");
  const dados = mercado ? await consultarOferta(partes[1], partes[2], ofertaId) : await consultar(partes[1], partes[2]);
  if (dados?.peca_id !== peca.id || dados?.loja !== (mercado ? lojaOferta : "kabum") || (mercado && dados?.oferta_id !== ofertaId) || !Array.isArray(dados.historico_precos)
      || typeof dados.tem_mais !== "boolean") throw new Error("Resposta do histórico de preços inválida.");
  const resultado = {historico_precos:dados.historico_precos, historico_precos_incompleto:dados.tem_mais};
  if (mercado) resultado.historico_loja = lojaOferta;
  return resultado;
}
