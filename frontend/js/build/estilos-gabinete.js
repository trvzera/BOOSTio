import { portesGabinete } from "./aparencia.js";
import { validarEstiloGabinete } from "./disponibilidade-gabinete.js";

let carregamentoReferencias;
export function carregarReferenciasGabinetes() {
  carregamentoReferencias ??= fetch(new URL("../../data/referencias-gabinetes.json",import.meta.url))
    .then(async resposta => {
      if (!resposta.ok) throw new Error("Não foi possível carregar as referências de gabinete.");
      const dados = await resposta.json();
      return dados.modelos;
    }).catch(erro => { carregamentoReferencias = null; throw erro; });
  return carregamentoReferencias;
}

export function iniciarRestricoesEstiloGabinete(raiz, {aviso} = {}) {
  const estilos = raiz.querySelector(".appearance-references--style");
  if (!estilos) return null;
  const ajuda = document.createElement("p");
  ajuda.className = "font-2-xs appearance-style-help";
  ajuda.id = "appearance-style-availability-help";
  estilos.querySelector(".appearance-section-help").after(ajuda);
  estilos.setAttribute("aria-describedby", estilos.getAttribute("aria-describedby") + " " + ajuda.id);
  let falha = false;
  if (!aviso) {
    aviso = document.createElement("p");
    aviso.className = "appearance-style-feedback font-2-xs";
    aviso.setAttribute("role","status");
    aviso.hidden = true;
    estilos.append(aviso);
  }
  function atualizar(catalogo, preferencias, referencias = [], {pronto = true} = {}) {
    if (pronto) falha = false;
    const validacao = pronto ? validarEstiloGabinete(catalogo,preferencias,referencias)
      : {bloqueados:[],alterado:false,estilo:preferencias.estilo};
    estilos.querySelectorAll('[name="appearance-style"]').forEach(input => {
      const bloqueado = validacao.bloqueados.includes(input.value);
      input.disabled = bloqueado;
      const card = input.closest(".appearance-case");
      if (!card) return;
      let motivo = card.querySelector(".appearance-case-availability");
      if (bloqueado && !motivo) {
        motivo = document.createElement("span");
        motivo.className = "appearance-case-availability";
        motivo.id = input.getAttribute("aria-labelledby").replace(/-name$/, "-availability");
        motivo.textContent = "Opção ainda não confirmada para este tamanho";
        card.append(motivo);
        input.setAttribute("aria-describedby", input.getAttribute("aria-describedby") + " " + motivo.id);
      } else if (!bloqueado && motivo) {
        input.setAttribute("aria-describedby", input.getAttribute("aria-describedby").split(" ").filter(id => id !== motivo.id).join(" "));
        motivo.remove();
      }
    });
    if (validacao.alterado) estilos.querySelector('[value="sem-preferencia"]').checked = true;
    const nomePorte = portesGabinete.find(([v]) => v === preferencias.porte)?.[1];
    ajuda.textContent = !pronto ? (falha ? "Não foi possível conferir os estilos agora. Suas preferências serão consideradas ao montar a build." : "Carregando as referências de tamanho e estilo…")
      : preferencias.porte === "sem-preferencia" ? "Selecione um tamanho para conferir os estilos disponíveis."
      : validacao.bloqueados.length === 4 ? `Nenhum estilo identificado para o tamanho ${nomePorte.toLowerCase()}. Você pode manter o estilo sem preferência ou escolher outro tamanho.`
      : `Escolha um dos estilos confirmados para o tamanho ${nomePorte.toLowerCase()}.`;
    aviso.hidden = !validacao.alterado;
    aviso.textContent = validacao.alterado ? "O estilo anterior não está disponível para este tamanho e voltou para “Sem preferência”." : "";
    return validacao;
  }
  function falhou() {
    falha = true;
    ajuda.textContent = "Não foi possível conferir os estilos agora. Suas preferências serão consideradas ao montar a build.";
  }
  return {atualizar,falhou};
}
