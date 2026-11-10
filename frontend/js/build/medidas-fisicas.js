import { referenciasPeca } from './codigos-pecas.js';

function produtoKabum(link) {
  if (typeof link !== "string" || /[\s\\]/.test(link)
      || !/^https:\/\/(?:www\.)?kabum\.com\.br(?::443)?\//i.test(link)) return null;
  try {
    const url = new URL(link);
    if (url.protocol !== "https:" || !["kabum.com.br","www.kabum.com.br"].includes(url.hostname)
        || url.username || url.password || url.port) return null;

    const caminho = /^https:\/\/[^/?#]+(\/[^?#]*)/i.exec(link)?.[1];
    return /^\/produto\/([1-9][0-9]*)(?:\/[a-zA-Z0-9_-]+)?\/?$/.exec(caminho)?.[1] ?? null;
  } catch { return null; }
}

function corresponde(peca,ficha) {
  if (peca.categoria !== ficha.categoria) return false;
  const nomes = ref => ["fabricante","modelo"].every(k => String(peca[k] || "").toLowerCase() === ref[k].toLowerCase());
  const referencias = referenciasPeca(peca);
  if (nomes(ficha) && ficha.part_numbers.some(codigo => referencias.includes(codigo))) return true;
  return (ficha.aliases_catalogo || []).some(alias => nomes(alias) && referencias.includes(alias.part_number)
    && produtoKabum(peca.link) === alias.produto_kabum);
}

export function completarMedidas(peca,manifesto = {pecas:[]}) {
  const ficha = manifesto.pecas.find(f => corresponde(peca,f));
  if (!ficha) return peca;
  return {...peca,...JSON.parse(JSON.stringify(ficha.medidas)),fonte_medidas:ficha.fonte,
    ...(ficha.verificado_em ? {modelo_ficha_tecnica:ficha.modelo,ficha_tecnica_verificada_em:ficha.verificado_em} : {})};
}
