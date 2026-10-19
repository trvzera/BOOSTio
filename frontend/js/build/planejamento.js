const CHAVE = "boostio:planejamento-local";
export function planejamentoLocal() {
  try {
    const valor = JSON.parse(localStorage.getItem(CHAVE) || "{}");
    return {budget:valor.budget != null && Number.isFinite(Number(valor.budget)) && Number(valor.budget) >= 0 && Number(valor.budget) <= 1000000 ? Number(valor.budget) : null,
      usarBudget:Boolean(valor.usarBudget),setupAtualId:typeof valor.setupAtualId === "string" ? valor.setupAtualId : null};
  } catch { return {budget:null,usarBudget:false,setupAtualId:null}; }
}
export function salvarPlanejamento(alteracoes) {
  const valor = {...planejamentoLocal(),...alteracoes};
  if (valor.budget != null && (!Number.isFinite(Number(valor.budget)) || valor.budget < 0 || valor.budget > 1000000)) throw new Error("Informe um budget entre R$ 0 e R$ 1.000.000.");
  localStorage.setItem(CHAVE,JSON.stringify(valor));
  return valor;
}
