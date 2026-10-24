import { selecionarPeca, informacoesArmazenamento, itensSelecionados } from "./estado.js";
import { exigirTrocaMelhoria } from "./validar-melhoria.js";
import { numeroConhecido } from "./hardware.js";

// A expansão preserva os volumes existentes; a substituição continua explícita.
// O seletor do editor confere M.2/SATA, portas compartilhadas e quantidades.
export function planejarMelhoriaDisco(build,peca,catalogo,{modo = "adicionar",quantidade = 1} = {}) {
  if (build?.travada) throw new Error("Destranque a build para melhorar o armazenamento.");
  if (!["ssd","hd"].includes(peca?.categoria) || !["adicionar","substituir"].includes(modo))
    throw new Error("Proposta de armazenamento inválida.");
  if (!Number.isInteger(quantidade)||quantidade<1||quantidade>64||modo==="substituir"&&quantidade!==1)
    throw new Error("Informe de 1 a 64 unidades para adicionar; a substituição usa uma unidade.");
  if (peca.esgotado || !["number","string"].includes(typeof peca.preco)
    || !String(peca.preco).trim() || !Number.isFinite(Number(peca.preco)) || Number(peca.preco) <= 0)
    throw new Error("O disco escolhido está indisponível ou sem preço válido.");
  exigirTrocaMelhoria(build,peca,catalogo,{modo});
  const base = structuredClone(build);
  if (modo === "substituir") delete base.componentes[peca.categoria];
  let selecionada=base;
  for (let unidade=0;unidade<quantidade;unidade++) selecionada=selecionarPeca(selecionada,peca,catalogo);
  const proxima = {...base,componentes:selecionada.componentes};
  const gabinete=catalogo.find(p=>p.categoria==="gabinete"&&p.id===proxima.componentes.gabinete?.id);
  const discos=itensSelecionados(proxima,catalogo).filter(i=>["ssd","hd"].includes(i.categoria));
  for (const [formato,campo] of [["2.5","baias_25"],["3.5","baias_35"]]) {
    const usados=discos.filter(({peca:p})=>String(p?.formato||"").replaceAll('"',"")===formato).reduce((s,{item})=>s+item.quantidade,0);
    const limite=numeroConhecido(gabinete?.[campo]);
    if (limite!=null&&usados>limite) throw new Error("As unidades de "+formato+" polegadas excedem as baias do gabinete.");
  }
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
