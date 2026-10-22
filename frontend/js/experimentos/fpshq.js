// Exclusivo do laboratório: não importar este cliente nas páginas de produção.
export const FPSHQ_BASE = "https://fpshq.com/api/public/v1/";
export const REFERENCIA_FPS = Object.freeze({cpu:"ryzen-5-5600",gpu:"rtx-3060"});
export const JOGOS_INICIAIS = Object.freeze([
  {slug:"valorant",name:"Valorant"}, {slug:"cs2",name:"Counter-Strike 2"},
  {slug:"fortnite",name:"Fortnite"}, {slug:"cyberpunk-2077",name:"Cyberpunk 2077"},
  {slug:"red-dead-redemption-2",name:"Red Dead Redemption 2"},
]);
const TTL = 60 * 60 * 1000;
const SLUG = /^[a-z0-9-]{1,190}$/;
const finito = valor => typeof valor === "number" && Number.isFinite(valor) && valor >= 0 ? valor : null;
export class ErroFPSHQ extends Error {
  constructor(mensagem,codigo = "api",espera = 0) { super(mensagem); this.name = "ErroFPSHQ"; this.codigo = codigo; this.espera = espera; }
}
export function validarConsulta({game,cpu,gpu,res = "1080p",preset = "high"}) {
  if (![game,cpu,gpu].every(valor => typeof valor === "string" && SLUG.test(valor)))
    throw new ErroFPSHQ("Identifique o jogo, processador e GPU aceitos pelo provedor.","entrada");
  if (!["1080p","1440p","4k"].includes(res) || !["low","medium","high","ultra"].includes(preset))
    throw new ErroFPSHQ("Selecione uma resolução e uma qualidade válidas.","entrada");
  return {game,cpu,gpu,res,preset};
}
export function normalizarResultado(dados,consulta) {
  if (dados?.ok !== true || dados.game?.slug !== consulta.game || dados.cpu?.slug !== consulta.cpu || dados.gpu?.slug !== consulta.gpu)
    throw new ErroFPSHQ("O provedor não confirmou a combinação de peças solicitada.","resposta");
  if (String(dados.res).toLowerCase() !== consulta.res || dados.preset !== consulta.preset)
    throw new ErroFPSHQ("O provedor retornou configurações diferentes das solicitadas.","resposta");
  const fps = finito(dados.fps);
  if (fps == null) throw new ErroFPSHQ("Não há desempenho disponível para esta combinação e configuração.","sem-dados");
  const intervalo = Array.isArray(dados.fps_range) && dados.fps_range.length === 2
    && dados.fps_range.every(valor => finito(valor) != null) && dados.fps_range[0] <= dados.fps_range[1]
    ? dados.fps_range : null;
  return {
    consulta, jogo:String(dados.game.name || consulta.game), fps, low1:finito(dados.low1), intervalo,
    origem:["measured","model"].includes(dados.source) ? dados.source : "unknown",
    base:["measured","aggregate","model"].includes(dados.basis) ? dados.basis : null,
    confianca:["high","medium","low"].includes(dados.confidence) ? dados.confidence : null,
    matriz:Object.fromEntries(["1080p","1440p","4K"].map(res => [res,
      Object.fromEntries(["low","medium","high","ultra"].map(preset => [preset,finito(dados.matrix?.[res]?.[preset])]))])),
    // O verdict da API usa 1080p High, não necessariamente a escolha atual. Não o reutilizar.
    url:"https://fpshq.com/pt/games/" + consulta.game + "/",
  };
}
export function criarClienteFPSHQ({fetcher = (...args) => fetch(...args),agora = Date.now,armazenamento = null,timeoutMs = 20000} = {}) {
  const memoria = new Map(), pendentes = new Map();
  let bloqueadoAte = 0;
  function ler(chave) {
    try {
      const item = memoria.get(chave) || JSON.parse(armazenamento?.getItem(chave) || "null");
      if (item && Number.isFinite(item.data) && item.data <= agora() && agora() - item.data < TTL) return item;
    } catch { /* Armazenamento indisponível não impede uma consulta explícita. */ }
    return null;
  }
  async function requisitar(caminho,parametros,{signal} = {}) {
    if (signal?.aborted) throw new ErroFPSHQ("Consulta cancelada.","cancelado");
    const url = new URL(caminho,FPSHQ_BASE);
    url.search = new URLSearchParams({...parametros,lang:"pt"});
    const chave = "boostio:fpshq-teste:v1:" + url.search;
    const salvo = ler(chave);
    if (salvo) return {...salvo,cache:true};
    if (pendentes.has(chave)) return pendentes.get(chave);
    if (agora() < bloqueadoAte) throw new ErroFPSHQ("Aguarde alguns segundos antes de consultar novamente.","limite",Math.ceil((bloqueadoAte - agora()) / 1000));
    bloqueadoAte = agora() + 1500;
    const promessa = (async () => {
      const controle = new AbortController();
      const cancelar = () => controle.abort();
      signal?.addEventListener("abort",cancelar,{once:true});
      const temporizador = setTimeout(() => controle.abort(),timeoutMs);
      try {
        const resposta = await fetcher(url.href,{signal:controle.signal,credentials:"omit",referrerPolicy:"no-referrer",headers:{Accept:"application/json"}});
        if (resposta.status === 429) {
          const retry = Number(resposta.headers.get("Retry-After"));
          const espera = Number.isFinite(retry) && retry > 0 ? Math.min(3600,Math.ceil(retry)) : 60;
          bloqueadoAte = agora() + espera * 1000;
          throw new ErroFPSHQ("O limite da FPSHQ foi atingido. Tente novamente após a espera informada.","limite",espera);
        }
        if (resposta.status === 404) throw new ErroFPSHQ("Jogo ou componente não encontrado pelo provedor.","nao-encontrado");
        if (!resposta.ok) throw new ErroFPSHQ("A FPSHQ não conseguiu atender à consulta agora. Tente novamente mais tarde.","http");
        let dados;
        try { dados = await resposta.json(); }
        catch { throw new ErroFPSHQ("A FPSHQ retornou uma resposta inválida. Tente novamente mais tarde.","resposta"); }
        if (dados?.ok !== true) throw new ErroFPSHQ("Não há dados disponíveis para esta consulta.","sem-dados");
        const item = {dados,data:agora()};
        memoria.set(chave,item);
        try { armazenamento?.setItem(chave,JSON.stringify(item)); } catch { /* Cache em memória permanece ativo. */ }
        return {...item,cache:false};
      } catch (erro) {
        if (erro instanceof ErroFPSHQ) throw erro;
        if (signal?.aborted) throw new ErroFPSHQ("Consulta cancelada.","cancelado");
        throw new ErroFPSHQ(controle.signal.aborted ? "A consulta demorou demais. Tente novamente." : "Não foi possível acessar a FPSHQ. Confira a conexão e tente novamente.",controle.signal.aborted ? "timeout" : "rede");
      } finally { clearTimeout(temporizador); signal?.removeEventListener("abort",cancelar); }
    })();
    pendentes.set(chave,promessa);
    try { return await promessa; } finally { pendentes.delete(chave); }
  }
  return {
    async consultar(entrada,opcoes) {
      const consulta = validarConsulta(entrada);
      const resposta = await requisitar("fps",consulta,opcoes);
      return {...normalizarResultado(resposta.dados,consulta),consultadoEm:resposta.data,cache:resposta.cache};
    },
    async buscarJogos(texto,opcoes) {
      const q = String(texto || "").trim();
      if (q.length < 2 || q.length > 60) throw new ErroFPSHQ("Digite entre 2 e 60 caracteres para buscar um jogo.","entrada");
      const {dados} = await requisitar("games",{q},opcoes);
      if (!Array.isArray(dados.results)) throw new ErroFPSHQ("A busca retornou um formato inesperado.","resposta");
      return dados.results.filter(jogo => typeof jogo.slug === "string" && SLUG.test(jogo.slug) && typeof jogo.name === "string")
        .slice(0,10).map(({slug,name}) => ({slug,name:name.slice(0,180)}));
    },
  };
}
