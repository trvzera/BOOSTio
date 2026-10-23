import { selecionarPeca, informacoesArmazenamento } from "./estado.js";
import { exigirTrocaMelhoria } from "./validar-melhoria.js";

// A expansão preserva os volumes existentes; a substituição continua explícita.
// O seletor do editor confere M.2/SATA, portas compartilhadas e quantidades.
export function planejarMelhoriaDisco(build,peca,catalogo,{modo = "adicionar"} = {}) {
  if (build?.travada) throw new Error("Destranque a build para melhorar o armazenamento.");
  if (!["ssd","hd"].includes(peca?.categoria) || !["adicionar","substituir"].includes(modo))
    throw new Error("Proposta de armazenamento inválida.");
  if (peca.esgotado || !["number","string"].includes(typeof peca.preco)
    || !String(peca.preco).trim() || !Number.isFinite(Number(peca.preco)) || Number(peca.preco) <= 0)
    throw new Error("O disco escolhido está indisponível ou sem preço válido.");
  exigirTrocaMelhoria(build,peca,catalogo,{modo});
  const base = structuredClone(build);
  if (modo === "substituir") delete base.componentes[peca.categoria];
  const selecionada = selecionarPeca(base,peca,catalogo);
  const proxima = {...base,componentes:selecionada.componentes};
  if (base.compatibilidade) {
    const info = informacoesArmazenamento(proxima,catalogo);
    const revalidados = new Set(["m2","sata"].filter(tipo => info[tipo] === 0
      || info.limites[tipo] != null && info[tipo] <= info.limites[tipo]).map(tipo => "discos-" + tipo));
    // Somente erros de conexões que o seletor acabou de conferir podem ficar obsoletos.
    // Não apagar diagnósticos das outras peças nem certificar limites desconhecidos.
    const erros = (base.compatibilidade.erros || []).filter(erro => !revalidados.has(erro.codigo));
    if (erros.length !== (base.compatibilidade.erros || []).length)
      proxima.compatibilidade = {status:erros.length ? "incompativel" : "nao_verificado",escopo:"parcial",
        rotulo:erros.length ? "Incompatibilidade identificada" : "Prévia local: revalidação pendente",erros,naoVerificado:[],
        aviso:"Conexões conferidas na prévia; o servidor reavalia a configuração ao salvar. Dados ausentes não estão certificados."};
  }
  return proxima;
}
