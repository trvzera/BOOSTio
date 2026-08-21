// Funções puras de formatação de data. Sem fetch, sem DOM.

const MESES_PT = [
  "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
  "Jul", "Ago", "Set", "Out", "Nov", "Dez",
];

// Recebe uma data no formato retornado pelo backend (ex.:
// "Sat, 08 Aug 2026 00:31:20 GMT") e retorna "Ago 2026".
export function formatarMesAno(dataString) {
  const data = new Date(dataString);
  const mes = MESES_PT[data.getUTCMonth()];
  const ano = data.getUTCFullYear();

  return `${mes} ${ano}`;
}

// Recebe datetime do backend e retorna "15 Ago 2026, 14:32".
export function formatarDataHora(dataString) {
  const data = new Date(dataString);
  const dia = String(data.getDate()).padStart(2, "0");
  const mes = MESES_PT[data.getMonth()];
  const ano = data.getFullYear();
  const horas = String(data.getHours()).padStart(2, "0");
  const minutos = String(data.getMinutes()).padStart(2, "0");

  return `${dia} ${mes} ${ano}, ${horas}:${minutos}`;
}
