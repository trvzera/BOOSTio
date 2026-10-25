const tipos = {
  "placa-mae":"placa_mae", "placa-video":"placa_video", memoria:"memoria_ram",
  cooler:"air_cooler", "water-cooler":"water_cooler", fans:"fan", headset:"fone",
};
export const categoriaPecaPropria=tipo=>tipos[tipo]||tipo;
export function reconhecerPecaPropria(catalogo,tipo,nome) {
  const normalizar=v=>String(v||"").trim().replace(/\s+/g," ").toLocaleLowerCase("pt-BR");
  const valor=normalizar(nome),categoria=categoriaPecaPropria(tipo);
  if(!valor)return {estado:"vazio",peca:null};
  const exatas=catalogo.filter(p=>p.categoria===categoria&&[p.modelo,[p.fabricante,p.modelo].filter(Boolean).join(" ")].some(n=>normalizar(n)===valor));
  return {estado:exatas.length===1?"encontrada":exatas.length>1?"ambigua":"nao_encontrada",peca:exatas.length===1?exatas[0]:null};
}

export function pecasPropriasFormulario(respostas) {
  const escolhidas = [...(respostas.pecas || []),...(respostas.perifericos === "alguns-perifericos" ? respostas.perifericosProprios || [] : [])];
  return Object.fromEntries(escolhidas.filter(peca => peca !== "nenhuma")
    .map(peca => [tipos[peca] || peca,respostas.pecasDetalhes?.[peca]?.trim()])
    .filter(([,modelo]) => modelo));
}
