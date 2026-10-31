const campos=["componentes","incluirPerifericos","incluirRede","substituirFansWaterCooler"];
const estado=build=>Object.fromEntries(campos.map(c=>[c,structuredClone(build[c])]));
const ordenar=valor=>Array.isArray(valor)?valor.map(ordenar):valor&&typeof valor==="object"
  ?Object.fromEntries(Object.keys(valor).sort().map(k=>[k,ordenar(valor[k])])):valor;
const chave=valor=>JSON.stringify(ordenar(valor));

// Histórico limitado à aba/editor, sem gravar snapshots no storage.
export function criarHistoricoBuild({limite = 25} = {}) {
  const maximo = Number.isInteger(limite) && limite > 0 ? Math.min(limite,100) : 25;
  let anteriores = [], proximas = [];
  const motivo=(build,acao="desfazer")=>{
    const item = (acao === "refazer" ? proximas : anteriores).at(-1);
    return build.travada ? "Destranque a build para alterar os componentes."
      : !item || item.id !== build.id ? "Nenhuma alteração de peças para " + acao + " nesta página."
      : chave(estado(build)) !== chave(acao === "refazer" ? item.antes : item.depois)
        ? "A configuração mudou desde a última alteração. O histórico não será aplicado sobre outra configuração." : "";
  };
  function mover(build,acao) {
    const erro=motivo(build,acao);if(erro)throw new Error(erro);
    const origem=acao === "refazer" ? proximas : anteriores, destino=acao === "refazer" ? anteriores : proximas;
    const item=origem.pop();destino.push(item);
    const resultado={...structuredClone(build),...structuredClone(acao === "refazer" ? item.depois : item.antes)};
    delete resultado.compatibilidade;
    return resultado;
  }
  return {
    motivo,
    limpar() { anteriores=[];proximas=[]; },
    registrar(antes,depois) {
      if (antes.id!==depois.id||antes.travada||depois.travada) return;
      if (chave(estado(antes))===chave(estado(depois))) return;
      const ultimo=anteriores.at(-1);
      if(ultimo && (ultimo.id !== antes.id || chave(ultimo.depois) !== chave(estado(antes)))) anteriores=[];
      anteriores.push({id:antes.id,antes:estado(antes),depois:estado(depois)});
      if(anteriores.length>maximo)anteriores.shift();
      proximas=[];
    },
    desfazer:build=>mover(build,"desfazer"),
    refazer:build=>mover(build,"refazer"),
  };
}

export function acaoAtalhoHistorico(evento) {
  if(evento.defaultPrevented || evento.isComposing || evento.repeat || evento.altKey || !(evento.ctrlKey || evento.metaKey) || evento.key?.toLowerCase() !== "z")return null;
  if(evento.target?.closest?.('textarea,select,input:not([type="checkbox"]):not([type="radio"]),[contenteditable]:not([contenteditable="false"]),[role="textbox"]'))return null;
  return evento.shiftKey ? "refazer" : "desfazer";
}
