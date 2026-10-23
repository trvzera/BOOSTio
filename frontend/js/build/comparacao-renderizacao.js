import { itensCategoria } from "./estado.js";
import { hardwareBlender } from "../benchmark/hardware.js";
import { criarClienteBenchmark } from "../api/benchmark/consultarBenchmark.js";

export async function consultarRenderizacoes(builds,catalogo,{tipo = "cpu",signal,cache = new Map(),cliente = criarClienteBenchmark()} = {}) {
  if (!["cpu","gpu"].includes(tipo)) throw new Error("Selecione CPU ou GPU para comparar a renderização.");
  const consultas = new Map();
  return Promise.all(builds.map(async build => {
    const peca = categoria => catalogo.find(p => p.id === itensCategoria(build,categoria)[0]?.id);
    const dispositivo = hardwareBlender(peca("processador"),peca("placa_video"))[tipo];
    if (!dispositivo) return {id:build.id,codigo:"modelo-nao-identificado",erro:tipo === "gpu" && !peca("placa_video")
      ? "Esta build não tem uma GPU dedicada identificada. Vídeo integrado não será substituído por outra placa para este teste."
      : "Modelo de " + tipo.toUpperCase() + " não identificado para o Blender. Não será usado outro componente."};
    const chave = tipo + ":" + dispositivo;
    try {
      if (!consultas.has(chave)) consultas.set(chave,cache.has(chave) ? Promise.resolve(cache.get(chave))
        : cliente.consultarBlender({dispositivo,tipo},{signal}).then(dados => { if (!signal?.aborted) cache.set(chave,dados); return dados; }));
      const dados = await consultas.get(chave);
      return {id:build.id,dispositivo,dados};
    } catch (erro) { return {id:build.id,dispositivo,erro:erro.message || "Resultado indisponível. Tente novamente.",
      codigo:erro.codigo,status:erro.status,espera:Number.isFinite(erro.espera) && erro.espera > 0 ? Math.min(erro.espera,3600) : 0}; }
  }));
}

export function resumirConsultaRenderizacoes(resultados) {
  const sucesso = resultados.filter(r => r.dados && Number.isFinite(r.dados.score)).length;
  const espera = Math.max(0,...resultados.map(r => Number.isFinite(r.espera) ? r.espera : 0));
  if (!sucesso) return {tom:"error",espera,mensagem:"Não foi possível comparar a renderização. "
    + [...new Set(resultados.map(r => r.erro || "Sem resultado disponível."))].join(" ")};
  if (sucesso !== resultados.length) return {tom:"warning",espera,mensagem:"Resultados disponíveis para " + sucesso + " de " + resultados.length
    + " builds. Confira o motivo em cada card; não há vencedora enquanto faltarem resultados."};
  const classificacao = classificarRenderizacoes(resultados);
  return {tom:classificacao.comparavel ? "info" : "warning",espera,mensagem:classificacao.comparavel
    ? "Mais amostras/min é melhor neste teste. CPU e GPU são separadas; RAM, VRAM, drivers e a cena podem mudar o desempenho real. A fonte pode agrupar variantes de fabricante e memória."
    : classificacao.motivo + " As pontuações continuam visíveis, sem indicar uma vencedora."};
}

export function classificarRenderizacoes(resultados) {
  const validos = resultados.filter(item => item.dados && Number.isFinite(item.dados.score) && item.dados.score >= 0
    && ["cpu","gpu"].includes(item.dados.tipo) && /^\d+\.\d+\.\d+$/.test(item.dados.versao || "")
    && ["CPU","CUDA","OPTIX","HIP","METAL","ONEAPI"].includes(item.dados.metodo)
    && (item.dados.tipo === "cpu") === (item.dados.metodo === "CPU"));
  if (resultados.length < 2 || validos.length !== resultados.length)
    return {comparavel:false,melhores:[],motivo:"É necessário ter dados de todas as builds para destacar o desempenho."};
  const criterios = new Set(validos.map(({dados}) => [dados.tipo,dados.versao,dados.metodo].join(":")));
  if (criterios.size !== 1) return {comparavel:false,melhores:[],motivo:"Versões ou métodos diferentes: os resultados não podem ser classificados juntos."};
  const maior = Math.max(...validos.map(({dados}) => dados.score));
  return {comparavel:true,melhores:validos.filter(({dados}) => dados.score === maior).map(item => item.id),score:maior};
}
