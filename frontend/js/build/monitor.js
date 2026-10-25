export function resumoMonitor(peca) {
  if (!peca) return "";
  const hz = Number(peca.taxa_atualizacao_hz);
  const frequencia = Number.isFinite(hz) && hz > 0 ? hz + " Hz" : "Hz não informados";
  const resolucao = typeof peca.resolucao === "string" && peca.resolucao.trim()
    ? peca.resolucao.trim().replace(/\s*[x×]\s*/gi," × ") : "Resolução não informada";
  return frequencia + " · " + resolucao;
}
