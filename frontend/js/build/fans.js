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
export function informacoesFans(gabinete,fans = [],water = null,substituir = false) {
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
  let substituidas = substituir && completas ? Math.min(selecionadas,radiador || 0) : 0;
  let substituicao = true;
  const tamanhoWater = n(water?.tamanho_fan_mm) || null;
  if (substituir && water) {
    substituicao = null;
    if (radiador != null && completas && tamanhoWater != null) substituicao = (demanda.get(tamanhoWater) || 0) >= radiador;
    if (radiador != null && completas && selecionadas < radiador) substituicao = false;
    if (substituicao === true) demanda.set(tamanhoWater,demanda.get(tamanhoWater) - radiador);
    else if (substituicao === false) substituidas = 0;
  }
  const minimo = selecionadas + (inclusas || 0) + (radiador || 0) - substituidas;
  const total = completas && inclusas != null && radiador != null ? minimo : null;
  return {selecionadas:completas ? selecionadas : null,inclusas,radiador,total,capacidade,
    livres:capacidade != null && total != null ? Math.max(0,capacidade-total) : null,
    tamanhos:tamanhoOk,quantidade:capacidade != null && minimo > capacidade ? false : total != null && capacidade != null ? total <= capacidade : null,
    substituidas,substituicao,
    distribuicao:(capacidade != null && minimo > capacidade) || substituicao === false ? false : completas && medidasConhecidas && substituicao === true ? distribuir(grupos,demanda,water,inclusas,gabinete?.posicoes_fans_completas !== false) : null};
}

export function fluxoFan(peca) {
  if (peca?.fluxo_ar === "reverso" || peca?.fluxo_ar === "normal") return peca.fluxo_ar;
  // Identificação comercial, não certificação técnica nem direção de instalação.
  return /\b(reverse|reversa|reverso)\b/i.test(peca?.modelo || "") ? "reverso" : "nao_informado";
}

export function encaixeRadiador(gabinete,water) {
  const limites = gabinete?.limites_radiador_mm;
  if (!Array.isArray(limites) || !limites.length) return null;
  const nominal = n(water?.tamanho_radiador_mm) || null;
  const e = n(water?.espessura_radiador_mm) || null, f = n(water?.espessura_fan_mm) || null;
  const medidas = [n(water?.comprimento_radiador_mm) || null,n(water?.largura_radiador_mm) || null,e != null && f != null ? e+f : null];
  const resultados = [];
  for (const limite of limites) {
    if (!limite || typeof limite !== 'object' || Array.isArray(limite)) { resultados.push(null); continue; }
    const opcoes = tamanhos(limite.tamanhos_mm);
    if (nominal && opcoes != null && !opcoes.includes(nominal)) continue;
    const maximos = [limite.comprimento_mm,limite.largura_mm,limite.espessura_conjunto_mm].map(v => n(v) || null);
    if (medidas.some((m,i) => m != null && maximos[i] != null && m > maximos[i])) resultados.push(false);
    else if ([...medidas,...maximos].every(v => v != null) && nominal && opcoes != null) resultados.push(true);
    else resultados.push(null);
  }
  return resultados.includes(true) ? true : resultados.includes(null) ? null : false;
}

export function orientacoesVentilacao({gabinete,fans = [],water,substituir = false}) {
  const info = informacoesFans(gabinete,fans,water,substituir), avisos = [], dicas = [];
  if (water) {
    dicas.push('O water cooler tem ' + (info.radiador ?? 'quantidade não informada de') + ' fans no catálogo. Elas ocupam posições do gabinete; não são posições extras.');
    dicas.push('Fans avulsas podem substituir as do water cooler se tamanho, furação, espessura, pressão estática e conectores forem adequados. Confira rosca e comprimento dos parafusos no manual; parafusos longos podem danificar o radiador.');
    dicas.push('240/360 mm é o tamanho nominal, não o comprimento externo do radiador. Reserve espaço real para tanques, conexões, tubos e espessura do conjunto; não adicione 3–5 cm como garantia universal.');
    if (substituir) avisos.push('Substituição das fans do water cooler planejada: ' + info.substituidas + ' fan(s) originais deixam de contar como instaladas. A montagem e os parafusos precisam ser conferidos; as peças compradas continuam no preço.');
    else if (info.quantidade === false) avisos.push('O water cooler já vem com fans cadastradas. Remova fans extras ou marque a opção de substituir as fans originais do water cooler; não instale todas no gabinete como fans adicionais.');
  }
  if (fans.length || (gabinete?.fans_inclusos > 0)) {
    dicas.push('Fluxo sugerido, quando o gabinete permitir: entrada de ar pela frente, base ou lateral; saída pelo topo e traseira. A orientação e as setas da fan definem o sentido, não apenas ela ser normal ou reversa.');
    if (fans.some(({peca}) => fluxoFan(peca) === 'reverso')) dicas.push('Há fan identificada como reversa. Ela pode favorecer o acabamento de entradas na base/lateral, mas isso é preferência, não incompatibilidade. Fans normais também podem ser orientadas para entrada; confirme o fluxo no manual.');
    dicas.push('Pode misturar marcas e modelos de fans sem a restrição de DDR/frequência da RAM. Confira dimensões, tensão, conectores PWM/DC e RGB/ARGB, corrente e portas ou hub disponíveis.');
  }
  return {avisos,dicas};
}
