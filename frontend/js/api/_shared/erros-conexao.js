export function estaOffline() {
  return typeof navigator !== "undefined" && navigator.onLine === false;
}

export function erroConexao(causa,{servico="a BOOSTio",mutacao=false,codigo="conexao"}={}) {
  if(causa?.name==="AbortError")return causa;
  const offline=estaOffline();
  const mensagem=offline
    ? "Seu navegador indica que você está sem internet. Confira o Wi-Fi ou os dados móveis."
    : `Não conseguimos completar a conexão com ${servico}. Confira sua internet; o serviço pode estar indisponível.`;
  return Object.assign(new Error(mensagem+(mutacao?" Não foi possível confirmar o resultado. Confira se a alteração foi salva antes de repetir.":" Tente novamente em instantes.")),{
    codigo:offline?"offline":codigo,resultadoIncerto:mutacao,cause:causa,
  });
}

export function falhaLeituraConexao(erro) {
  return erro?.name==="TypeError" || erro?.name==="NetworkError";
}
