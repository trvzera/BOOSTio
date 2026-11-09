export function separarCodigos(peca) {
  if (typeof peca.part_number !== 'string' || !/^(KABUM|SEED|REDE|DEMO|BOOSTIO)[-_]/i.test(peca.part_number.trim())) return peca;
  return {...peca, referencia_interna: peca.referencia_interna || peca.part_number, part_number: null};
}

export function referenciasPeca(peca) {
  return [peca.referencia_interna, peca.part_number].filter(Boolean);
}
