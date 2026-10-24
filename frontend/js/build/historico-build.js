const campos=["componentes","incluirPerifericos","incluirRede","substituirFansWaterCooler"];
const estado=build=>Object.fromEntries(campos.map(c=>[c,structuredClone(build[c])]));
const ordenar=valor=>Array.isArray(valor)?valor.map(ordenar):valor&&typeof valor==="object"
  ?Object.fromEntries(Object.keys(valor).sort().map(k=>[k,ordenar(valor[k])])):valor;
const chave=valor=>JSON.stringify(ordenar(valor));

// Um nível em memória, desta aba/editor. Não grava dados pessoais no storage.
export function criarHistoricoBuild() {
  let ultima;
  const motivo=build=>build.travada?"Destranque a build para desfazer alterações.":!ultima||ultima.id!==build.id
    ?"Nenhuma alteração de peças para desfazer nesta página.":chave(estado(build))!==ultima.depois
      ?"A configuração mudou desde a última alteração. O histórico não será aplicado sobre outra configuração.":"";
  return {
    motivo,
    registrar(antes,depois) {
      if (antes.id!==depois.id||antes.travada||depois.travada) return;
      if (chave(estado(antes))===chave(estado(depois))) return;
      ultima={id:antes.id,antes:estado(antes),depois:chave(estado(depois))};
    },
    desfazer(build) {
      const erro=motivo(build);if (erro) throw new Error(erro);
      const resultado={...structuredClone(build),...structuredClone(ultima.antes)};
      delete resultado.compatibilidade;
      ultima=null;return resultado;
    },
  };
}
