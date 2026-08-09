// Funções puras de formatação de moeda. Sem fetch, sem DOM.

// Formata um número para o padrão monetário brasileiro: "R$ 1.234,56".
export function formatarReal(valor) {
  return Number(valor).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}
