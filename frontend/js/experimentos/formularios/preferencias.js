import { memoriaSugerida, perfisUso } from "./objetivos.js";

export const prioridadesPreview = [
  ["desempenho", "Melhor desempenho"],
  ["custo_beneficio", "Maior custo-benefício"],
];
export const marcasPreview = [
  ["sem-preferencia", "Sem preferência"],
  ["intel", "Intel"],
  ["amd", "AMD"],
];
export const marcasNotebook = [
  ["sem-preferencia", "Sem preferência"],
  ["dell", "Dell"],
  ["lenovo", "Lenovo"],
  ["asus", "ASUS"],
  ["acer", "Acer"],
  ["hp", "HP"],
  ["samsung", "Samsung"],
  ["lg", "LG"],
  ["msi", "MSI"],
  ["avell", "Avell"],
  ["apple", "Apple"],
];
const linhasGamer = new Set([
  "sem-preferencia",
  "dell",
  "lenovo",
  "asus",
  "acer",
  "hp",
  "msi",
  "avell",
]);
export function motivoMarcaNotebook(
  marca,
  respostas,
  valorNotebook = respostas.orcamento,
) {
  if (!marcasNotebook.some(([v]) => v === marca))
    return "Escolha uma marca da lista.";
  if (respostas.objetivo === "jogos" && !linhasGamer.has(marca))
    return "Nesta prévia, foco em jogos usa as marcas com linhas gamer selecionadas. O modelo e os jogos ainda precisam ser conferidos.";
  if (
    marca === "apple" &&
    (!Number.isFinite(valorNotebook) || valorNotebook < 6000)
  )
    return "A regra desta prévia reserva pelo menos R$ 6.000 só para o notebook Apple, depois dos acessórios. Não é uma garantia de oferta.";
  return "";
}
export function criteriosUso(tipo, respostas, valorComputador) {
  const uso = perfisUso[respostas.objetivo];
  return {
    objetivo: respostas.objetivo,
    prioridades: uso?.prioridade,
    memoriaSugeridaGb: memoriaSugerida(respostas.objetivo, valorComputador),
    memoriaEscolhidaPeloUsuario: false,
    video: uso?.gpu,
    monitor: uso?.monitor,
    painelMonitorPermitido: ["IPS", "Fast IPS", "VA", "Fast VA"],
    ...(tipo === "pc"
      ? {
          fabricanteCpuObrigatorio:
            respostas.preferencia_processador === "sem-preferencia"
              ? null
              : respostas.preferencia_processador,
          aparenciaFlexivel: true,
          marcaCpuFlexivel: false,
        }
      : {
          marcaNotebookPreferida: respostas.marca_notebook,
          bateria: respostas.bateria,
          restricoesApple: {
            minimoNotebook: 6000,
            focoJogosPermitido: false,
            verificarAplicativos: true,
          },
        }),
  };
}
