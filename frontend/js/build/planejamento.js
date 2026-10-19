const CHAVE = "boostio:planejamento-local";
let budgetPerfil = {budget:null,usarBudget:false};

// Projeção em memória da conta consultada; nunca transfere budget entre contas.
export function sincronizarBudgetPerfil(usuario) {
  const valor = usuario?.budget;
  const valido = Number.isInteger(usuario?.id) && usuario.id > 0 && typeof valor === "number" &&
    Number.isFinite(valor) && valor >= 0 && valor <= 1000000;
  budgetPerfil = {budget:valido ? valor : null,usarBudget:valido && valor > 0 && usuario.usar_budget === true};
}

export function planejamentoLocal() {
  let setupAtualId = null;
  try {
    const valor = JSON.parse(localStorage.getItem(CHAVE) || "{}");
    setupAtualId = typeof valor?.setupAtualId === "string" ? valor.setupAtualId : null;
  } catch { /* O budget da conta não depende do localStorage. */ }
  return {...budgetPerfil,setupAtualId};
}
export function salvarPlanejamento(alteracoes) {
  if ("budget" in alteracoes || "usarBudget" in alteracoes) throw new Error("Salve o budget nas configurações da conta.");
  const setupAtualId = alteracoes.setupAtualId === null || typeof alteracoes.setupAtualId === "string"
    ? alteracoes.setupAtualId : planejamentoLocal().setupAtualId;
  localStorage.setItem(CHAVE,JSON.stringify({setupAtualId}));
  return planejamentoLocal();
}
