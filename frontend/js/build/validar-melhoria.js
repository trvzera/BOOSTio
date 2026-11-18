import { itensCategoria } from "./estado.js";
import { categorias } from "./catalogo.js";

const NUMERO = valor => valor == null || !["number","string"].includes(typeof valor) || String(valor).trim() === ""
  || !Number.isFinite(Number(valor)) || Number(valor) <= 0 ? null : Number(valor);
const bloquear = (codigo,motivo) => ({permitida:false,codigo,motivo});
const desconhecida = motivo => bloquear("dados-insuficientes",motivo);
const equivalente = () => bloquear("sem-ganho","As especificações comparadas são equivalentes às atuais. Não há melhoria comprovada para recomendar essa troca.");
const regrediu = criterio => bloquear("regressao","A troca reduziria " + criterio + ". Escolha uma peça equivalente ou superior nesse critério.");
const ddr = valor => /^DDR[1-9]$/.test(String(valor).replace(/[\s-]/g,"").toUpperCase())
  ? String(valor).replace(/[\s-]/g,"").toUpperCase() : null;
const cl = valor => {
  const resultado = /^(?:CL\s*)?(\d+(?:[.,]\d+)?)(?:-\d+)*$/i.exec(String(valor ?? "").trim());
  return resultado ? NUMERO(resultado[1].replace(",",".")) : null;
};


