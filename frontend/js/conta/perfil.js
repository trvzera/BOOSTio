import { buscarUsuarioLogado } from "../api/usuario/buscarUsuarioLogado.js";
import { sincronizarBudgetPerfil } from "../build/planejamento.js";
import { sincronizarExperiencia } from "./preferencias-uso.js";

let pendente = null, revisao = 0, atual = {auth:false,usuario:null};
function aplicar(resposta) {
  if ((atual.auth ? atual.usuario?.id : null) !== (resposta.auth ? resposta.usuario?.id : null)) revisao++;
  atual = resposta;
  sincronizarBudgetPerfil(resposta.auth ? resposta.usuario : null);
  sincronizarExperiencia(resposta.auth ? resposta.usuario : null);
  return atual;
}
export function revisaoPerfil() { return revisao; }
export function perfilAtual() { return atual; }
export function atualizarPerfil(usuario, revisaoEsperada = revisao) {
  if (revisaoEsperada !== revisao) return null;
  revisao++;
  pendente = null;
  return aplicar({auth:Boolean(usuario),usuario:usuario || null});
}
export function limparPerfil() { return atualizarPerfil(null); }

// Compartilha somente consultas simultâneas. Cada nova página revalida a sessão.
export function carregarPerfil() {
  if (pendente) return pendente;
  const versao = revisao, controle = new AbortController();
  const timeout = setTimeout(() => controle.abort(),8000);
  const consulta = buscarUsuarioLogado({signal:controle.signal})
    .then(resposta => versao === revisao ? aplicar(resposta) : atual)
    .catch(erro => {
      if (versao !== revisao) return atual;
      aplicar({auth:false,usuario:null});
      if (erro.name === "AbortError") throw new Error("A consulta da conta demorou demais. Tente novamente.");
      throw erro;
    }).finally(() => {
      clearTimeout(timeout);
      if (pendente === consulta) pendente = null;
    });
  pendente = consulta;
  return consulta;
}
