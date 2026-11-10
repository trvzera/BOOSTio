
export const TAMANHO_LOTE_IA = 20;
export const ESPERAS_MS = [15000, 45000, 90000];

const somar = ["sugeridas", "sem_sugestao", "aceitas", "rejeitadas", "decisoes_falhas", "ignoradas"];
const dormir = ms => new Promise(resolver => setTimeout(resolver, ms));


export async function processarEnvioIA({
  ids, enviar, tamanho = TAMANHO_LOTE_IA, esperas = ESPERAS_MS, esperar = dormir,
  parou = () => false, aoProgredir = () => {},
}) {
  const total = {feitos: 0, falharam: [], parado: false};
  for (const chave of somar) total[chave] = 0;
  for (let inicio = 0; inicio < ids.length; inicio += tamanho) {
    if (parou()) { total.parado = true; break; }
    let pendentes = ids.slice(inicio, inicio + tamanho);
    for (let tentativa = 0; pendentes.length; tentativa++) {
      let resposta = null;
      try { resposta = await enviar(pendentes); } catch { resposta = null; }
      if (resposta) {
        for (const chave of somar) total[chave] += resposta[chave] || 0;
        pendentes = resposta.ids_falhos || [];
      }
      if (!pendentes.length) break;
      if (tentativa >= esperas.length || parou()) { total.falharam.push(...pendentes); break; }
      aoProgredir({...total, aguardandoMs: esperas[tentativa], tentativa: tentativa + 1});
      await esperar(esperas[tentativa]);
    }
    total.feitos = Math.min(inicio + tamanho, ids.length);
    aoProgredir({...total});
  }
  return total;
}
