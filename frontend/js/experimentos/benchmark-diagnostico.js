// Apenas laboratório. A montagem e os cards continuam usando a API Python.
import { criarClienteFPSHQ } from "./fpshq.js";
import { criarClienteBenchmark } from "../api/benchmark/consultarBenchmark.js";
import { fetchComErro } from "../api/_shared/fetchComErro.js";
import { API_URL } from "../config.js";

export function criarDiagnosticoBenchmark({modo = () => "backend",fetcher = (...args) => fetch(...args),requisitar = fetchComErro,
  aoRegistro = () => {},aoOcupar = () => {},relogio = () => performance.now(),timeoutMs = 20000} = {}) {
  async function executar(metodo,entrada,opcoes) {
    const via = modo();
    if (!["backend","direto"].includes(via)) throw new Error("Caminho de diagnóstico inválido.");
    const inicio = relogio();
    const registro = {via,operacao:metodo === "consultar" ? "fps" : "jogos",http:null,url:null,cache:null,redirecionado:false};
    aoOcupar(true);
    // Cliente novo e sem sessionStorage: uma resposta antiga não mascara o teste direto.
    const cliente = via === "direto" ? criarClienteFPSHQ({timeoutMs,fetcher:async (url,config) => {
      registro.url = url;
      const resposta = await fetcher(url,{...config,cache:"no-store"});
      registro.http = resposta.status;
      registro.redirecionado = resposta.redirected;
      return resposta;
    }}) : criarClienteBenchmark({timeoutMs:25000,requisitar:async (caminho,config) => {
      registro.url = API_URL + caminho;
      try {
        const dados = await requisitar(caminho,config);
        registro.http = 200;
        return dados;
      } catch (erro) { registro.http = erro.status ?? null; throw erro; }
    }});
    try {
      const dados = await cliente[metodo](entrada,opcoes);
      registro.cache = typeof dados.cache === "boolean" ? dados.cache : null;
      registro.ok = true;
      registro.codigo = "ok";
      return dados;
    } catch (erro) {
      registro.ok = false;
      registro.codigo = erro.codigo || (registro.http === 200 ? "resposta" : "rede-ou-cors");
      registro.mensagem = erro.message;
      throw erro;
    } finally {
      registro.tempoMs = Math.max(0,Math.round(relogio() - inicio));
      aoRegistro({...registro});
      aoOcupar(false);
    }
  }
  return {consultar:(entrada,opcoes) => executar("consultar",entrada,opcoes),buscarJogos:(texto,opcoes) => executar("buscarJogos",texto,opcoes)};
}

export function textoDiagnostico(registro) {
  const caminho = registro.via === "direto" ? "JavaScript → FPSHQ" : "JavaScript → BOOSTio (Python) → FPSHQ";
  const http = registro.http == null ? "Nenhuma resposta HTTP recebida pelo navegador" : "HTTP " + registro.http + (registro.via === "direto" ? " da FPSHQ" : " da BOOSTio (não é o status HTTP do provedor)");
  const cache = registro.cache == null ? "Cache não confirmado" : registro.cache ? "Resposta reutilizada do cache; não comprova disponibilidade atual" : "Sem reutilização de cache da aplicação";
  return [caminho,http,(registro.tempoMs / 1000).toFixed(2) + " s · " + registro.codigo,cache,
    registro.url || "Nenhuma chamada enviada",registro.mensagem || "Resposta aceita pelo cliente",
    registro.codigo === "rede" || registro.codigo === "rede-ou-cors" ? "Falha de rede ou CORS: confira a aba Network do navegador; o JavaScript não distingue todas essas causas." : "",
    registro.redirecionado ? "O navegador seguiu um redirecionamento. O cliente Python não segue redirecionamentos." : ""].filter(Boolean).join("\n");
}
