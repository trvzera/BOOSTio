

const MESES_PT = [
  "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
  "Jul", "Ago", "Set", "Out", "Nov", "Dez",
];


export function formatarMesAno(dataString) {
  const data = new Date(dataString);
  const mes = MESES_PT[data.getUTCMonth()];
  const ano = data.getUTCFullYear();

  return `${mes} ${ano}`;
}


export function formatarDataHora(dataString) {
  const data = new Date(dataString);
  const dia = String(data.getDate()).padStart(2, "0");
  const mes = MESES_PT[data.getMonth()];
  const ano = data.getFullYear();
  const horas = String(data.getHours()).padStart(2, "0");
  const minutos = String(data.getMinutes()).padStart(2, "0");

  return `${dia} ${mes} ${ano}, ${horas}:${minutos}`;
}
