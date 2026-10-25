// Mesmo contrato de services/build_service/armazenamento.py. Sem inferência pelo nome.
export function contagem(valor) {
  if(!['number','string'].includes(typeof valor)||!String(valor).trim())return null;
  if(typeof valor==='string'&&!/^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$/.test(valor.trim()))return null;
  const n=Number(valor);return Number.isFinite(n)&&Number.isInteger(n)&&n>=0&&n<=4096?n:null;
}
export function conexaoDisco(peca) {
  if(!peca)return null;
  const formato=String(peca.formato||'').toUpperCase(),interfacePeca=String(peca.interface||peca.tipo||'').toUpperCase();
  if(['2.5','3.5','U.2','U.3','PCIE','ADD-IN-CARD'].includes(formatoDisco(peca).toUpperCase())&&/NVME|PCI[E-]/.test(interfacePeca))return null;
  if(/M\.?2|NVME|PCI[E-]/.test(formato+' '+interfacePeca))return /SATA/.test(interfacePeca)?'m2-sata':'m2';
  return /SATA/.test(interfacePeca)?'sata':null;
}
export function formatoDisco(peca) {return String(peca?.formato||'').trim().replaceAll(',','.').replace(/[\s"\u2033]|polegadas|inch/gi,'');}
export function formatoM2(peca) {return /^(?:M\.?2[\s-]*)?(2230|2242|2260|2280|22110)$/.exec(String(peca?.formato_m2||peca?.formato||'').toUpperCase().trim())?.[1]??null;}

export function encaixeM2(placa,discos,sata) {
  const slots=placa.slots_m2,portas=placa.portas_sata;
  if(!Array.isArray(slots)||slots.length>16||slots.some(s=>!s||typeof s!=='object'||typeof s.nome!=='string'||!s.nome.trim())||new Set(slots.map(s=>s.nome)).size!==slots.length)return null;
  const declarados=contagem(placa.quantidade_slots_m2);
  if(declarados!==null&&declarados!==slots.length)return null;
  if(discos.reduce((s,[,q])=>s+q,0)>slots.length)return declarados!==null||placa.topologia_armazenamento_verificada===true?false:null;
  const unidades=discos.flatMap(([p,q])=>Array.from({length:q},()=>[p,formatoM2(p)]));
  const portasOk=Array.isArray(portas)&&portas.length<=64&&portas.every(p=>typeof p==='string'&&p.trim())&&new Set(portas).size===portas.length;
  if(portas!=null&&!portasOk)return null;
  let limite=contagem(placa.quantidade_portas_sata);
  if(portasOk&&limite!==null&&portas.length!==limite)return null;
  if(portasOk)limite=portas.length;
  let visitas=0;const cache=new Map(),limiteBusca={};
  function tentar(i,ocupados,desativadas) {
    const chave=JSON.stringify([i,ocupados,desativadas]);if(cache.has(chave))return cache.get(chave);
    if(++visitas>10000)throw limiteBusca;
    if(limite!==null&&sata+desativadas.length>limite)return false;
    if(i===unidades.length)return !sata||limite!==null?true:null;
    const [peca,formato]=unidades[i],conexao=conexaoDisco(peca);let pendente=false;
    for(let j=0;j<slots.length;j++){
      if(ocupados&(1<<j))continue;
      const slot=slots[j],interfaces=slot.interfaces,formatos=slot.formatos;
      const interfacesOk=Array.isArray(interfaces)&&interfaces.length>0&&interfaces.every(v=>['m2','m2-sata'].includes(v));
      const formatosOk=Array.isArray(formatos)&&formatos.length>0&&formatos.every(f=>formatoM2({formato:f})===f);
      if(interfacesOk&&!interfaces.includes(conexao)||formatosOk&&formato&&!formatos.includes(formato))continue;
      let conhecido=interfacesOk&&formatosOk&&formato!==null&&slot.condicional_cpu===false,removidas=[];
      if(sata){
        removidas=slot.portas_sata_desativadas?.[conexao];
        const perdasOk=Array.isArray(removidas)&&limite!==null&&removidas.every(p=>typeof p==='string'&&p.trim().length>0&&p.trim().length<=64)&&new Set(removidas).size<=limite&&(!portasOk||removidas.every(p=>portas.includes(p)));
        conhecido=conhecido&&perdasOk;if(!perdasOk)removidas=[];
      }
      const resultado=tentar(i+1,ocupados|(1<<j),[...new Set([...desativadas,...removidas])].sort());
      if(resultado===true&&conhecido){cache.set(chave,true);return true;}
      if(resultado===null||resultado===true)pendente=true;
    }
    const resultado=pendente?null:false;cache.set(chave,resultado);return resultado;
  }
  let resultado;try{resultado=tentar(0,0,[]);}catch(erro){if(erro===limiteBusca)return null;throw erro;}
  if(resultado===false&&declarados===null&&placa.topologia_armazenamento_verificada!==true)return null;
  return resultado===true&&placa.topologia_armazenamento_verificada!==true?null:resultado;
}

export function avaliarArmazenamento(placa,discos) {
  const regras=[],adicionar=(codigo,titulo,condicao,mensagem)=>regras.push({codigo,titulo,condicao,mensagem});
  let conhecidos=true,quantidadesOk=true,sata=0,m2sata=0;const m2=[];
  for(const [item,peca] of discos){
    const q=contagem(item.quantidade===undefined?1:item.quantidade),conexao=conexaoDisco(peca);
    if(q===null||q<1){quantidadesOk=false;continue;}
    if(['m2','m2-sata'].includes(conexao)){m2.push([peca,q]);if(conexao==='m2-sata')m2sata+=q;}
    else if(conexao==='sata')sata+=q;else conhecidos=false;
  }
  adicionar('discos-interface','Identificação dos discos',conhecidos&&quantidadesOk?true:null,
    conhecidos&&quantidadesOk?'As conexões dos discos estão identificadas.':'Falta identificar a conexão ou a quantidade de algum SSD/HD; não foi presumido NVMe ou SATA.');
  const usadosM2=m2.reduce((s,[,q])=>s+q,0);
  for(const [usados,campo,codigo,nome] of [[usadosM2,'quantidade_slots_m2','discos-m2','slots M.2'],[m2sata,'quantidade_slots_m2_sata','m2-sata','slots M.2 com suporte a SATA']]){
    if(usados){const limite=contagem(placa[campo]);adicionar(codigo,'Conexões '+nome,limite!==null?usados<=limite:null,
      limite!==null?`${usados} SSD(s) para ${limite} ${nome}.`:`Falta a quantidade de ${nome} da placa-mãe.`);}
  }
  const limite=contagem(placa.quantidade_portas_sata),perdas=contagem(placa.portas_sata_desativadas_por_m2_sata);
  const porSlot=Array.isArray(placa.slots_m2)&&placa.topologia_armazenamento_verificada===true;
  const limiteSata=porSlot||!m2sata?limite:limite!==null&&perdas!==null?Math.max(0,limite-m2sata*perdas):null;
  let encaixe=usadosM2&&quantidadesOk?encaixeM2(placa,m2,sata):null;
  let condicaoSata=limiteSata!==null?sata<=limiteSata:limite!==null&&sata>limite?false:null;
  if(porSlot&&usadosM2&&condicaoSata===true)condicaoSata=encaixe===true?true:null;
  if(sata)adicionar('discos-sata','Portas SATA disponíveis',condicaoSata,
    porSlot&&limiteSata!==null?`${sata} disco(s) SATA; capacidade física: ${limiteSata}. A distribuição dos M.2 define quais portas ficam disponíveis.`:
    limiteSata!==null?`${sata} disco(s); limite SATA considerando as perdas cadastradas: ${limiteSata}.`:'Falta confirmar as portas SATA disponíveis após instalar os SSDs M.2.');
  if(!usadosM2&&conhecidos&&quantidadesOk&&limite!==null)encaixe=sata<=limite;
  if((!conhecidos||!quantidadesOk)&&encaixe!==false)encaixe=null;
  adicionar('discos-compartilhamento','Encaixe e compartilhamento M.2/SATA',encaixe,
    encaixe===true?'Os padrões e tamanhos dos SSDs cabem nos slots cadastrados, com portas SATA suficientes.':encaixe===false?
    'Não há distribuição dos SSDs nos slots e portas cadastrados: confira padrão, tamanho e portas SATA desativadas.':
    'Faltam detalhes dos slots: padrões aceitos, comprimento dos SSDs ou portas SATA compartilhadas. As baias são verificadas separadamente.');
  return regras;
}

export function avaliarBaias(gabinete,discos) {
  const usados={baias_25:0,baias_35:0},regras=[];let conhecidos=true;
  for(const [item,peca] of discos){
    if(['m2','m2-sata'].includes(conexaoDisco(peca)))continue;
    const formato=formatoDisco(peca),q=contagem(item.quantidade===undefined?1:item.quantidade);
    if(!['2.5','3.5'].includes(formato)||q===null||q<1){conhecidos=false;continue;}
    usados[formato==='2.5'?'baias_25':'baias_35']+=q;
  }
  if(!conhecidos)regras.push({codigo:'discos-baias-identificacao',titulo:'Formato dos discos e baias',condicao:null,mensagem:'Falta identificar o formato físico de algum SSD/HD para conferir as baias.'});
  for(const [campo,q] of Object.entries(usados))if(q){
    const limite=contagem(gabinete[campo]);regras.push({codigo:'baias-'+campo,titulo:'Baias de '+(campo==='baias_25'?'2,5':'3,5')+' polegadas',
      condicao:limite!==null?q<=limite:null,mensagem:limite!==null?`${q} disco(s); limite cadastrado: ${limite}.`:'Falta a quantidade de baias deste tamanho no gabinete.'});
  }
  const arranjos=gabinete.configuracoes_baias;
  if(!Object.values(usados).some(Boolean)||arranjos==null&&!Object.values(usados).every(Boolean))return regras;
  let resultado=null;
  if(Array.isArray(arranjos)&&arranjos.length>=1&&arranjos.length<=32){
    const validos=arranjos.filter(a=>a!==null&&typeof a==='object'&&!Array.isArray(a)&&Object.keys(usados).every(c=>contagem(a[c])!==null));
    if(validos.some(a=>Object.keys(usados).every(c=>usados[c]<=contagem(a[c]))))resultado=conhecidos?true:null;
    else if(validos.length===arranjos.length&&gabinete.configuracoes_baias_completas===true)resultado=false;
  }
  regras.push({codigo:'baias-conjunto',titulo:'Baias usadas ao mesmo tempo',condicao:resultado,mensagem:resultado===true?
    'Os discos cabem juntos em um arranjo de baias cadastrado.':resultado===false?
    'Os SSDs/HDs não cabem juntos nas baias compartilhadas deste gabinete.':
    'Falta confirmar quais baias podem ser usadas ao mesmo tempo; não some montagens alternativas.'});
  return regras;
}
