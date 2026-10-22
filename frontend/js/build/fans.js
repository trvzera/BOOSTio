// Mesmo contrato de services/build_service/encaixe_fisico.py. Sem inferir pelo nome.
const n = v => v == null || v === "" || typeof v === "boolean" || !Number.isFinite(Number(v)) || Number(v) < 0 ? null : Number(v);
const inteiro = (v,min = 0) => Number.isInteger(n(v)) && n(v) >= min && n(v) <= 64 ? n(v) : null;
const tamanhos = v => Array.isArray(v) && v.every(x => n(x) > 0) ? v.map(n) : null;
export function posicoesFans(gabinete) {
  const grupos = gabinete?.posicoes_fans;
  if (!Array.isArray(grupos) || !grupos.length || grupos.length > 12) return null;
  for (const g of grupos) {
    if (!g || !Array.isArray(g.opcoes) || !g.opcoes.length || g.opcoes.length > 8 || !Array.isArray(g.fans_inclusas) || tamanhos(g.radiadores_mm) == null) return null;
    if ([...g.opcoes,...g.fans_inclusas].some(v => !v || !(n(v.tamanho_mm) > 0) || inteiro(v.quantidade,1) == null)) return null;
  }
  return grupos.map(g => ({...g,opcoes:g.opcoes.map(o => ({tamanho_mm:n(o.tamanho_mm),quantidade:inteiro(o.quantidade,1)})),
    fans_inclusas:g.fans_inclusas.map(o => ({tamanho_mm:n(o.tamanho_mm),quantidade:inteiro(o.quantidade,1)})),radiadores_mm:tamanhos(g.radiadores_mm)}));
}
function distribuir(grupos,demanda,water,inclusas,completas) {
  if (!grupos || inclusas == null || grupos.flatMap(g => g.fans_inclusas).reduce((s,f) => s + f.quantidade,0) !== inclusas) return null;
  if (water && (!(n(water.tamanho_fan_mm) > 0) || inteiro(water.quantidade_fans,1) == null || !(n(water.tamanho_radiador_mm) > 0))) return null;
  if (water) water = {...water,tamanho_fan_mm:n(water.tamanho_fan_mm),quantidade_fans:inteiro(water.quantidade_fans,1),tamanho_radiador_mm:n(water.tamanho_radiador_mm)};
  const totais = new Map(demanda);
  for (const f of grupos.flatMap(g => g.fans_inclusas)) totais.set(f.tamanho_mm,(totais.get(f.tamanho_mm) || 0) + f.quantidade);
  if (water) totais.set(water.tamanho_fan_mm,(totais.get(water.tamanho_fan_mm) || 0) + water.quantidade_fans);
  for (const [d,quantidade] of totais) {
    const limite = grupos.reduce((s,g) => s + Math.max(0,...g.opcoes.filter(o => o.tamanho_mm === d).map(o => o.quantidade)),0);
    if (quantidade > limite) return false;
  }
  const diametros = [...demanda.keys()].sort((a,b) => a-b), memo = new Map();
  function tentar(indice,restante,pendente) {
    if (indice === grupos.length) return !restante.some(Boolean) && !pendente;
    const chave = [indice,...restante,pendente].join(":");
    if (memo.has(chave)) return memo.get(chave);
    const g = grupos[indice];
    for (const o of g.opcoes) {
      if (g.fans_inclusas.some(f => f.tamanho_mm !== o.tamanho_mm)) continue;
      const livres = o.quantidade - g.fans_inclusas.reduce((s,f) => s + f.quantidade,0);
      for (const instalar of pendente ? [false,true] : [false]) {
        if (instalar && (!g.radiadores_mm.includes(water.tamanho_radiador_mm) || water.tamanho_fan_mm !== o.tamanho_mm)) continue;
        const vagas = livres - (instalar ? water.quantidade_fans : 0);
        if (vagas < 0) continue;
        const atual = [...restante], i = diametros.indexOf(o.tamanho_mm);
        if (i >= 0) atual[i] = Math.max(0,atual[i] - vagas);
        if (tentar(indice+1,atual,pendente && !instalar)) { memo.set(chave,true); return true; }
      }
    }
    memo.set(chave,false); return false;
  }
  const resultado = tentar(0,diametros.map(d => demanda.get(d)),Boolean(water));
  return resultado || completas ? resultado : null;
}
export function informacoesFans(gabinete,fans = [],water = null) {
  const grupos = posicoesFans(gabinete);
  let capacidade = inteiro(gabinete?.quantidade_max_fans);
  if (grupos) {
    const max = grupos.reduce((s,g) => s + Math.max(...g.opcoes.map(o => o.quantidade)),0);
    capacidade = capacidade == null ? max : Math.min(capacidade,max);
  }
  const inclusas = inteiro(gabinete?.fans_inclusos), radiador = water ? inteiro(water.quantidade_fans,1) : 0;
  let suportados = tamanhos(gabinete?.tamanhos_fan_suportados_mm);
  if (grupos) suportados = [...new Set(grupos.flatMap(g => g.opcoes.map(o => o.tamanho_mm)))];
  let selecionadas = 0, completas = true, medidasConhecidas = true, tamanhoOk = suportados == null ? null : true;
  const demanda = new Map();
  for (const {item,peca} of fans) {
    const kit = inteiro(peca?.quantidade,1), repeticoes = inteiro(item.quantidade ?? 1,1), tamanho = n(peca?.tamanho_mm) || null;
    if (kit == null || repeticoes == null) completas = false;
    else {
      selecionadas += kit * repeticoes;
      if (tamanho) demanda.set(tamanho,(demanda.get(tamanho) || 0) + kit * repeticoes);
    }
    if (tamanho == null) medidasConhecidas = false;
    else if (suportados != null && !suportados.includes(tamanho)) tamanhoOk = false;
  }
  if (tamanhoOk !== false && !medidasConhecidas) tamanhoOk = null;
  const minimo = selecionadas + (inclusas || 0) + (radiador || 0);
  const total = completas && inclusas != null && radiador != null ? minimo : null;
  return {selecionadas:completas ? selecionadas : null,inclusas,radiador,total,capacidade,
    livres:capacidade != null && total != null ? Math.max(0,capacidade-total) : null,
    tamanhos:tamanhoOk,quantidade:capacidade != null && minimo > capacidade ? false : total != null && capacidade != null ? total <= capacidade : null,
    distribuicao:capacidade != null && minimo > capacidade ? false : completas && medidasConhecidas ? distribuir(grupos,demanda,water,inclusas,gabinete?.posicoes_fans_completas !== false) : null};
}
