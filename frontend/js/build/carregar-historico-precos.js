import { consultarHistoricoPrecos } from "../api/peca/historico-precos.js";

export async function obterHistoricoDaPeca(peca, {conta = false, consultar = consultarHistoricoPrecos} = {}) {
  // IDs do catálogo demonstrativo não identificam os registros do banco.
  if (!conta) return {historico_precos:[], historico_precos_incompleto:false};
  const partes = /^([a-z_]+):([1-9]\d*)$/.exec(peca?.id || "");
  if (!partes || partes[1] !== peca.categoria) throw new Error("Identificação da peça inválida.");
  const dados = await consultar(partes[1], partes[2]);
  if (dados?.peca_id !== peca.id || dados?.loja !== "kabum" || !Array.isArray(dados.historico_precos)
      || typeof dados.tem_mais !== "boolean") throw new Error("Resposta do histórico de preços inválida.");
  return {historico_precos:dados.historico_precos, historico_precos_incompleto:dados.tem_mais};
}
