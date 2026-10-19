import { fetchComErro } from "../_shared/fetchComErro.js";

const SLUG = /^[a-z0-9-]{1,190}$/;
export function criarClienteBenchmark({requisitar = fetchComErro,timeoutMs = 25000} = {}) {
  async function enviar(rota,parametros,{signal} = {}) {
    const controle = new AbortController();
    const cancelar = () => controle.abort();
    if (signal?.aborted) cancelar();
    signal?.addEventListener("abort",cancelar,{once:true});
    const prazo = setTimeout(cancelar,timeoutMs);
    try {
      const dados = await requisitar("/benchmark/" + rota + "?" + new URLSearchParams(parametros),{signal:controle.signal});
      if (!dados?.resultado || typeof dados.resultado !== "object") throw new Error("Resposta de desempenho inválida.");
      return dados.resultado;
    } catch (erro) {
      if (controle.signal.aborted) throw Object.assign(new Error(signal?.aborted ? "Consulta cancelada." : "A consulta demorou demais. Tente novamente."),{codigo:signal?.aborted ? "cancelado" : "timeout"});
      if (erro instanceof TypeError) throw new Error("Não foi possível acessar o servidor da BOOSTio. Confira a conexão e tente novamente.");
      throw erro;
    } finally {
      clearTimeout(prazo); signal?.removeEventListener("abort",cancelar);
    }
  }
  return {
    consultar({game,cpu,gpu,res = "1080p",preset = "high"},opcoes) {
      if (![game,cpu,gpu].every(v => typeof v === "string" && SLUG.test(v)) || !["1080p","1440p","4k"].includes(res) || !["low","medium","high","ultra"].includes(preset))
        return Promise.reject(new Error("Selecione um jogo e modelos de CPU e GPU reconhecidos, com ajustes válidos."));
      return enviar("fps",{game,cpu,gpu,res,preset},opcoes);
    },
    async buscarJogos(texto,opcoes) {
      const q = String(texto || "").trim();
      if (q.length < 2 || q.length > 60) throw new Error("Digite entre 2 e 60 caracteres para buscar um jogo.");
      const dados = await enviar("jogos",{q},opcoes);
      if (!Array.isArray(dados.jogos)) throw new Error("A busca retornou uma resposta inválida.");
      return dados.jogos;
    },
  };
}
