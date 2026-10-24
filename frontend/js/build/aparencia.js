import { htmlSeguro as h, imagemPeca } from "./catalogo.js";

export const estilosGabinete=[['sem-preferencia','Sem preferência'],['discreto','Discreto'],['vidro','Vidro lateral'],['compacto','Compacto'],['panoramico','Panorâmico']];
export const portesGabinete=[['sem-preferencia','Sem preferência'],['mini-tower','Mini Tower'],['mid-tower','Mid Tower'],['full-tower','Full Tower']];
export const coresSetup=[['sem-preferencia','Sem preferência'],['preto','Preto'],['branco','Branco'],['misto','Preto e branco']];

// Exemplos visuais, não ofertas. As fontes/modelos estão em docs/geracao-build.md.
const exemplos={
  'mini-tower':{modelo:'Cooler Master MasterBox Q300L',imagem:'../imgs/produtos/gabinete-1.webp'},
  'mid-tower':{modelo:'Cooler Master MasterBox TD500',imagem:'../imgs/produtos/gabinete-2.webp'},
  'full-tower':{modelo:'Corsair 7000D Airflow',imagem:'../imgs/referencia-gabinete-full-tower.webp'},
  discreto:{modelo:'Rise Mode Office X1',imagem:'../imgs/produtos/gabinete-54.jpg'},
  vidro:{modelo:'NZXT H5 Flow',imagem:'../imgs/produtos/gabinete-43.jpg'},
  panoramico:{modelo:'Lian Li O11 Dynamic',imagem:'../imgs/produtos/gabinete-29.webp'},
};
export function normalizarAparencia(valor={}) {
  const escolher=(campo,opcoes)=>opcoes.some(([v])=>v===valor?.[campo])?valor[campo]:'sem-preferencia';
  return {estilo:escolher('estilo',estilosGabinete),porte:escolher('porte',portesGabinete),cor:escolher('cor',coresSetup),
    gabinete_id:Number.isInteger(valor?.gabinete_id)&&valor.gabinete_id>0&&valor.gabinete_id<=1000000000?valor.gabinete_id:null};
}
function referencias(campo,titulo,opcoes,atual) {
  return '<fieldset class="appearance-references"><legend class="font-1-xs">'+titulo+'</legend>'
    +'<label class="appearance-no-preference"><input type="radio" name="appearance-'+campo+'" value="sem-preferencia" '+(atual==='sem-preferencia'?'checked':'')+'> Sem preferência</label>'
    +'<div class="appearance-cases">'+opcoes.filter(([v])=>v!=='sem-preferencia'&&v!=='compacto').map(([v,n])=>{
      const foto=exemplos[v];
      return '<label class="appearance-case"><input type="radio" name="appearance-'+campo+'" value="'+v+'" '+(v===atual?'checked':'')+'>'+imagemPeca({...foto,categoria:'gabinete'},'appearance-case-image')+'<span>'+h(n)+'</span></label>';
    }).join('')+'</div></fieldset>';
}
export function aparenciaHtml(valor,_catalogo=[],{possuiGabinete=false}={}) {
  const atual=normalizarAparencia(valor);
  if(atual.estilo==='compacto')atual.estilo='sem-preferencia';
  return '<fieldset class="appearance-colors"><legend class="font-1-xs">Cor do setup</legend><div class="appearance-swatches">'+coresSetup.map(([v,n])=>
    '<label class="appearance-swatch"><input type="radio" name="appearance-color" value="'+v+'" '+(v===atual.cor?'checked':'')+'><span class="appearance-color-dot color-'+v+'" aria-hidden="true"></span><span>'+n+'</span></label>').join('')+'</div></fieldset>'
    +(possuiGabinete?'<p class="font-2-xs">O gabinete que você já possui será preservado.</p>':
      '<div class="appearance-examples" role="region" aria-label="Exemplos de porte e visual de gabinete" tabindex="0">'
      +referencias('size','Porte do gabinete',portesGabinete,atual.porte)
      +referencias('style','Visual do gabinete',estilosGabinete,atual.estilo)+'</div>')
    +'<p class="font-2-xs planning-help">As fotos mostram exemplos de tamanho e visual, não produtos que você precisa comprar. As peças devem caber e ficar dentro do seu orçamento. Só consideramos a cor quando ela está informada no cadastro.</p>';
}
