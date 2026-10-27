import { htmlSeguro as h, imagemPeca } from "./catalogo.js";

// Os valores anteriores continuam válidos para as builds já salvas.
export const estilosGabinete=[['sem-preferencia','Sem preferência'],['discreto','Sem vidro'],['vidro','Vidro lateral'],['compacto','Compacto'],['panoramico','Aquário'],['panoramico-3-faces','Panorâmico — 3 faces']];
export const portesGabinete=[['sem-preferencia','Sem preferência'],['mini-tower','Pequeno'],['mid-tower','Médio'],['full-tower','Grande']];
export const coresSetup=[['sem-preferencia','Sem preferência'],['preto','Preto'],['branco','Branco'],['misto','Preto e branco']];

// Exemplos visuais, não ofertas. As fontes/modelos estão em docs/geracao-build.md.
const exemplos={
  'mini-tower':{modelo:'Cooler Master MasterBox Q300L',imagem:'../imgs/produtos/gabinete-1.webp',descricao:'Mini Tower · ocupa menos espaço. Costuma usar placas-mãe menores.',
    medidas:'387 × 230 × 381 mm',placas:'Micro-ATX e Mini-ITX.',fans:'120 mm; na frente também aceita 140 mm.',radiador:'Até 240 mm na frente.'},
  'mid-tower':{modelo:'Cooler Master MasterBox TD500 ARGB',imagem:'../imgs/produtos/gabinete-2.webp',descricao:'Mid Tower · tamanho intermediário, com espaço para a maioria das montagens.',
    medidas:'493 × 217 × 469 mm',placas:'ATX, Micro-ATX e Mini-ITX, entre os formatos suportados.',fans:'120 ou 140 mm, conforme a posição.',radiador:'Até 360 mm na frente ou no teto, respeitando os limites de espaço do modelo.'},
  'full-tower':{modelo:'Corsair 7000D Airflow',imagem:'../imgs/referencia-gabinete-full-tower.webp',descricao:'Full Tower · ocupa mais espaço e permite montagens maiores, conforme o modelo.',
    medidas:'550 × 248 × 600 mm',placas:'ATX e E-ATX até 277 mm de largura, além de formatos menores.',fans:'120 ou 140 mm, conforme a posição.',radiador:'Até 480 mm na lateral ou 420 mm na frente/no teto. As combinações dependem da montagem.'},
  discreto:{modelo:'Rise Mode Office X1',imagem:'../imgs/produtos/gabinete-54.jpg',descricao:'Painéis fechados ou perfurados, sem janela transparente.'},
  vidro:{modelo:'NZXT H5 Flow',imagem:'../imgs/produtos/gabinete-43.jpg',descricao:'Lateral de vidro, com a frente fechada ou perfurada.'},
  panoramico:{modelo:'Lian Li O11 Dynamic',imagem:'../imgs/produtos/gabinete-29.webp',descricao:'Vidro na frente e na lateral. Esse visual pode custar mais que opções simples.'},
  'panoramico-3-faces':{modelo:'Lian Li O11 Vision',imagem:'../imgs/referencia-gabinete-tres-faces.webp',descricao:'Vidro na frente, na lateral e no teto. Pode ter um custo maior.'},
};

// Referências dos modelos das fotos, nunca regras gerais de compatibilidade.
export function guiaPorteGabineteHtml(porte) {
  const exemplo=portesGabinete.some(([v])=>v===porte)&&exemplos[porte];
  if(!exemplo)return '<p class="font-2-xs">Escolha um tamanho para ver medidas e encaixes de um modelo de exemplo. Não existe uma medida única para todos os Mini, Mid ou Full Tower.</p>';
  return '<details class="appearance-technical-guide"><summary class="font-1-xs">Ver medidas e encaixes do exemplo</summary><h2 class="font-1-xs">Exemplo de tamanho: '+h(exemplo.modelo)+'</h2><dl class="appearance-size-specs">'
    +[['Medidas externas',exemplo.medidas+' (profundidade × largura × altura).'],['Placa-mãe',exemplo.placas],['Ventoinhas (fans)',exemplo.fans],['Radiador do water cooler',exemplo.radiador]]
      .map(([nome,valor])=>'<div><dt>'+h(nome)+'</dt><dd>'+h(valor)+'</dd></div>').join('')
    +'</dl><p class="font-2-xs">Estas medidas são desse exemplo, não de todos os gabinetes desse tamanho. A montagem usa a ficha do modelo que for escolhido.</p></details>';
}

