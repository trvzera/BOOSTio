const fs = require('fs');
const path = require('path');
const deps = '/Users/trvzera/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const { instance } = require(path.join(deps, '@viz-js/viz'));
const sharp = require(path.join(deps, 'sharp'));
const out = __dirname;
const classes = [
  ['ModeloBase','base',true,['id: Integer','criado_em: DateTime','atualizado_em: DateTime'],['salvar()','deletar()']],
  ['Peca','base',true,['fabricante','modelo','part_number','consumo_energia','preco','preco_atualizado_em','esgotado','imagem_url','kabum_external'],['buscar_por_id()','mostrar_pecas()','atualizar_preco()','to_catalogo()']],
  ['Periferico','base',true,['conexao','iluminacao'],[]],
  ['Usuario','conta',false,['nome','email','senha','verificado','ativo','login_google','google_sub','versao_sessao','budget','usar_budget'],['buscar_por_email()','atualizar_dados()','atualizar_budget()','desativar()']],
  ['Codigo','conta',false,['usuario_id','codigo','email_destino','tentativas','data_expiracao','usado'],[]],
  ['TokenRecuperacao','conta',false,['usuario_id','token_hash','email_destino','versao_sessao','data_expiracao','usado'],[]],
  ['Build','configuracoes',false,['usuario_id','nome','quantidade_ram','quantidade_ssd','quantidade_hd','quantidade_fan'],['criar_gerada()','quantidade_de()','listar_por_usuario()','to_dict()']],
  ['BuildSalva','configuracoes',false,['usuario_id','build_original_id: Integer [0..1, único]','estado: JSON','LIMITE = 3'],['verificar_espaco()','criar_limitada()','listar_por_usuario()','buscar()','buscar_publica()','validar_estado()']],
  ['Processador','componentes',false,['soquete','nucleo','thread','clockbase','clockmax','videointegrado','cooler'],[]],
  ['PlacaMae','componentes',false,['socket','chipset','formato','tipo_memoria','quantidade_slots_ram','memoria_maxima_gb','quantidade_slots_m2'],[]],
  ['MemoriaRAM','componentes',false,['capacidade_gb','ddr','frequencia_mhz','quantidade_pentes'],[]],
  ['PlacaVideo','componentes',false,['memoria_gb','tipo_memoria','consumo_w','quantidade_fans'],[]],
  ['SSD','componentes',false,['capacidade_gb','tipo','interface','formato'],[]],
  ['HD','componentes',false,['capacidade_gb','velocidade_rpm','interface'],[]],
  ['Fonte','componentes',false,['potencia_w','formato'],[]],
  ['Gabinete','componentes',false,['formato','formatos_placa_mae','fans_inclusos','tamanho_max_gpu_mm','tamanho_max_cooler_mm'],[]],
  ['AirCooler','componentes',false,['compatibilidade','dimensoes'],[]],
  ['WaterCooler','componentes',false,['compatibilidade','tamanho_radiador_mm','quantidade_fans'],[]],
  ['Fan','componentes',false,['tamanho_mm','quantidade','iluminacao'],[]],
  ['PlacaRede','componentes',false,['interface','padrao_wifi','velocidade_mbps','bluetooth'],[]],
  ['CaboRede','componentes',false,['categoria','comprimento_m','conector'],[]],
  ['Monitor','perifericos',false,['tamanho_polegadas','resolucao','taxa_atualizacao_hz'],[]],
  ['Teclado','perifericos',false,['layout','switch','mecanico'],[]],
  ['Mouse','perifericos',false,['dpi_max','botoes','sensor'],[]],
  ['Fone','perifericos',false,['tipo','microfone','cancelamento_ruido'],[]],
];
const components=classes.filter(c=>c[1]==='componentes').map(c=>c[0]);
const peripherals=classes.filter(c=>c[1]==='perifericos').map(c=>c[0]);
const inheritance=[
  ...['Peca','Usuario','Codigo','TokenRecuperacao','Build','BuildSalva'].map(c=>({child:c,parent:'ModeloBase'})),
  {child:'Periferico',parent:'Peca'},
  ...components.map(c=>({child:c,parent:'Peca'})),
  ...peripherals.map(c=>({child:c,parent:'Periferico'})),
];
const mandatory=new Set(['Processador','PlacaMae','MemoriaRAM','Fonte','Gabinete']);
const associations=[
  {a:'Usuario',b:'Build',ma:'1',mb:'0..*'},
  {a:'Usuario',b:'BuildSalva',ma:'1',mb:'0..*'},
  {a:'Usuario',b:'Codigo',ma:'1',mb:'0..*'},
  {a:'Usuario',b:'TokenRecuperacao',ma:'1',mb:'0..*'},
  {a:'BuildSalva',b:'Build',ma:'0..1',mb:'0..1',label:'original'},
  ...[...components,...peripherals].map(c=>({a:'Build',b:c,ma:'0..*',mb:mandatory.has(c)?'1':'0..1'})),
];
const notes=[
  ['nota_estado','estado armazena título, descrição, visibilidade, tranca, orçamento, componentes e quantidades; são dados JSON, não colunas individuais. Pode existir sem uma Build original.','BuildSalva'],
  ['nota_limite','limite de negócio: três configurações salvas por conta','BuildSalva'],
  ['nota_quantidades','Em Build, quantidades representam unidades do modelo referenciado. Em BuildSalva, o JSON também permite múltiplos modelos de RAM, armazenamento e fans.','Build'],
];
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function table(c){
 const [name,area,abstract,attrs,methods]=c;
 const rows=[];
 if(abstract)rows.push('<TR><TD BGCOLOR="#EFF6FF"><FONT COLOR="#0056B3" POINT-SIZE="12">«abstract»</FONT></TD></TR>');
 rows.push(`<TR><TD PORT="title" BGCOLOR="#EFF6FF" CELLPADDING="10"><FONT COLOR="#0056B3" POINT-SIZE="19"><B>${abstract?'<I>':''}${esc(name)}${abstract?'</I>':''}</B></FONT></TD></TR>`);
 rows.push('<TR><TD ALIGN="LEFT" BALIGN="LEFT" CELLPADDING="9"><FONT POINT-SIZE="14">'+attrs.map(a=>a==='LIMITE = 3'?'<U>'+a+'</U>':esc(a)).join('<BR ALIGN="LEFT"/>')+'<BR ALIGN="LEFT"/></FONT></TD></TR>');
 if(methods.length)rows.push('<TR><TD ALIGN="LEFT" BALIGN="LEFT" CELLPADDING="9"><FONT POINT-SIZE="14">'+methods.map(esc).join('<BR ALIGN="LEFT"/>')+'<BR ALIGN="LEFT"/></FONT></TD></TR>');
 return '<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" COLOR="#77869B" BGCOLOR="white" RULES="ROWS">'+rows.join('')+'</TABLE>';
}
const wrap=(text,n=47)=>{const lines=[];let line='';for(const word of text.split(' ')){if(line.length+word.length+1>n){lines.push(line);line=word;}else line+=(line?' ':'')+word;}if(line)lines.push(line);return lines;};
function makeDot(){
 const lines=['digraph BOOSTio {',
 'graph [rankdir=TB, newrank=true, bgcolor="white", pad="0.55", nodesep="0.42", ranksep="1.5 equally", splines=polyline, outputorder=edgesfirst, fontname="Arial", fontsize=30, fontcolor="#0056B3", labelloc=t, label="BOOSTio — Diagrama de classes do domínio\\n ", compound=true, ordering=out];',
 'node [shape=plain, fontname="Arial", margin=0];',
 'edge [fontname="Arial", fontsize=13, color="#718096", penwidth=1.15, arrowsize=0.85, labeldistance=1.7, labelangle=25];'];
 for(const c of classes)lines.push(`${c[0]} [label=<${table(c)}>];`);
 const groups=[['conta','CONTA',['Usuario','Codigo','TokenRecuperacao']],['configuracoes','CONFIGURAÇÕES',['Build','BuildSalva']],['componentes','COMPONENTES · herdam Peca',components],['perifericos','PERIFÉRICOS · herdam Periferico',peripherals]];
 for(const [id,title,names] of groups){lines.push(`subgraph cluster_${id} { label="${title}"; fontsize=19; fontcolor="#0056B3"; color="#D7E1EE"; penwidth=1; margin=24;`);for(const name of names)lines.push(name+';');if(id==='componentes'||id==='perifericos')lines.push('{ rank=same; '+names.join('; ')+'; }');lines.push('}');}
 for(const i of inheritance){const constraint=['Build','BuildSalva'].includes(i.child)?'false':'true';lines.push(`${i.parent} -> ${i.child} [dir=back, arrowtail=empty, arrowhead=none, color="#0056B3", penwidth=1.3, constraint=${constraint}];`);}
 for(const a of associations)lines.push(`${a.a} -> ${a.b} [dir=none, constraint=false, taillabel="${a.ma}", headlabel="${a.mb}"${a.label?',label="'+a.label+'"':''}];`);
 for(const [id,text,target] of notes){lines.push(`${id} [shape=note, color="#B8C8DD", fillcolor="#F8FAFD", style=filled, fontname="Arial", fontsize=14, margin="0.18", label="${wrap(text).map(esc).join('\\l')}\\l"];`);lines.push(`${target} -> ${id} [dir=none, style=dashed, color="#A6B3C4", constraint=false];`);}
 lines.push('{rank=same; Build; BuildSalva; nota_estado; nota_limite; nota_quantidades;}');
 lines.push('Periferico -> Build [style=invis, weight=15, minlen=2];');
 lines.push('Monitor -> Build [style=invis, weight=1];');
 lines.push('Usuario -> Build [style=invis, weight=1];');
 lines.push('}');return lines.join('\n');
}
(async()=>{
 const viz=await instance();const dot=makeDot();
 fs.writeFileSync(path.join(out,'boostio-dominio.dot'),dot);
 const result=viz.render(dot,{format:'svg',engine:'dot'});
 if(result.status!=='success')throw new Error(JSON.stringify(result.errors));
 fs.writeFileSync(path.join(out,'boostio-dominio.svg'),result.output);
 fs.writeFileSync(path.join(out,'modelo-dominio.json'),JSON.stringify({classes,inheritance,associations,notes},null,2));
 const metadata=await sharp(Buffer.from(result.output)).metadata();
 await sharp(Buffer.from(result.output)).resize({width:Math.min(14000,Math.round(metadata.width*1.5))}).png().toFile(path.join(out,'boostio-dominio.png'));
 await sharp(Buffer.from(result.output)).resize({width:2200}).png().toFile(path.join(out,'previa.png'));
 console.log(JSON.stringify({classes:classes.length,inheritance:inheritance.length,associations:associations.length,metadata,warnings:result.errors},null,2));
})();
