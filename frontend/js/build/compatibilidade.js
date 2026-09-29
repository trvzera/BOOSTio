import { categorias, perifericos } from "./catalogo.js";
import { itensSelecionados, informacoesRam, selecionarPeca } from "./estado.js";

export function avaliarBuild(build,catalogo) {
  const get = cat => catalogo.find(p => p.id === build.componentes[cat]?.id && p.categoria === cat);
  const erros = [], avisos = [], infoRam = informacoesRam(build,catalogo);
  const cpu = get("processador"), placa = get("placa_mae"), fonte = get("fonte"), gabinete = get("gabinete");
  const rams = infoRam.itens.filter(r => r.peca);
  let preco = 0, watts = 0;
  for (const {categoria,item,peca} of itensSelecionados(build,catalogo)) {
    if (!peca) {
      avisos.push(item.proprio ? "A peça própria de " + categorias.find(c => c.id === categoria).nome +
        " precisa ser identificada no catálogo." : "Uma peça não foi encontrada no catálogo.");
      continue;
    }
    preco += Number(peca.preco || 0) * item.quantidade;
    if (![...perifericos,"fonte"].includes(categoria)) watts += Number(peca.consumo_energia || 0) * item.quantidade;
  }
  const faltam = categorias.filter(c => c.obrigatoria && (c.id === "memoria_ram" ? !rams.length : !get(c.id))).map(c => c.nome);
  if (!get("ssd") && !get("hd")) faltam.push("Armazenamento");
  if (cpu && !cpu.videointegrado && !get("placa_video")) faltam.push("Placa de vídeo");
  if (cpu && !cpu.cooler && !get("air_cooler") && !get("water_cooler")) faltam.push("Cooler para o processador");
  if (cpu && placa && String(cpu.soquete).toUpperCase() !== String(placa.socket).toUpperCase())
    erros.push("O socket do processador (" + cpu.soquete + ") difere da placa-mãe (" + placa.socket + ").");
  for (const {peca:ram} of rams) {
    if (placa && ram.ddr !== placa.tipo_memoria)
      erros.push("A RAM " + ram.ddr + " não corresponde ao padrão " + placa.tipo_memoria + " da placa-mãe.");
    if (rams[0] && (ram.ddr !== rams[0].peca.ddr || Number(ram.frequencia_mhz) !== Number(rams[0].peca.frequencia_mhz)))
      erros.push("As memórias precisam ter o mesmo padrão DDR e a mesma frequência.");
  }
  if (placa && infoRam.usados > infoRam.slots) erros.push("Há mais módulos de RAM do que slots disponíveis.");
  if (placa?.memoria_maxima_gb && infoRam.capacidade > Number(placa.memoria_maxima_gb))
    erros.push("A capacidade de RAM supera o máximo informado da placa-mãe.");
  if (new Set(rams.map(r => r.peca.id)).size > 1)
    avisos.push("Misturar marcas ou modelos de RAM pode afetar estabilidade, timings e XMP/EXPO, mesmo com DDR e frequência iguais. Prefira kits testados juntos.");
  const potencia = Number(fonte?.potencia_w ?? fonte?.potencia);
  if (fonte && watts > potencia) erros.push("O consumo estimado supera a potência da fonte.");
  else if (fonte && watts > 0 && watts === potencia)
    avisos.push("A potência da fonte é igual ao consumo estimado, sem margem para picos de energia.");
  if (cpu && !cpu.videointegrado && !get("placa_video")) avisos.push("Este processador precisa de uma placa de vídeo para exibir imagem.");
  for (const tipo of ["air_cooler","water_cooler"]) {
    const cooler = get(tipo);
    if (cooler && cpu && cooler.compatibilidade) {
      const sockets = String(cooler.compatibilidade).toUpperCase().split(/[,;/\s]+/);
      if (sockets.includes("INTEL") || sockets.includes("AMD"))
        avisos.push("Confirme no fabricante o suporte do cooler ao socket " + cpu.soquete + ".");
      else if (!sockets.includes(String(cpu.soquete).toUpperCase()))
        erros.push("O cooler não lista o socket do processador.");
    }
  }
  if (get("air_cooler") && get("water_cooler")) erros.push("Escolha apenas um cooler para o processador.");
  const formatos = String(gabinete?.formatos_placa_mae || "").toUpperCase().split(/[,;/]+/).map(v => v.trim());
  if (placa && gabinete?.formatos_placa_mae && !formatos.includes(String(placa.formato).toUpperCase()))
    erros.push("O gabinete não lista o formato da placa-mãe.");
  const cooler = get("air_cooler");
  if (cooler && gabinete?.tamanho_max_cooler_mm && Number(cooler.dimensoes) > Number(gabinete.tamanho_max_cooler_mm))
    erros.push("O air cooler ultrapassa a altura suportada pelo gabinete.");
  if (get("water_cooler") && gabinete && !gabinete.suporte_water_cooler)
    erros.push("O gabinete não informa suporte a water cooler.");
  if (get("ssd")?.formato === "M.2" && placa && !Number(placa.quantidade_slots_m2))
    erros.push("A placa-mãe não informa um slot M.2 para este SSD.");
  const grupos = ["processador","placa_mae","memoria_ram","armazenamento","placa_video","fonte","gabinete","fan","refrigeracao"];
  const preenchidos = grupos.filter(cat => cat === "armazenamento" ? get("ssd") || get("hd")
    : cat === "refrigeracao" ? get("air_cooler") || get("water_cooler") || cpu?.cooler
    : cat === "placa_video" ? get(cat) || cpu?.videointegrado
    : cat === "memoria_ram" ? rams.length : get(cat)).length;
  return {erros:[...new Set(erros)],avisos:[...new Set(avisos)],faltam,preco,watts:Math.round(watts),
    preenchidos,total:grupos.length,status:erros.length ? "erro" : faltam.length ? "incompleta" : avisos.length ? "atencao" : "completa"};
}
export function selecionarPecaCompativel(build,peca,catalogo) {
  const proxima = selecionarPeca(build,peca,catalogo);
  const conflitos = avaliarBuild(proxima,catalogo).erros;
  if (conflitos.length) throw new Error(conflitos.join(" "));
  return proxima;
}
export function pecaCompativel(build,peca,catalogo) {
  try { selecionarPecaCompativel(build,peca,catalogo); return true; } catch { return false; }
}