export function avaliarTrocaMelhoria(build,candidata,catalogo,{modo = "substituir"} = {}) {
  if (!build?.componentes || typeof candidata?.id !== "string" || !candidata.id.trim() || !Array.isArray(catalogo)
    || !categorias.some(categoria => categoria.id === candidata.categoria))
    return desconhecida("Identifique a build e as peças no catálogo antes de comparar a troca.");
  const categoria = candidata.categoria;
  const itens = itensCategoria(build,categoria);
  const expandirDiscos = ["ssd","hd"].includes(categoria) && modo === "adicionar";
  if (!["adicionar","substituir"].includes(modo)) return desconhecida("Escolha se deseja adicionar ou substituir a peça.");
  if (expandirDiscos && NUMERO(candidata.capacidade_gb) == null)
    return desconhecida("Falta a capacidade do novo disco para confirmar a expansão de armazenamento.");
  if (!itens.length) {

    if (categoria === "placa_video") {
      const cpu = itensCategoria(build,"processador")[0];
      const processador = catalogo.find(peca => peca.categoria === "processador" && peca.id === cpu?.id);
      if (cpu && processador?.videointegrado !== false)
        return desconhecida("Faltam benchmarks comparáveis entre a placa de vídeo e o vídeo do processador. Não é possível garantir uma melhoria.");
    }
    return {permitida:true,codigo:"adicao",motivo:"Adição em uma categoria sem peça atual; a compatibilidade ainda será validada."};
  }
  const atuais = itens.map(item => ({
    quantidade:NUMERO(item?.quantidade === undefined ? 1 : item.quantidade),
    peca:catalogo.find(peca => peca.categoria === categoria && peca.id === item?.id),
  }));
  if (atuais.some(({peca,quantidade}) => !peca || !Number.isInteger(quantidade) || quantidade > 64))
    return desconhecida("Identifique todos os modelos e quantidades atuais desta categoria para evitar uma troca inferior.");
  if (expandirDiscos)
    return {permitida:true,codigo:"expansao",motivo:"Acrescenta capacidade sem remover os discos atuais. Não implica ganho de velocidade; conexões e encaixes ainda serão verificados."};
  if (atuais.some(({peca}) => peca.id === candidata.id || peca.part_number && candidata.part_number
    && String(peca.part_number).trim().toUpperCase() === String(candidata.part_number).trim().toUpperCase()))
    return bloquear("mesma-peca","Este modelo já está na build. Ajuste sua quantidade no editor, sem substituir a categoria inteira.");

  function minimo(campo,rotulo,{somar = false} = {}) {
    const nova = NUMERO(candidata[campo]);
    const valores = atuais.map(({peca,quantidade}) => {
      const valor = NUMERO(peca[campo]);
      return valor == null ? null : valor * (somar ? quantidade : 1);
    });
    if (nova == null || valores.some(valor => valor == null || !Number.isFinite(valor)))
      return desconhecida("Faltam dados de " + rotulo + " para comparar as peças com segurança.");
    const antes = somar ? valores.reduce((total,valor) => total + valor,0) : Math.max(...valores);
    if (!Number.isFinite(antes)) return desconhecida("Os valores atuais de " + rotulo + " não são válidos para comparar.");
    if (nova > antes) ganhos.push({criterio:rotulo,antes,depois:nova});
    return nova < antes ? regrediu(rotulo + " (de " + antes + " para " + nova + ")") : null;
  }
  const ganhos = [];
  const aprovar = motivo => ganhos.length ? {permitida:true,codigo:"melhoria",motivo,ganhos} : equivalente();

  if (categoria === "memoria_ram") {
    const geracao = ddr(candidata.ddr), anteriores = atuais.map(({peca}) => ddr(peca.ddr));
    if (!geracao || anteriores.some(valor => !valor)) return desconhecida("Falta a geração DDR de alguma memória para comparar.");
    if (anteriores.some(valor => valor !== geracao))
      return desconhecida("Memórias de gerações DDR diferentes não serão tratadas como equivalentes nesta comparação.");
    const erro = minimo("capacidade_gb","a capacidade total de RAM em GB",{somar:true})
      || minimo("frequencia_mhz","a frequência informada da RAM em MHz")
      || minimo("quantidade_pentes","a quantidade total de pentes",{somar:true});
    if (erro) return erro;
    const novaCl = cl(candidata.latencia), novaFrequencia = NUMERO(candidata.frequencia_mhz);
    for (const {peca} of atuais) {
      const antesCl = cl(peca.latencia), antesFrequencia = NUMERO(peca.frequencia_mhz);
      if (novaCl == null || antesCl == null)
        return desconhecida("Falta a latência CAS identificada para descartar uma piora na RAM.");

      if (novaCl / novaFrequencia > antesCl / antesFrequencia + 1e-12)
        return regrediu("a resposta da RAM ao aumentar a latência CAS relativa à frequência");
    }
    if (atuais.every(({peca}) => novaCl / novaFrequencia < cl(peca.latencia) / NUMERO(peca.frequencia_mhz) - 1e-12))
      ganhos.push({criterio:"latência da RAM em ns",antes:Math.max(...atuais.map(({peca}) => 2000 * cl(peca.latencia) / NUMERO(peca.frequencia_mhz))),depois:2000 * novaCl / novaFrequencia});
    // Acrescentar pentes por si só não comprova uma melhora de desempenho.
    const ganhoReal = ganhos.filter(ganho => ganho.criterio !== "a quantidade total de pentes");
    ganhos.splice(0,ganhos.length,...ganhoReal);
    return aprovar("Mais capacidade, frequência ou menor latência, sem redução nos demais critérios comparados.");
  }
  if (categoria === "ssd" || categoria === "hd") {
    const erro = minimo("capacidade_gb","a capacidade total de armazenamento em GB",{somar:true})
      || (categoria === "ssd"
        ? minimo("velocidade_leitura_mbps","a velocidade de leitura informada em MB/s")
          || minimo("velocidade_gravacao_mbps","a velocidade de gravação informada em MB/s")
        : minimo("velocidade_rpm","a rotação informada do HD em RPM")
          || minimo("memoria_cache_mb","o cache informado do HD em MB"));
    if (erro) return erro;
    return aprovar("Ganho nas especificações de armazenamento comparadas, sem reduzir a capacidade total nem as demais métricas.");
  }
  if (categoria === "processador" || categoria === "placa_video") {
    const teste = categoria === "processador" ? "PassMark CPU Mark / Single Thread" : "PassMark G2D / G3D";
    const origem = peca => typeof peca.benchmark_fonte === "string" && peca.benchmark_fonte.trim();
    if (!origem(candidata) || candidata.benchmark_teste !== teste || atuais.some(({peca}) =>
      peca.benchmark_teste !== teste || !origem(peca) || origem(peca) !== origem(candidata)
      || (peca.benchmark_versao ?? null) !== (candidata.benchmark_versao ?? null)
      || (peca.benchmark_referencia_em ?? null) !== (candidata.benchmark_referencia_em ?? null)))
      return desconhecida("Faltam benchmarks comparáveis: mesmo teste, fonte, versão e data de referência. Preço, nome e especificações isoladas não comprovam desempenho.");
    const erro = categoria === "processador"
      ? minimo("benchmark_multi_core","pontuação de processamento com vários núcleos") || minimo("benchmark_single_thread","pontuação de processamento por núcleo")
      : minimo("benchmark_g3d","pontuação gráfica 3D") || minimo("memoria_gb","memória da placa de vídeo em GB");
    if (erro) return erro;
    // VRAM extra com a mesma pontuação não comprova ganho no processamento gráfico.
    if (categoria === "placa_video" && !ganhos.some(g => g.criterio === "pontuação gráfica 3D")) return equivalente();
    return {...aprovar("Pontuação superior no mesmo benchmark, sem reduzir as demais métricas comparadas. Não representa um ganho de FPS garantido."),teste,fonte:candidata.benchmark_fonte};
  }
  return desconhecida("Ainda faltam critérios comparáveis desta categoria para descartar uma piora. Esta troca não será sugerida como melhoria.");
}

export function exigirTrocaMelhoria(build,candidata,catalogo,opcoes) {
  const avaliacao = avaliarTrocaMelhoria(build,candidata,catalogo,opcoes);
  if (!avaliacao.permitida) throw new Error(avaliacao.motivo);
  return avaliacao;
}

export function resumoGanhoMelhoria(avaliacao) {
  if (!avaliacao?.permitida) return "";
  if (avaliacao.codigo === "expansao") return "Mais espaço, mantendo os discos atuais.";
  if (avaliacao.codigo === "adicao") return "Acrescenta uma peça à categoria vazia.";
  const numero = new Intl.NumberFormat("pt-BR",{maximumFractionDigits:2});
  return (avaliacao.ganhos || []).map(({criterio,antes,depois}) =>
    criterio + ": de " + numero.format(antes) + " para " + numero.format(depois)).join(" · ");
}
