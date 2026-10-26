export const MINIMO_PC_GERACAO = 2000;
export const MINIMO_PERIFERICOS_GERACAO = 500;

export function orcamentoValido(valor) {
  return typeof valor === "number" && Number.isFinite(valor) && valor > 0 && valor <= 1000000 &&
    Math.abs(valor * 100 - Math.round(valor * 100)) < 0.000001;
}

export function dividirOrcamento(total, percentual) {
  if (!orcamentoValido(total) || !Number.isInteger(percentual) || percentual < 0 || percentual > 99) return null;
  const centavos = Math.round(total * 100);
  const reserva = Math.floor(centavos * percentual / 100);
  return {pc:(centavos - reserva) / 100, perifericos:reserva / 100};
}


export function avaliarOrcamentoGeracao(total, percentual = 0) {
  const divisao = dividirOrcamento(total, percentual);
  if (!divisao) return {valido:false,motivo:"orcamento",mensagem:"Informe um orçamento válido e uma porcentagem inteira de 0 a 99."};
  const minimoTotal = Math.ceil(Math.max(MINIMO_PC_GERACAO * 100 / (100 - percentual), percentual ? MINIMO_PERIFERICOS_GERACAO * 100 / percentual : 0) / 100) * 100;
  if (divisao.pc < MINIMO_PC_GERACAO) return {valido:false,motivo:"orcamento",minimoTotal,...divisao,
    mensagem:"Reserve pelo menos R$ 2.000 para o PC, depois de descontar os periféricos."};
  if (percentual && divisao.perifericos < MINIMO_PERIFERICOS_GERACAO) return {valido:false,motivo:"perifericos",minimoTotal,...divisao,
    mensagem:"Reserve pelo menos R$ 500 para periféricos novos. O conjunto do catálogo pode exigir mais."};
  return {valido:true,minimoTotal,...divisao};
}
