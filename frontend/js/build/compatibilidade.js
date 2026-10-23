import { categorias, perifericos, acessoriosRede } from "./catalogo.js";
import { itensSelecionados, itensCategoria, informacoesRam, informacoesArmazenamento, conflitosArmazenamento, selecionarPeca } from "./estado.js";
import { validarEncaixe, conexaoDisco } from "./hardware.js";

export function avaliarBuild(build,catalogo) {
  const get = cat => catalogo.find(p => p.id === itensCategoria(build,cat)[0]?.id && p.categoria === cat);
  const tem = cat => itensCategoria(build,cat).length > 0;
  const erros = [], avisos = [], dicas = [], infoRam = informacoesRam(build,catalogo);
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
    if (![...perifericos,...acessoriosRede,"fonte"].includes(categoria)) watts += Number(peca.consumo_energia || 0) * item.quantidade;
  }
  const fansInclusas = Number.isInteger(gabinete?.fans_inclusos) && gabinete.fans_inclusos > 0;
  const faltam = categorias.filter(c => c.obrigatoria && !tem(c.id) && !(c.id === "fan" && fansInclusas)).map(c => c.nome);
  if (!tem("ssd") && !tem("hd")) faltam.push("Armazenamento");
  if (cpu && !cpu.videointegrado && !tem("placa_video")) faltam.push("Placa de vídeo");
  if (cpu && !cpu.cooler && !tem("air_cooler") && !tem("water_cooler")) faltam.push("Cooler para o processador");
  if (cpu && placa && String(cpu.soquete).toUpperCase() !== String(placa.socket).toUpperCase())
    erros.push("O socket do processador (" + cpu.soquete + ") difere da placa-mãe (" + placa.socket + ").");
  for (const {peca:ram} of rams) {
    if (placa && ram.ddr !== placa.tipo_memoria)
      erros.push("A RAM " + ram.ddr + " não corresponde ao padrão " + placa.tipo_memoria + " da placa-mãe.");
    if (rams[0] && (ram.ddr !== rams[0].peca.ddr || Number(ram.frequencia_mhz) !== Number(rams[0].peca.frequencia_mhz)))
      erros.push("As memórias precisam ter o mesmo padrão DDR e a mesma frequência.");
  }
  if (placa && infoRam.usados > infoRam.slots) erros.push("Há mais pentes de RAM do que slots disponíveis.");
  if (placa?.memoria_maxima_gb && infoRam.capacidade > Number(placa.memoria_maxima_gb))
    erros.push("A capacidade de RAM supera o máximo informado da placa-mãe.");
  if (new Set(rams.map(r => r.peca.id)).size > 1)
    avisos.push("Misturar marcas ou modelos de RAM pode afetar estabilidade, timings e XMP/EXPO, mesmo com DDR e frequência iguais. Prefira kits testados juntos.");
  const potencia = Number(fonte?.potencia_w ?? fonte?.potencia);
  if (fonte && watts > potencia) erros.push("O consumo estimado supera a potência da fonte.");
  else if (fonte && watts > 0 && watts === potencia)
    avisos.push("A potência da fonte é igual ao consumo estimado, sem margem para picos de energia.");
  if (cpu && !cpu.videointegrado && !tem("placa_video")) avisos.push("Este processador precisa de uma placa de vídeo para exibir imagem.");
  if (get("adaptador_wifi")) dicas.push("Confira a interface USB/PCIe do adaptador, as conexões livres e a compatibilidade com o roteador.");
  if (get("cabo_rede")) dicas.push("Confira o comprimento e a categoria do cabo, a velocidade da porta Ethernet e do roteador.");
  for (const tipo of ["air_cooler","water_cooler"]) {
    const cooler = get(tipo);
    if (cooler && cpu && cooler.compatibilidade) {
      const sockets = String(cooler.compatibilidade).toUpperCase().split(/[,;/\s]+/);
      if (sockets.includes("INTEL") || sockets.includes("AMD"))
        dicas.push("Confirme no fabricante o suporte do cooler ao socket " + cpu.soquete + ".");
      else if (!sockets.includes(String(cpu.soquete).toUpperCase()))
        erros.push("O cooler não lista o socket do processador.");
    }
  }
  if (tem("air_cooler") && tem("water_cooler")) erros.push("Escolha apenas um cooler para o processador.");
  const formatoNormalizado = valor => String(valor || "").toUpperCase().replace(/\s/g,"").replace(/^(MICRO-?ATX|M-ATX)$/, "MATX").replace(/^MINI-?ITX$/, "ITX");
  const formatos = String(gabinete?.formatos_placa_mae || "").split(/[,;/]+/).map(formatoNormalizado);
  if (placa?.formato && gabinete?.formatos_placa_mae && !formatos.includes(formatoNormalizado(placa.formato)))
    erros.push("O gabinete não lista o formato da placa-mãe.");
  const discos = informacoesArmazenamento(build,catalogo);
  erros.push(...conflitosArmazenamento(discos));
  if (discos.itens.length) {
    if (!placa) dicas.push("Selecione a placa-mãe para conferir as conexões de armazenamento.");
    if (discos.itens.some(({peca}) => !conexaoDisco(peca))) dicas.push("Há discos sem conexão identificada; confirme a interface antes de duplicar.");
    if (placa && ((discos.m2 && discos.limites.m2 == null) || (discos.sata && discos.limites.sata == null)))
      dicas.push("Faltam as quantidades de slots M.2 ou portas SATA da placa-mãe para confirmar o armazenamento.");
    if (placa && discos.m2Sata && discos.limites.m2Sata == null) dicas.push("Confirme quais slots M.2 da placa-mãe aceitam SSD SATA.");
    if (placa && discos.limites.compartilhamentoDesconhecido) dicas.push("Confirme se o SSD M.2 SATA desativa alguma porta SATA da placa-mãe.");
  }
  const encaixe = validarEncaixe({gpu:get("placa_video"),air:get("air_cooler"),water:get("water_cooler") || (tem("water_cooler") ? {} : null),gabinete,placa,fonte:get("fonte"),
    substituir:build.substituirFansWaterCooler === true,
    discos:itensSelecionados(build,catalogo).filter(p => ["ssd","hd"].includes(p.categoria)),
    fans:itensSelecionados(build,catalogo).filter(p => p.categoria === "fan")});
  erros.push(...encaixe.erros); dicas.push(...encaixe.avisos); avisos.push(...encaixe.alertas);
  const grupos = ["processador","placa_mae","memoria_ram","armazenamento","placa_video","fonte","gabinete","fan","refrigeracao"];
  const preenchidos = grupos.filter(cat => cat === "armazenamento" ? tem("ssd") || tem("hd")
    : cat === "refrigeracao" ? tem("air_cooler") || tem("water_cooler") || cpu?.cooler
    : cat === "placa_video" ? tem(cat) || cpu?.videointegrado
    : cat === "fan" ? tem(cat) || fansInclusas
    : tem(cat)).length;
  const compatibilidade = build.compatibilidade || {status:"nao_verificado",rotulo:"Dados ainda não totalmente verificados",naoVerificado:[],aviso:"As verificações locais não confirmam medidas ou especificações ausentes. Uma build preenchida não é garantia de compatibilidade."};
  for (const erro of build.compatibilidade?.erros || []) if (typeof erro.mensagem === "string") erros.push(erro.mensagem);
  return {erros:[...new Set(erros)],avisos:[...new Set(avisos)],dicas:[...new Set(dicas)],faltam,preco,watts:Math.round(watts),compatibilidade,
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
