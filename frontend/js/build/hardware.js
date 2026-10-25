import { informacoesFans, orientacoesVentilacao, encaixeRadiador } from "./fans.js";
import { completarMedidas } from "./medidas-fisicas.js";
import { avaliarBaias } from "./armazenamento.js";
export { conexaoDisco } from "./armazenamento.js";
export { informacoesFans } from "./fans.js";
// Campos ausentes são desconhecidos, nunca zero ou uma medida inferida pelo nome.
export function numeroConhecido(valor) {
  if (valor == null || valor === "" || typeof valor === "boolean") return null;
  const n = Number(valor);
  return Number.isFinite(n) && n >= 0 ? n : null;
}
export const AVISO_SLOTS_RAM_PROVISORIOS = "Slots de RAM não informados: limite provisório de dois pentes no editor. Confirme a quantidade real de slots e a capacidade máxima no manual da placa-mãe antes de comprar.";
export function slotsRam(placa) {
  if (!placa) return {slots:0,provisorio:false};
  const valor = placa.quantidade_slots_ram;
  const numero = ["number","string"].includes(typeof valor) && String(valor).trim() ? numeroConhecido(valor) : null;
  // Zero ou um slot explicitamente cadastrado não vira dois. Não altera a ficha.
  return numero != null && Number.isInteger(numero) ? {slots:numero,provisorio:false} : {slots:2,provisorio:true};
}
export function limitesArmazenamento(placa, m2Sata = 0) {
  const sata = numeroConhecido(placa?.quantidade_portas_sata);
  const compartilhadas = numeroConhecido(placa?.portas_sata_desativadas_por_m2_sata);
  return {
    m2:numeroConhecido(placa?.quantidade_slots_m2),
    m2Sata:numeroConhecido(placa?.quantidade_slots_m2_sata),
    // Com mapa por slot, este é o teto nominal. A distribuição completa é
    // revalidada antes de adicionar, sem descontar duas vezes uma porta compartilhada.
    sata:sata == null ? null : placa?.slots_m2 && placa.topologia_armazenamento_verificada === true ? sata : Math.max(0,sata - m2Sata * (compartilhadas ?? 0)),
    compartilhamentoDesconhecido:m2Sata > 0 && compartilhadas == null && placa?.topologia_armazenamento_verificada !== true,
  };
}
function medidas(valor) {
  if (valor == null) return null;
  return (Array.isArray(valor) ? valor : String(valor).split(/[,;/]/))
    .map(v => numeroConhecido(String(v).trim().replace(/\s*mm$/i,"")))
    .reduce((valores,v) => valores == null || v == null || v <= 0 ? null : [...valores,v],[]);
}
export function encaixeCoolerPlaca(cooler,placa) {
  const normalizar = v => String(v || "").trim().replace(/\s+/g," ").toUpperCase();
  if (!placa?.fabricante || !placa.modelo || !Array.isArray(cooler?.placas_mae_incompativeis)) return null;
  const fabricante = normalizar(placa.fabricante), modelo = normalizar(placa.modelo);
  const nome = modelo.startsWith(fabricante + " ") ? modelo : fabricante + " " + modelo;
  return cooler.placas_mae_incompativeis.some(p => normalizar(p) === nome) ? false : null;
}
export function validarEncaixe({gpu,air,water,fans = [],gabinete,placa,fonte,discos = [],substituir = false}) {
  const orientacoes = orientacoesVentilacao({gabinete,fans,water,substituir});
  const erros = [], avisos = [...orientacoes.dicas], alertas = [...orientacoes.avisos];
  for (const cooler of [air,water]) if (encaixeCoolerPlaca(cooler,placa) === false)
    erros.push("O fabricante do cooler declara incompatibilidade física com este modelo exato de placa-mãe.");
  if (!gabinete) return {erros,avisos,alertas};
  if (gabinete.observacoes_medidas) avisos.push(gabinete.observacoes_medidas);
  const checarMedida = (peca,medida,limite,nome) => {
    if (!peca) return;
    const tamanho = numeroConhecido(medida), maximo = numeroConhecido(limite);
    if (!tamanho || !maximo) avisos.push("Faltam medidas para confirmar o encaixe " + nome + " no gabinete.");
    else if (tamanho > maximo) erros.push("O tamanho " + nome + " (" + tamanho + " mm) ultrapassa o limite do gabinete (" + maximo + " mm).");
  };
  checarMedida(gpu,gpu?.comprimento_mm,gabinete.tamanho_max_gpu_mm,"da placa de vídeo");
  checarMedida(gpu,gpu?.altura_mm,gabinete.tamanho_max_altura_gpu_mm,"da altura da placa de vídeo");
  checarMedida(gpu,gpu?.espessura_mm,gabinete.tamanho_max_espessura_gpu_mm,"da espessura da placa de vídeo");
  checarMedida(air,air?.altura_mm,gabinete.tamanho_max_cooler_mm,"do air cooler");
  checarMedida(fonte,fonte?.comprimento_mm,gabinete.tamanho_max_fonte_mm,"da fonte");
  if (gpu) {
    const slots = numeroConhecido(gpu.slots_ocupados), limite = numeroConhecido(gabinete.slots_expansao);
    if (slots && limite && slots > limite) erros.push("A placa de vídeo ocupa mais slots do que o gabinete oferece.");
    avisos.push("Confirme as folgas da GPU com cabos, radiador e fans frontais; comprimento isolado não confirma o conjunto.");
  }
  if (fonte) {
    const normalizar = v => String(v).toUpperCase().replace(/[ -]/g,"");
    if (fonte.formato && Array.isArray(gabinete.formatos_fonte)) {
      if (!gabinete.formatos_fonte.map(normalizar).includes(normalizar(fonte.formato))) erros.push("O formato da fonte não é aceito pelo gabinete.");
    } else avisos.push("Faltam os formatos de fonte aceitos pelo gabinete.");
  }
  for(const r of avaliarBaias(gabinete,discos.map(({item,peca})=>[item,peca]))){
    if(r.condicao===false)erros.push(r.mensagem);else if(r.condicao===null)avisos.push(r.mensagem);
  }
  const radiadores = medidas(gabinete.radiadores_suportados_mm);
  const tamanhoRadiador = numeroConhecido(water?.tamanho_radiador_mm);
  if (water) {
    if (encaixeRadiador(gabinete,water) === false) erros.push("As dimensões reais do radiador ou a espessura radiador + fans excedem os limites por posição do gabinete.");
    if (gabinete.suporte_water_cooler === false) erros.push("O gabinete não suporta water cooler.");
    else if (tamanhoRadiador != null && radiadores != null && !radiadores.includes(tamanhoRadiador))
      erros.push("O gabinete não suporta radiador de " + tamanhoRadiador + " mm.");
    else if (tamanhoRadiador == null || radiadores == null)
      avisos.push("Confirme os tamanhos de radiador suportados pelo gabinete; suporte a water cooler não garante encaixe de 360 mm.");
    avisos.push("Confirme a espessura do conjunto radiador + fans e as folgas com RAM e GPU.");
  }
  const info = informacoesFans(gabinete,fans,water,substituir);
  if (fans.length || water) {
    if (info.tamanhos === false) erros.push("O gabinete não suporta o tamanho das fans selecionadas.");
    if (info.tamanhos == null) avisos.push("Falta o tamanho dos encaixes de fans do gabinete para confirmar a instalação.");
    if (info.quantidade == null)
      avisos.push("Falta a capacidade de fans do gabinete para conferir a quantidade total, incluindo as fans inclusas e as do radiador.");
    else if (!info.quantidade)
      erros.push("Há mais fans do que posições no gabinete, contando as inclusas e as do radiador. Remova um kit ou configure a substituição das fans do water cooler, se for essa a intenção.");
    if (info.substituicao === false) erros.push("Para substituir as fans do water cooler, selecione fans suficientes do mesmo tamanho das originais.");
    else if (info.substituicao == null) avisos.push("Faltam especificações para verificar as fans escolhidas para substituir as do water cooler.");
    if (info.distribuicao === false) erros.push("As fans e o radiador não cabem nas posições compartilhadas do gabinete, mantendo as fans inclusas.");
    else if (info.distribuicao == null) avisos.push("Confirme a distribuição das fans e do radiador: faltam medidas por posição ou tamanho das fans do radiador.");
  }
  return {erros,avisos,alertas};
}

// Slots/SATA: complemento somente demonstrativo. Medidas: manifesto compartilhado
// com Peca.to_catalogo(), sem alterar registros ou o esquema do banco.
// Documentação das revisões de referência: docs/frontend-build.md.
export function completarCatalogoDemo(catalogo,manifesto = {pecas:[]}) {
  const placas = {
    "ASUS|Prime A520M-K": {quantidade_slots_m2:1,quantidade_portas_sata:4,quantidade_slots_m2_sata:1},
    "Gigabyte|B550M DS3H": {quantidade_slots_m2:2,quantidade_portas_sata:4,quantidade_slots_m2_sata:2},
    "MSI|PRO B760M-P": {quantidade_slots_m2:2,quantidade_portas_sata:4,quantidade_slots_m2_sata:1,portas_sata_desativadas_por_m2_sata:1},
  };
  return catalogo.map(p => {
    const base = p.categoria === "placa_mae" ? {...p,...placas[p.fabricante + "|" + p.modelo]} : p;
    return completarMedidas(base,manifesto);
  });
}
