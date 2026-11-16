import { normalizarAparencia, estilosGabinete } from "./aparencia.js";

export function validarEstiloGabinete(catalogo, preferencia = {}, referencias = []) {
  const atual = normalizarAparencia(preferencia);
  const modelos = [...catalogo, ...referencias];
  const bloqueados = atual.porte === "sem-preferencia" ? [] : estilosGabinete
    .map(([valor]) => valor)
    .filter(estilo => !["sem-preferencia", "compacto"].includes(estilo)
      && !modelos.some(p => p.categoria === "gabinete" && p.porte_referencia === atual.porte && p.estilo_referencia === estilo));
  const alterado = bloqueados.includes(atual.estilo);
  return {bloqueados, estilo:alterado ? "sem-preferencia" : atual.estilo, alterado};
}

// Ausência de classificação não prova que a combinação não existe.
export function avaliarGabinetes(catalogo, preferencia = {}) {
  const {porte, estilo, cor} = normalizarAparencia(preferencia);
  const gabinetes = catalogo.filter(p => p.categoria === "gabinete");
  const corresponde = p => (porte === "sem-preferencia" || p.porte_referencia === porte)
    && (estilo === "sem-preferencia" || p.estilo_referencia === estilo)
    && (cor === "sem-preferencia" || (p.cor_referencia?.length && p.cor_referencia.every(c => cor === "misto" ? ["preto", "branco"].includes(c) : c === cor)));
  const pendente = p => !corresponde(p)
    && (porte === "sem-preferencia" || !p.porte_referencia || p.porte_referencia === porte)
    && (estilo === "sem-preferencia" || !p.estilo_referencia || p.estilo_referencia === estilo)
    && (cor === "sem-preferencia" || !p.cor_referencia?.length || p.cor_referencia.every(c => cor === "misto" ? ["preto", "branco"].includes(c) : c === cor));
  const identificados = gabinetes.filter(corresponde);
  const disponiveis = identificados.filter(p => p.disponivel === true);
  const dadosPendentes = gabinetes.filter(pendente).length;
  const estado = !gabinetes.length ? "sem-dados" : disponiveis.length ? "disponivel"
    : identificados.length ? "indisponivel" : dadosPendentes ? "dados-insuficientes" : "sem-modelos";
  return {estado, identificados, disponiveis, dadosPendentes};
}
