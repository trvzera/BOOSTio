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
