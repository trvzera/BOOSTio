import { htmlSeguro as h, imagemPeca, nomePeca, moeda } from "./catalogo.js";

export const estilosGabinete=[['sem-preferencia','Sem preferência'],['discreto','Discreto'],['vidro','Com vidro'],['compacto','Compacto'],['panoramico','Panorâmico']];
export const coresSetup=[['sem-preferencia','Sem preferência'],['preto','Preto'],['branco','Branco'],['misto','Preto e branco']];
export function normalizarAparencia(valor={}) {
  return {estilo:estilosGabinete.some(([v])=>v===valor?.estilo)?valor.estilo:'sem-preferencia',
    cor:coresSetup.some(([v])=>v===valor?.cor)?valor.cor:'sem-preferencia',
    gabinete_id:Number.isInteger(valor?.gabinete_id)&&valor.gabinete_id>0&&valor.gabinete_id<=1000000000?valor.gabinete_id:null};
}
export function aparenciaHtml(valor,catalogo,{orcamento,possuiGabinete=false}={}) {
  const atual=normalizarAparencia(valor);
  const campo=(id,titulo,opcoes,selecionado)=>'<label class="appearance-field" for="'+id+'"><span>'+titulo+'</span><select id="'+id+'">'+opcoes.map(([v,n])=>'<option value="'+v+'" '+(v===selecionado?'selected':'')+'>'+n+'</option>').join('')+'</select></label>';
  const idPeca=p=>Number(String(p.id).split(':').at(-1));
  const disponiveis=catalogo.filter(p=>p.categoria==='gabinete'&&p.esgotado===false&&Number.isFinite(p.preco)&&p.preco>0&&Number.isInteger(idPeca(p))&&idPeca(p)>0&&(!orcamento||p.preco<=orcamento)).sort((a,b)=>a.preco-b.preco);
  const referencias=disponiveis.length<=6?disponiveis:Array.from({length:6},(_,i)=>disponiveis[Math.round(i*(disponiveis.length-1)/5)]);
  const escolhida=disponiveis.find(p=>idPeca(p)===atual.gabinete_id);
  if(escolhida&&!referencias.includes(escolhida))referencias[referencias.length-1]=escolhida;
  return '<div class="appearance-fields">'+campo('appearance-style','Estilo do gabinete',estilosGabinete,atual.estilo)+campo('appearance-color','Cor do setup',coresSetup,atual.cor)+'</div>'
    +'<p class="font-2-xs planning-help">Preferências, não exigências. Compatibilidade, orçamento e disponibilidade vêm primeiro. A cor só será considerada quando informada no catálogo.</p>'
    +(possuiGabinete?'<p class="font-2-xs">O gabinete que você já possui será preservado.</p>':
      '<fieldset class="appearance-references"><legend class="font-1-xs">Algum destes modelos combina com você?</legend><label class="appearance-no-preference font-2-xs"><input type="radio" name="case-reference" value="" '+(!escolhida?'checked':'')+'> Sem modelo de referência</label>'
      +(referencias.length?'<div class="appearance-cases" role="region" aria-label="Referências de gabinetes com imagens" tabindex="0">'+referencias.map(p=>{
        const id=Number(String(p.id).split(':').at(-1));
        return '<label class="appearance-case"><input type="radio" name="case-reference" value="'+id+'" '+(atual.gabinete_id===id?'checked':'')+'>'+imagemPeca(p,'appearance-case-image')+'<span>'+h(nomePeca(p))+'</span><small>'+h(moeda(p.preco))+'</small></label>';
      }).join('')+'</div>':'<p class="font-2-xs">Nenhum modelo disponível nesta faixa para mostrar como referência.</p>')+'</fieldset>');
}