export function atualizarGuiaPorteGabinete(raiz,porte) {
  const guia=raiz.querySelector('#appearance-size-guide');
  if(!guia||guia.dataset.porte===porte)return;
  guia.innerHTML=guiaPorteGabineteHtml(porte);guia.dataset.porte=porte;
  const aviso=raiz.querySelector('#appearance-size-feedback');
  if(aviso)aviso.textContent=porte==='sem-preferencia'?'Tamanho sem preferência.':('Referência de '+(portesGabinete.find(([v])=>v===porte)?.[1]||'tamanho')+' atualizada abaixo das opções. Os encaixes variam por modelo.');
}
export function normalizarAparencia(valor={}) {
  const escolher=(campo,opcoes)=>opcoes.some(([v])=>v===valor?.[campo])?valor[campo]:'sem-preferencia';
  return {estilo:escolher('estilo',estilosGabinete),porte:escolher('porte',portesGabinete),cor:escolher('cor',coresSetup),
    gabinete_id:Number.isInteger(valor?.gabinete_id)&&valor.gabinete_id>0&&valor.gabinete_id<=1000000000?valor.gabinete_id:null};
}
function referencias(campo,titulo,opcoes,atual) {
  return '<fieldset class="appearance-references appearance-references--'+campo+'" aria-describedby="appearance-'+campo+'-help"><legend class="font-1-xs">'+titulo+'</legend>'
    +'<p class="font-2-xs appearance-section-help" id="appearance-'+campo+'-help">'+(campo==='size'?'O tamanho indica o espaço geral do gabinete. Os formatos abaixo são comuns, não uma garantia de encaixe.':'Escolha onde prefere os painéis de vidro. O estilo não define o tamanho nem quantas peças cabem.')+'</p>'
    +'<label class="appearance-no-preference"><input type="radio" name="appearance-'+campo+'" value="sem-preferencia" '+(atual==='sem-preferencia'?'checked':'')+'> Sem preferência</label>'
    +'<div class="appearance-cases">'+opcoes.filter(([v])=>v!=='sem-preferencia'&&v!=='compacto').map(([v,n])=>{
      const foto=exemplos[v],id='appearance-'+campo+'-'+v;
      return '<label class="appearance-case"><input type="radio" name="appearance-'+campo+'" value="'+v+'" aria-labelledby="'+id+'-name" aria-describedby="'+id+'-description" '+(v===atual?'checked':'')+'><span class="appearance-case-media">'+imagemPeca({...foto,categoria:'gabinete'},'appearance-case-image')+'</span><span class="appearance-case-name" id="'+id+'-name">'+h(n)+'</span><span class="appearance-case-description" id="'+id+'-description">'+h(foto.descricao)+'</span></label>';
    }).join('')+'</div>'+(campo==='size'?'<p class="sr-only" id="appearance-size-feedback" role="status"></p><div class="appearance-size-guide" id="appearance-size-guide" data-porte="'+atual+'">'+guiaPorteGabineteHtml(atual)+'</div>':'')+'</fieldset>';
}
export function aparenciaHtml(valor,_catalogo=[],{possuiGabinete=false}={}) {
  const atual=normalizarAparencia(valor);
  if(atual.estilo==='compacto')atual.estilo='sem-preferencia';
  return '<fieldset class="appearance-colors"><legend class="font-1-xs">Cor das peças e periféricos</legend><div class="appearance-swatches">'+coresSetup.map(([v,n])=>
    '<label class="appearance-swatch"><input type="radio" name="appearance-color" value="'+v+'" '+(v===atual.cor?'checked':'')+'><span class="appearance-color-dot color-'+v+'" aria-hidden="true"></span><span>'+n+'</span></label>').join('')+'</div><p class="font-2-xs appearance-price-help">Peças brancas podem custar mais ou ter menos opções disponíveis que as pretas. O preço depende do modelo e da loja.</p></fieldset>'
    +(possuiGabinete?'<p class="font-2-xs">O gabinete que você já possui será preservado.</p>':
      '<div class="appearance-examples" role="region" aria-label="Tamanho e estilo do gabinete" tabindex="0">'
      +referencias('size','Tamanho do gabinete',portesGabinete,atual.porte)
      +referencias('style','Estilo do gabinete',estilosGabinete,atual.estilo)
      +'<p class="font-2-xs appearance-fan-help">Uma ventoinha comum mede 120 ou 140 mm. Um water cooler de 240 mm costuma usar 2 ventoinhas de 120 mm; um de 360 mm, 3. O radiador completo, os tubos e as conexões precisam de espaço extra.</p></div>')
    +'<p class="font-2-xs planning-help">A cor é uma preferência para todas as peças e periféricos novos, incluindo gabinete e ventoinhas. Vamos buscar opções da cor escolhida quando ela estiver cadastrada ou indicada no nome do modelo, sem passar do orçamento ou prejudicar a montagem. As peças que você já possui serão mantidas. As fotos são apenas exemplos.</p>';
}
