import { itensCategoria } from "./estado.js";
import { categorias } from "./catalogo.js";

const NUMERO = valor => valor == null || !["number","string"].includes(typeof valor) || String(valor).trim() === ""
  || !Number.isFinite(Number(valor)) || Number(valor) <= 0 ? null : Number(valor);
const bloquear = (codigo,motivo) => ({permitida:false,codigo,motivo});
const desconhecida = motivo => bloquear("dados-insuficientes",motivo);
const regrediu = criterio => bloquear("regressao","A troca reduziria " + criterio + ". Escolha uma peça equivalente ou superior nesse critério.");
const ddr = valor => /^DDR[1-9]$/.test(String(valor).replace(/[\s-]/g,"").toUpperCase())
  ? String(valor).replace(/[\s-]/g,"").toUpperCase() : null;
const cl = valor => {
  const resultado = /^(?:CL\s*)?(\d+(?:[.,]\d+)?)(?:-\d+)*$/i.exec(String(valor ?? "").trim());
  return resultado ? NUMERO(resultado[1].replace(",",".")) : null;
};

// Política conservadora: ausência de dados não prova que a troca não é pior.
// Não classifica CPU/GPU por nome, preço, GHz, núcleos ou quantidade de VRAM.
// O modal substitui a categoria inteira por UMA unidade/kit, não cada item isolado.
export function avaliarTrocaMelhoria(build,candidata,catalogo) {
  if (!build?.componentes || typeof candidata?.id !== "string" || !candidata.id.trim() || !Array.isArray(catalogo)
    || !categorias.some(categoria => categoria.id === candidata.categoria))
    return desconhecida("Identifique a build e as peças no catálogo antes de comparar a troca.");
  const categoria = candidata.categoria;
  const itens = itensCategoria(build,categoria);
  if (!itens.length) {
    // Uma GPU dedicada antiga não é necessariamente melhor que o vídeo integrado.
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
    return nova < antes ? regrediu(rotulo + " (de " + antes + " para " + nova + ")") : null;
  }

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
      // Com a mesma geração DDR, CL/frequência compara a latência, não o CL isolado.
      if (novaCl / novaFrequencia > antesCl / antesFrequencia + 1e-12)
        return regrediu("a resposta da RAM ao aumentar a latência CAS relativa à frequência");
    }
    return {permitida:true,codigo:"sem-regressao",motivo:"Sem redução de capacidade, frequência ou pentes e sem aumento da latência CAS calculada."};
  }
  if (categoria === "ssd" || categoria === "hd") {
    const erro = minimo("capacidade_gb","a capacidade total de armazenamento em GB",{somar:true})
      || (categoria === "ssd"
        ? minimo("velocidade_leitura_mbps","a velocidade de leitura informada em MB/s")
          || minimo("velocidade_gravacao_mbps","a velocidade de gravação informada em MB/s")
        : minimo("velocidade_rpm","a rotação informada do HD em RPM")
          || minimo("memoria_cache_mb","o cache informado do HD em MB"));
    if (erro) return erro;
    return {permitida:true,codigo:"sem-regressao",motivo:"Sem redução da capacidade total nem das velocidades/especificações de armazenamento comparadas."};
  }
  if (categoria === "processador" || categoria === "placa_video")
    return desconhecida("O catálogo ainda não tem benchmarks comparáveis de CPU/GPU para garantir que esta troca não é inferior. Preço e especificações isoladas não comprovam desempenho.");
  return desconhecida("Ainda faltam critérios comparáveis desta categoria para descartar uma piora. Esta troca não será sugerida como melhoria.");
}

export function exigirTrocaMelhoria(build,candidata,catalogo) {
  const avaliacao = avaliarTrocaMelhoria(build,candidata,catalogo);
  if (!avaliacao.permitida) throw new Error(avaliacao.motivo);
  return avaliacao;
}
