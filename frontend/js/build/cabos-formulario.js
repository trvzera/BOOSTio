export function comprimentosCabosCatalogo(pecas = []) {
  return [
    ...new Set(
      pecas
        .filter(
          (p) =>
            p.categoria === "cabo_rede" &&
            p.esgotado === false &&
            Number.isFinite(Number(p.preco)) &&
            Number(p.preco) > 0 &&
            /\bcat(?:egoria)?[\s.-]*6a?\b/i.test(
              [p.categoria_cabo, p.modelo].filter(Boolean).join(" "),
            ),
        )
        .map((p) => Number(p.comprimento_m))
        .filter((m) => Number.isFinite(m) && m > 0),
    ),
  ].sort((a, b) => a - b);
}
export function validarCaboFormulario(rede = {}, comprimentos = []) {
  if (!["cabo", "ambos"].includes(rede.tipo) || rede.possuiAcessorio !== false)
    return "";
  return comprimentos.includes(rede.comprimentoCaboM)
    ? ""
    : "Escolha um comprimento de cabo disponível no catálogo, ou compre esse acessório separadamente.";
}
