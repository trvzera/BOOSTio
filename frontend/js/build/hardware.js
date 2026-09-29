// Campos ausentes são desconhecidos, nunca zero ou uma medida inferida pelo nome.
export function numeroConhecido(valor) {
  if (valor == null || valor === "" || typeof valor === "boolean") return null;
  const n = Number(valor);
  return Number.isFinite(n) && n >= 0 ? n : null;
}
export function conexaoDisco(peca) {
  if (!peca) return null;
  const formato = String(peca.formato || "").toUpperCase();
  const interfacePeca = String(peca.interface || peca.tipo || "").toUpperCase();
  if (/M\.?2|NVME|PCI[E-]/.test(formato + " " + interfacePeca))
    return /SATA/.test(interfacePeca) ? "m2-sata" : "m2";
  if (/SATA/.test(interfacePeca)) return "sata";
  return null;
}
export function limitesArmazenamento(placa, m2Sata = 0) {
  const sata = numeroConhecido(placa?.quantidade_portas_sata);
  const compartilhadas = numeroConhecido(placa?.portas_sata_desativadas_por_m2_sata);
  return {
    m2:numeroConhecido(placa?.quantidade_slots_m2),
    m2Sata:numeroConhecido(placa?.quantidade_slots_m2_sata),
    sata:sata == null ? null : Math.max(0,sata - m2Sata * (compartilhadas ?? 0)),
    compartilhamentoDesconhecido:m2Sata > 0 && compartilhadas == null,
  };
}
function medidas(valor) {
  if (valor == null) return null;
  return (Array.isArray(valor) ? valor : String(valor).split(/[,;/]/))
    .map(v => numeroConhecido(String(v).trim().replace(/\s*mm$/i,""))).filter(v => v != null);
}
export function validarEncaixe({gpu,air,water,fans,gabinete}) {
  const erros = [], avisos = [];
  if (!gabinete) return {erros,avisos};
  const checarMedida = (peca,medida,limite,nome) => {
    if (!peca) return;
    const tamanho = numeroConhecido(medida), maximo = numeroConhecido(limite);
    if (tamanho == null || maximo == null) avisos.push("Faltam medidas para confirmar o encaixe " + nome + " no gabinete.");
    else if (tamanho > maximo) erros.push("O tamanho " + nome + " (" + tamanho + " mm) ultrapassa o limite do gabinete (" + maximo + " mm).");
  };
  checarMedida(gpu,gpu?.comprimento_mm,gabinete.tamanho_max_gpu_mm,"da placa de vídeo");
  // O catálogo antigo usa dimensoes como altura numérica; L×A×P não é interpretado.
  checarMedida(air,air?.altura_mm ?? numeroConhecido(air?.dimensoes),gabinete.tamanho_max_cooler_mm,"do air cooler");
  const radiadores = medidas(gabinete.radiadores_suportados_mm);
  const tamanhoRadiador = numeroConhecido(water?.tamanho_radiador_mm);
  if (water) {
    if (gabinete.suporte_water_cooler === false) erros.push("O gabinete não suporta water cooler.");
    else if (tamanhoRadiador != null && radiadores != null && !radiadores.includes(tamanhoRadiador))
      erros.push("O gabinete não suporta radiador de " + tamanhoRadiador + " mm.");
    else if (tamanhoRadiador == null || radiadores == null)
      avisos.push("Confirme os tamanhos de radiador suportados pelo gabinete; suporte a water cooler não garante encaixe de 360 mm.");
  }
  const tamanhos = medidas(gabinete.tamanhos_fan_suportados_mm);
  let quantidade = 0;
  for (const {peca,item} of fans) {
    const tamanho = numeroConhecido(peca?.tamanho_mm);
    quantidade += Number(peca?.quantidade || 1) * item.quantidade;
    if (!peca) continue;
    if (tamanho != null && tamanhos != null && !tamanhos.includes(tamanho))
      erros.push("O gabinete não suporta fans de " + tamanho + " mm.");
    else if (tamanho == null || tamanhos == null) avisos.push("Falta o tamanho dos encaixes de fans do gabinete para confirmar a instalação.");
  }
  const maxFans = numeroConhecido(gabinete.quantidade_max_fans);
  const inclusas = numeroConhecido(gabinete.fans_inclusos);
  const fansRadiador = water ? numeroConhecido(water.quantidade_fans) : 0;
  if (fans.length || water) {
    if (maxFans == null || inclusas == null || fansRadiador == null)
      avisos.push("Falta a capacidade de fans do gabinete para conferir a quantidade total, incluindo as fans inclusas e as do radiador.");
    else if (quantidade + inclusas + fansRadiador > maxFans)
      erros.push("Há mais fans do que posições no gabinete, contando as inclusas e as do radiador. Remova um kit ou use menos fans.");
    if (fans.length && water) avisos.push("Confirme a distribuição das fans e do radiador: encaixes de tamanhos diferentes podem compartilhar a mesma posição.");
  }
  return {erros,avisos};
}

// Complemento SOMENTE do catálogo demonstrativo. Não altera modelos ou seed Python.
// Documentação das revisões de referência: docs/frontend-build.md.
export function completarCatalogoDemo(catalogo) {
  const placas = {
    "ASUS|Prime A520M-K": {quantidade_slots_m2:1,quantidade_portas_sata:4,quantidade_slots_m2_sata:1},
    "Gigabyte|B550M DS3H": {quantidade_slots_m2:2,quantidade_portas_sata:4,quantidade_slots_m2_sata:2},
    "MSI|PRO B760M-P": {quantidade_slots_m2:2,quantidade_portas_sata:4,quantidade_slots_m2_sata:1,portas_sata_desativadas_por_m2_sata:1},
  };
  return catalogo.map(p => p.categoria === "placa_mae" ? {...p,...placas[p.fabricante + "|" + p.modelo]} : p);
}
