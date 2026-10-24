import { fetchComErro } from "../_shared/fetchComErro.js";
import { erroConexao } from "../_shared/erros-conexao.js";

const SLUG = /^[a-z0-9-]{1,190}$/;
const BUILD_ID = /^(?:s-)?[1-9][0-9]{0,17}$/;
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
      if (erro instanceof TypeError) throw erroConexao(erro);
      throw erro;
    } finally {
      clearTimeout(prazo); signal?.removeEventListener("abort",cancelar);
    }
  }
  return {
    consultarRequisitosBuild({game,buildId,publica = false},opcoes) {
      if (typeof game !== "string" || !SLUG.test(game) || typeof buildId !== "string" || !BUILD_ID.test(buildId))
        return Promise.reject(new Error("Selecione um jogo e uma build salva na sua conta."));
      return enviar("requisitos-build",{game,build_id:buildId,...(publica ? {origem_publica:'1'} : {})},opcoes).then(dados => {
        const estados = ["nao_informada","abaixo_minimo","abaixo_recomendado","recomendado","minimo_sem_recomendacao"];
        if (dados.game !== game || dados.buildId !== buildId || dados.escopo !== "parcial" || dados.requisitosVerificados !== false || dados.fpsValidado !== false
          || dados.ram?.fonte !== (publica ? "build_publica" : "build_salva") || typeof dados.ram.completa !== "boolean" || !estados.includes(dados.ram.status)
          || !Number.isInteger(dados.ram.conhecidaGb) || dados.ram.conhecidaGb < 0 || !Array.isArray(dados.ram.pendencias)
          || !Number.isInteger(dados.minimos?.ramGb) || dados.minimos.ramGb <= 0 || !dados.fonte
          || (dados.ram.completa ? !Number.isInteger(dados.ram.informadaGb) || dados.ram.informadaGb <= 0 || dados.ram.informadaGb !== dados.ram.conhecidaGb || dados.ram.status === "nao_informada" : dados.ram.informadaGb !== null || dados.ram.status !== "nao_informada"))
          throw new Error("Não foi possível confirmar os requisitos da build salva.");
        const minimo = dados.ram.informadaGb == null ? null : dados.ram.informadaGb >= dados.minimos.ramGb;
        if (dados.ram.atendeMinimo !== minimo || (minimo === false && dados.ram.status !== "abaixo_minimo"))
          throw new Error("A resposta de requisitos contém informações inconsistentes de RAM.");
        if (dados.vram || dados.armazenamento || dados.impedimentosMinimos) {
          const v = dados.vram, a = dados.armazenamento;
          const capacidade = n => n === null || Number.isInteger(n) && n > 0;
          const conclusaoVram = v?.dedicadaGb != null && v?.minimaGb != null ? v.dedicadaGb >= v.minimaGb : null;
          const conclusaoDisco = a?.minimaGb == null ? null : a?.maiorUnidadeElegivelGb >= a.minimaGb ? true : a?.completo === true ? false : null;
          if (!v || !a || v.minimaGb !== (dados.minimos.vramGb ?? null) || a.minimaGb !== (dados.minimos.armazenamentoGb ?? null)
            || a.exigeSsd !== (dados.minimos.exigeSsd === true) || !capacidade(v.dedicadaGb) || !capacidade(v.minimaGb)
            || !capacidade(a.maiorUnidadeElegivelGb) || !capacidade(a.minimaGb) || typeof a.completo !== 'boolean'
            || typeof a.exigeSsd !== 'boolean' || a.espacoLivreVerificado !== false
            || v.atendeCapacidadeMinima !== conclusaoVram || a.atendeCapacidadeMinima !== conclusaoDisco
            || !Array.isArray(dados.impedimentosMinimos) || dados.impedimentosMinimos.some(m => typeof m !== 'string' || !m.trim())
            || Boolean(dados.impedimentosMinimos.length) !== (minimo === false || conclusaoVram === false || conclusaoDisco === false))
            throw new Error("Não foi possível confirmar as capacidades de vídeo e armazenamento da build.");
        }
        return dados;
      });
    },
    consultarRequisitos({game,ramGb = null},opcoes) {
      if (typeof game !== "string" || !SLUG.test(game) || ramGb != null && (!Number.isInteger(ramGb) || ramGb < 1 || ramGb > 4096))
        return Promise.reject(new Error("Selecione um jogo e informe a RAM em GB inteiros, ou deixe o campo vazio."));
      return enviar("requisitos",{game,...(ramGb == null ? {} : {ram_gb:ramGb})},opcoes).then(dados => {
        if (dados.game !== game || dados.escopo !== "parcial" || dados.requisitosVerificados !== false || dados.fpsValidado !== false
          || !dados.ram || !dados.minimos || !dados.fonte || !Number.isInteger(dados.minimos.ramGb))
          throw new Error("Resposta de requisitos inválida. A build não foi aprovada.");
        return dados;
      });
    },
    consultarBlender({dispositivo,tipo},opcoes) {
      if (typeof dispositivo !== "string" || !/^[A-Za-z0-9() +._/\-]{2,160}$/.test(dispositivo) || !["cpu","gpu"].includes(tipo))
        return Promise.reject(new Error("Selecione uma CPU ou GPU identificada para o Blender."));
      return enviar("blender",{dispositivo,tipo},opcoes).then(dados => {
        const identidade = nome => String(nome).replace(/^\d{2}(st|nd|rd|th) Gen\s+/i,"").replace(/\((R|TM)\)/gi,"").toLowerCase();
        if (identidade(dados.dispositivo) !== identidade(dispositivo) || dados.tipo !== tipo || !Number.isFinite(dados.score) || dados.score < 0 || !Number.isInteger(dados.quantidade) || dados.quantidade < 1 || !/^\d+\.\d+\.\d+$/.test(dados.versao || "") || !["CPU","CUDA","OPTIX","HIP","METAL","ONEAPI"].includes(dados.metodo) || !Number.isFinite(dados.consultadoEm) || !String(dados.url).startsWith("https://opendata.blender.org/benchmarks/query/?"))
          throw new Error("Resposta do Blender inválida. Nenhuma pontuação foi estimada.");
        return dados;
      });
    },
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
