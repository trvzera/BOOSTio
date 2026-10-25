import { API_URL } from "../../config.js";
import { erroConexao, falhaLeituraConexao } from "./erros-conexao.js";

function mensagemHttp(status) {
  if(status===401)return "Entre novamente na sua conta para continuar.";
  if(status===403)return "Não foi possível autorizar esta ação. Recarregue a página e tente novamente.";
  if(status===404)return "Não encontramos o que você pediu. Atualize a página ou volte à lista.";
  if(status===429)return "Muitas tentativas em pouco tempo. Aguarde um pouco antes de tentar novamente.";
  if(status>=500)return "A BOOSTio está com dificuldades para atender agora. Aguarde um pouco e tente novamente.";
  return "Não foi possível concluir o pedido. Confira as informações e tente novamente.";
}

function mensagemInformada(dados) {
  const texto=dados?.erro || dados?.mensagem;
  return typeof texto==="string" && texto.trim() && !/^(?:internal server error|bad gateway|service unavailable|unknown error)$/i.test(texto.trim()) ? texto : null;
}

// Somente os campos de diagnóstico conhecidos, sem corpo/headers de terceiros.
function diagnosticoSeguro(valor) {
  if(!valor || typeof valor!=="object")return undefined;
  const dados={};
  if(Number.isInteger(valor.httpProvedor)&&valor.httpProvedor>=100&&valor.httpProvedor<=599)dados.httpProvedor=valor.httpProvedor;
  if(["json","html","outro"].includes(valor.tipoResposta))dados.tipoResposta=valor.tipoResposta;
  if(typeof valor.redirecionamento==="boolean")dados.redirecionamento=valor.redirecionamento;
  if(valor.pausa===true)dados.pausa=true;
  return Object.keys(dados).length?dados:undefined;
}

export async function fetchComErro(caminho,opcoes={}) {
  const {headers,...resto}=opcoes,metodo=(resto.method||"GET").toUpperCase();
  const mutacao=!["GET","HEAD","OPTIONS","TRACE"].includes(metodo);
  async function buscar(url,config,incerto=false) {
    try { return await fetch(url,config); }
    catch(causa) { throw erroConexao(causa,{mutacao:incerto}); }
  }
  async function ler(resposta,incerto=false) {
    let dados;
    try { dados=await resposta.json(); }
    catch(causa) {
      if(causa?.name==="AbortError")throw causa;
      if(resposta.ok&&falhaLeituraConexao(causa))throw erroConexao(causa,{mutacao:incerto});
      const erro=new Error(!resposta.ok?mensagemHttp(resposta.status):"Não conseguimos entender a resposta da BOOSTio. Recarregue a página e tente novamente."+(incerto?" Confira se a alteração foi salva antes de repetir.":""));
      Object.assign(erro,{status:resposta.status,codigo:resposta.ok?"resposta":"http",resultadoIncerto:incerto&&resposta.ok,cause:causa});
      throw erro;
    }
    if(!resposta.ok) {
      const retry=Number(resposta.headers?.get?.("Retry-After"));
      throw Object.assign(new Error(mensagemInformada(dados)||mensagemHttp(resposta.status)),{
        status:resposta.status,codigo:typeof dados?.codigo==="string"?dados.codigo:"http",
        espera:Number.isFinite(dados?.espera)&&dados.espera>0?dados.espera:Number.isFinite(retry)&&retry>0&&retry<=86400?retry:0,
        diagnostico:diagnosticoSeguro(dados?.diagnostico),
      });
    }
    return dados;
  }
  let csrf={};
  if(mutacao) {
    const preparo=await buscar(`${API_URL}/auth/csrf`,{credentials:"include",cache:"no-store",signal:resto.signal});
    const dados=await ler(preparo);
    if(typeof dados?.csrf_token!=="string"||!dados.csrf_token.trim())
      throw Object.assign(new Error("Não conseguimos preparar esta ação com segurança. Recarregue a página e tente novamente."),{codigo:"resposta"});
    csrf={"X-CSRF-Token":dados.csrf_token};
  }
  const resposta=await buscar(`${API_URL}${caminho}`,{credentials:"include",...resto,headers:{"Content-Type":"application/json",...headers,...csrf}},mutacao);
  if(resposta.status===204&&resposta.ok)return null;
  return ler(resposta,mutacao);
}
