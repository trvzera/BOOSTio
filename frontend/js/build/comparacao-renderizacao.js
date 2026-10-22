import { itensCategoria } from "./estado.js";
import { hardwareBlender } from "../benchmark/hardware.js";
import { criarClienteBenchmark } from "../api/benchmark/consultarBenchmark.js";

export async function consultarRenderizacoes(builds,catalogo,{tipo = "cpu",signal,cache = new Map(),cliente = criarClienteBenchmark()} = {}) {
  if (!["cpu","gpu"].includes(tipo)) throw new Error("Selecione CPU ou GPU para comparar a renderização.");
  const consultas = new Map();
  return Promise.all(builds.map(async build => {
    const peca = categoria => catalogo.find(p => p.id === itensCategoria(build,categoria)[0]?.id);
    const dispositivo = hardwareBlender(peca("processador"),peca("placa_video"))[tipo];
    if (!dispositivo) return {id:build.id,erro:"Modelo não identificado para este teste. Não será usado outro componente."};
    const chave = tipo + ":" + dispositivo;
    try {
      if (!consultas.has(chave)) consultas.set(chave,cache.has(chave) ? Promise.resolve(cache.get(chave))
        : cliente.consultarBlender({dispositivo,tipo},{signal}).then(dados => { if (!signal?.aborted) cache.set(chave,dados); return dados; }));
      const dados = await consultas.get(chave);
      return {id:build.id,dispositivo,dados};
    } catch (erro) { return {id:build.id,dispositivo,erro:erro.message || "Resultado indisponível. Tente novamente."}; }
  }));
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
