import { selecionarPecaCompativel } from "./compatibilidade.js";
import { nomePeca, htmlSeguro as h } from "./catalogo.js";

const normal = valor => String(valor || "").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
const rotulos = {estoque:"Indisponíveis",trancada:"Build trancada",selecionada:"Peça já selecionada",ddr:"Padrão DDR ou frequência incompatível",
  slots:"Slots ou capacidade de RAM",dados:"Dados insuficientes",encaixe:"Espaço ou formato incompatível",conexoes:"Conexões de armazenamento",conflito:"Outros conflitos"};
function grupo(motivo) {
  const texto=normal(motivo);
  if (/indisponivel/.test(texto)) return "estoque";
  if (/destranque|trancada/.test(texto)) return "trancada";
  if (/remova.*atual/.test(texto)) return "selecionada";
  if (/falta|identifique|confirme|selecione a placa/.test(texto)) return "dados";
  if (/ddr|frequencia/.test(texto)) return "ddr";
  if (/pentes|ram.*maximo|capacidade de ram/.test(texto)) return "slots";
  if (/ultrapassa|baias|gabinete|radiador|fisic|cooler.*altura/.test(texto)) return "encaixe";
  if (/m\.2|sata|conexoes|discos/.test(texto)) return "conexoes";
  return "conflito";
}

export function filtrarPecasCatalogo(build,produtos,catalogo,{busca="",marca=""}={}) {
  const consideradas=produtos.filter(p=>normal(nomePeca(p)).includes(normal(busca))&&(!marca||p.fabricante===marca));
  const incluidas=[],excluidas=[];
  for (const peca of consideradas) {
    try { selecionarPecaCompativel(build,peca,catalogo); incluidas.push(peca); }
    catch (erro) {
      const motivo=erro.message||"Não foi possível validar esta peça.";
      excluidas.push({peca,motivo,grupo:grupo(motivo)});
    }
  }
  return {incluidas,excluidas,consideradas:consideradas.length};
}

export function motivosCatalogoHtml(excluidas,{aberto=false}={}) {
  if (!excluidas.length) return "";
  const grupos=new Map();
  for (const item of excluidas) { if (!grupos.has(item.grupo)) grupos.set(item.grupo,[]); grupos.get(item.grupo).push(item); }
  return '<details class="catalog-exclusions glass-card"'+(aberto?' open':'')+'><summary>Por que outras peças não aparecem? ('+excluidas.length+')</summary><ul>'
    +[...grupos].map(([codigo,itens])=>'<li><strong>'+h(rotulos[codigo])+' · '+itens.length+'</strong><ul>'
      +itens.slice(0,3).map(({peca,motivo})=>'<li>'+h(nomePeca(peca))+': '+h(motivo)+'</li>').join('')
      +(itens.length>3?'<li>Mais '+(itens.length-3)+' modelo(s) com esse tipo de restrição.</li>':'')+'</ul></li>').join('')+'</ul></details>';
}
