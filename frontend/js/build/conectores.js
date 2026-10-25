import { contagem,conexaoDisco,formatoDisco } from './armazenamento.js';
const tipos=['atx_24','eps_8','atx12v_4','eps_4_4','pcie_6','pcie_8','pcie_6_2','12vhpwr','12v_2x6','sata','molex_4'];
const rotulos={atx_24:'ATX de 24 pinos',eps_8:'EPS/CPU de 8 pinos',atx12v_4:'CPU de 4 pinos',eps_4_4:'EPS/CPU 4+4',pcie_6:'PCIe de 6 pinos',pcie_8:'PCIe de 8 pinos',pcie_6_2:'PCIe 6+2','12vhpwr':'12VHPWR','12v_2x6':'12V-2x6',sata:'SATA',molex_4:'Molex de 4 pinos'};
const objeto=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);

export function avaliarConectores(fonte,consumidores) {
  const exigidos={};let pendente=false,gpuMultiplos=false;
  for(const [categoria,item,dados] of consumidores){
    const peca=dados||{},quantidade=contagem(item.quantidade===undefined?1:item.quantidade);
    if(quantidade===null||quantidade<1){pendente=true;continue;}
    if(['ssd','hd'].includes(categoria)){
      const conexao=conexaoDisco(peca);
      if(['m2','m2-sata'].includes(conexao)&&String(peca.formato||'').toUpperCase().replaceAll('.','').startsWith('M2'))continue;
      if(conexao==='sata'&&['2.5','3.5'].includes(formatoDisco(peca))){exigidos.sata=(exigidos.sata||0)+quantidade;continue;}
    }
    const mapa=peca.conectores_alimentacao;
    if(!objeto(mapa)){pendente=true;continue;}
    if(peca.conectores_alimentacao_completos!==true)pendente=true;
    for(const [tipo,valor] of Object.entries(mapa)){
      const n=contagem(valor);if(!tipos.includes(tipo)||n===null)pendente=true;
      else {const necessario=tipo==='eps_4_4'?'eps_8':tipo==='pcie_6_2'?'pcie_8':tipo;exigidos[necessario]=(exigidos[necessario]||0)+n*quantidade;}
    }
    if(categoria==='placa_video'&&['pcie_6','pcie_8','pcie_6_2'].reduce((s,t)=>s+(contagem(mapa[t]??0)||0),0)>1)gpuMultiplos=true;
  }
  let inventario=fonte.conectores_alimentacao,completo=fonte.conectores_alimentacao_completos===true;
  if(!objeto(inventario)){inventario={};completo=false;pendente=true;}
  if(Object.entries(inventario).some(([t,n])=>!tipos.includes(t)||contagem(n)===null)){completo=false;pendente=true;}
  const disponivel=t=>contagem(Object.hasOwn(inventario,t)?inventario[t]:completo?0:null),conflitos=[];
  const grupos=[['eps_8','atx12v_4','eps_4_4'],['pcie_8','pcie_6','pcie_6_2']];
  const dezesseis=['12vhpwr','12v_2x6'];
  if(dezesseis.some(t=>exigidos[t])){
    const diretos=dezesseis.filter(t=>exigidos[t]).every(t=>disponivel(t)!==null&&exigidos[t]<=disponivel(t));
    if(!diretos){
      const totais=dezesseis.map(disponivel);
      if(totais.every(v=>v!==null)&&dezesseis.reduce((s,t)=>s+(exigidos[t]||0),0)>totais.reduce((s,v)=>s+v,0))conflitos.push('conectores de 16 pinos');else pendente=true;
    }
  }
  const agrupados=new Set([...grupos.flat(),...dezesseis]);grupos.push(...tipos.filter(t=>!agrupados.has(t)).map(t=>[t]));
  for(const grupo of grupos){
    const fixos=grupo.length===1?grupo:grupo.slice(0,-1),flex=grupo.length===1?null:grupo.at(-1);
    const usadosFlex=flex?(exigidos[flex]||0):0;let falta=usadosFlex,todosConhecidos=true;
    if(!grupo.some(t=>exigidos[t]))continue;
    for(const tipo of fixos){
      const precisa=exigidos[tipo]||0,possui=disponivel(tipo);
      if(precisa){
        falta+=Math.max(0,precisa-(possui||0));todosConhecidos=todosConhecidos&&possui!==null;
        const f=flex?disponivel(flex):0;
        if(possui!==null&&f!==null&&precisa>possui+Math.max(0,f-usadosFlex))conflitos.push(rotulos[tipo]);
      }
    }
    const livresFlex=flex?disponivel(flex):0;
    if(livresFlex!==null&&falta<=livresFlex)continue;
    if(todosConhecidos&&livresFlex!==null)conflitos.push(...grupo.filter(t=>exigidos[t]).map(t=>rotulos[t]));else pendente=true;
  }
  if(gpuMultiplos){
    const gpu=consumidores.find(([c])=>c==='placa_video')?.[2]||{};
    const minimo=contagem(gpu.cabos_pcie_independentes_minimos),cabos=contagem(fonte.cabos_pcie_independentes);
    if(minimo===null||cabos===null)pendente=true;else if(minimo>cabos)conflitos.push('cabos PCIe independentes');
  }
  if(conflitos.length)return [false,'A fonte não oferece conectores suficientes para: '+[...new Set(conflitos)].sort().join(', ')+'. EPS/CPU e PCIe não são intercambiáveis.'];
  if(pendente||!consumidores.length)return [null,'Faltam tipos/quantidades de conectores ou a exigência de cabos PCIe independentes. Não foi presumido adaptador nem que EPS/CPU seja PCIe.'];
  return [true,'Tipos e quantidades de conectores da placa-mãe, GPU e discos atendidos. Fans, hubs, adaptadores e limites elétricos por cabo precisam de conferência separada.'];
}
