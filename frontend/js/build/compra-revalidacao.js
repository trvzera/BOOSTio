import { itensSelecionados } from "./estado.js";
const preco = valor => typeof valor === "number" && Number.isFinite(valor) && valor > 0 ? Math.round(valor*100) : null;

export function compararCatalogosCompra(build,anterior,atual) {
  if (!Array.isArray(atual)) throw new Error("Não foi possível confirmar o catálogo atualizado.");
  const linhas=itensSelecionados(build,anterior).map(({categoria,item,peca:antes})=>{
    const depois=atual.find(p=>p.categoria===categoria&&p.id===item.id);
    const antigo=preco(antes?.preco),novo=preco(depois?.preco);
    return {categoria,item,antes,depois,antigo,novo,
      indisponivel:!depois||depois.esgotado!==false||novo==null,
      alterado:antigo!==novo||antes?.esgotado!==depois?.esgotado,
      diferenca:antigo!=null&&novo!=null?(novo-antigo)*item.quantidade:null};
  });
  const total = chave => linhas.reduce((s,l)=>s+(l[chave]||0)*l.item.quantidade,0);
  const completo=linhas.length>0&&linhas.every(l=>l.antigo!=null&&l.novo!=null);
  return {linhas,antes:total("antigo"),depois:total("novo"),parcial:!completo||linhas.some(l=>l.indisponivel),
    diferenca:completo?total("novo")-total("antigo"):null};
}
