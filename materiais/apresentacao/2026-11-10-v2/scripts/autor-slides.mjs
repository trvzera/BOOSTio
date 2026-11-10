import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
const ROOT='/Users/trvzera/Desktop/BOOSTio';
const DIR=ROOT+'/materiais/apresentacao/2026-11-10-v2';
const OUT=ROOT+'/materiais/exportacoes/apresentacao/2026-11-10-v2';
const C={black:'#000000',dark:'#0C0E10',blue:'#007BFF',white:'#FFFFFF',gray:'#A1A1A6',line:'#34383E'};
const TEAM=['Arthur Ferreira Raymundo','Gustavo Azevedo Oliveira','Gustavo Lopes Horta','Giovanni de Castro Morais Trivellato','Kayky Luiz Ferreira de Paula da Silva'];
export async function build(p){
 const require=createRequire('/Users/trvzera/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/package.json');
 const {FontLibrary}=require('skia-canvas');
 FontLibrary.use('Lexend','/Users/trvzera/Library/Fonts/Lexend-VariableFont_wght.ttf');
 FontLibrary.use('Poppins',OUT+'/fonts/Poppins-Regular.ttf');
 const logoBytes=new Uint8Array(await fs.readFile(ROOT+'/materiais/brand/LOGO1V2-PNG_00000.png'));
 p.slides.keep([]);p.theme.defaultFont='Poppins';
 const notes=[],media=[];
 function text(s,txt,x,y,w,h,size=30,color=C.white,{bold=false,font='Poppins',name}={}){
  const a=s.shapes.add({geometry:'textbox',name:name||txt.slice(0,50),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  a.text=txt;a.text.style={typeface:font,fontSize:size,color,bold,insets:0,autoFit:'none',wrap:'square',alignment:'left',verticalAlignment:'top'};return a;
 }
 function rect(s,x,y,w,h,fill=C.dark,line=C.line,name='') {return s.shapes.add({geometry:'rect',name,position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width:1.4}});}
 function path(s,pts,{col=C.blue,dash=false,width=2}={}) {return s.shapes.add({geometry:'custom',position:{left:0,top:0,width:1600,height:900},fill:'none',line:{fill:col,width,style:dash?'dashed':'solid'},customPaths:[{width:1600,height:900,commands:pts.map(([x,y],i)=>i?{lineTo:{x,y}}:{moveTo:{x,y}})}]});}
 function arrow(s,pts){path(s,pts);const [x,y]=pts.at(-1),[a,b]=pts.at(-2);let tri;if(x>a)tri=[[x-11,y-7],[x,y],[x-11,y+7]];else if(x<a)tri=[[x+11,y-7],[x,y],[x+11,y+7]];else if(y>b)tri=[[x-7,y-11],[x,y],[x+7,y-11]];else tri=[[x-7,y+11],[x,y],[x+7,y+11]];path(s,tri);}
 function logo(s,x,y,w){s.images.add({blob:logoBytes,contentType:'image/png',crop:{left:.21,top:.438,right:.15,bottom:.435},fit:'contain',position:{left:x,top:y,width:w,height:w/5.04},alt:'Logo oficial BOOSTio'});}
 function slide(title,time,presenter,speech,technical='',{bg=C.black}={}){
  const s=p.slides.add({width:1600,height:900});s.background.fill=bg;
  const number=p.slides.items.length;
  if(title)text(s,title,80,61,1440,96,54,C.white,{font:'Lexend',bold:true});
  text(s,'BOOSTio  /  3A2',80,849,650,27,20,bg===C.blue?C.white:C.gray);
  text(s,String(number).padStart(2,'0')+' / 17',1415,849,105,27,20,bg===C.blue?C.white:C.gray);
  s.speakerNotes.text=`SLIDE ${number} • ${time}s • ${presenter}\n\nFALA\n${speech}\n\nNOTAS TÉCNICAS E FONTES\n${technical}`;
  notes.push({slide:number,title:title|| (number===1?'BOOSTio':'Encerramento'),tempo:time,apresentador:presenter,fala:speech,notas_tecnicas:technical});return s;
 }
 function slot(s,file,x,y,w,h,seconds,desc){
  rect(s,x,y,w,h,C.dark,C.line,'MIDIA_'+file.replace(/\W/g,'_'));
  text(s,'VÍDEO A INSERIR',x+35,y+40,w-70,40,25,C.blue,{bold:true});
  text(s,desc,x+35,y+h*.36,w-70,110,36,C.white,{font:'Lexend'});
  text(s,file,x+35,y+h-110,w-70,40,25,C.gray);
  text(s,seconds,x+35,y+h-66,w-70,35,22,C.gray);
  media.push({slide:p.slides.items.length,arquivo:file,tempo:seconds,conteudo:desc,area:{x,y,largura:w,altura:h},proporcao:'16:9',objeto:'MIDIA_'+file.replace(/\W/g,'_')});
 }
 function box(s,title,body,x,y,w,h,{size=27}={}){rect(s,x,y,w,h,C.dark,C.line);text(s,title,x+22,y+18,w-44,47,29,C.blue,{font:'Lexend',bold:true});text(s,body,x+22,y+79,w-44,h-89,size);}
 function cls(s,title,body,x,y,w,h){rect(s,x,y,w,h,C.black,C.line);path(s,[[x,y+59],[x+w,y+59]],{col:C.line,width:1});text(s,title,x+18,y+13,w-36,40,28,C.blue,{font:'Lexend',bold:true});text(s,body,x+18,y+73,w-36,h-82,25);}

 let s=slide('',20,TEAM[0],
  'Boa tarde! Somos Arthur, Gustavo Azevedo, Gustavo Horta, Giovanni e Kayky, da turma 3A2. A BOOSTio ajuda quem vai montar ou melhorar um computador a escolher as peças de acordo com o uso, o orçamento e o que já possui.',
  'Os nomes completos estão no slide e não precisam ser lidos. Fonte: README.md, apresentação do projeto. Data do pitch: 10/11/2026.');
 logo(s,80,73,435);text(s,'Planejamento de PCs\npor objetivo e orçamento',80,260,1440,190,69,C.white,{font:'Lexend',bold:true});
 text(s,'Colégio Cotemig  ·  Turma 3A2',80,500,1400,45,31,C.blue);
 text(s,TEAM.slice(0,3).join('\n'),80,623,690,154,26);
 text(s,TEAM.slice(3).join('\n'),810,623,710,154,26);

 s=slide('O diferencial da BOOSTio',15,TEAM[0],
  'Quem monta o primeiro PC precisa decidir onde investir e quais peças combinam. A plataforma reúne sugestão por uso e orçamento, reaproveitamento de peças, diagnóstico e comparação. Nosso público inclui estudantes, jogadores e profissionais.',
  'Recursos da plataforma, sem alegação de exclusividade. Fontes: README.md, RF03, RF04, RF06, RF07 e RF13.');
 text(s,'Primeiro PC\nou upgrade',80,240,390,160,49,C.white,{font:'Lexend',bold:true});
 text(s,'Para estudar, jogar\nou trabalhar',80,466,360,100,28,C.gray);
 const rows=['Escolha por uso e orçamento','Reaproveitamento de peças','Montagem com diagnóstico','Comparação antes da decisão'];
 rows.forEach((t,i)=>{text(s,String(i+1).padStart(2,'0'),560,239+i*130,88,60,37,C.blue,{font:'Lexend'});text(s,t,670,237+i*130,850,76,39);});

 const cases=[
  ['Montagem inteligente','RF04','Necessidades\ne orçamento','Uma sugestão de configuração','03-rf04-formulario.mp4','Últimas respostas → build gerada','O formulário transforma uso, orçamento e peças já possuídas em uma sugestão de configuração.','README.md: RF04; frontend/pages/formulario.html; backend/services/build_service/gerar_build_service.py. Usar gravação real; não há vídeo incorporado.'],
  ['Compatibilidade e consumo','RF13','Conflitos\ne consumo','Diagnóstico com base nos dados disponíveis','04-rf13-compatibilidade.mp4','Editor → regra aplicada → consumo','O diagnóstico mostra conflitos e consumo estimado. Dados insuficientes deixam a verificação pendente.','README.md: RF13; frontend/js/build/compatibilidade.js; backend/services/validacoes_service/avaliar_compatibilidade_service.py. Consumo é estimativa.'],
  ['Comparação de builds','RF07','Duas builds,\nlado a lado','Diferenças de peças, preço e consumo','05-rf07-comparacao.mp4','Comparação entre duas configurações','Duas builds lado a lado mostram diferenças de peças, preço e consumo estimado.','README.md: RF07; frontend/js/build/comparacao.js. Cálculo básico ocorre no navegador com dados carregados pela API. Preços dependem da última consulta e não incluem frete.'],
  ['Compartilhamento de configurações','RF08','Link público,\noriginal protegida','Consulta sem alterar a configuração','06-rf08-compartilhamento.mp4','Link público → visualização sem login','O link público permite consultar sem login. Só o proprietário pode alterar a configuração original.','README.md: RF08; backend/services/build_service/buscar_build_publica_service.py; frontend/js/build/compartilhamento.js. A demonstração completa deve evidenciar controle de acesso.'],
  ['Configurações prontas','RF10','Um ponto\nde partida','Modelos para filtrar e personalizar','07-rf10-prontas.mp4','Filtro → configuração pronta','Os modelos prontos são pontos de partida para escolher e personalizar conforme a necessidade.','README.md: RF10; frontend/pages/configuracoes-prontas.html; frontend/js/build/modelos.js. Não contar abertura/listagem como uma das quatro funções não CRUD.']
 ];
 for(const [title,rf,goal,desc,file,scene,speech,source]of cases){
  s=slide(title,8,TEAM[0],speech,source+' Trecho silencioso de 6 a 8 segundos; inserir no mesmo bloco de 8s, sem aumentar a duração.');
  text(s,rf,80,208,350,55,36,C.blue,{font:'Lexend',bold:true});
  text(s,goal,80,327,355,170,43,C.white,{font:'Lexend',bold:true});text(s,desc,80,580,350,150,28,C.gray);
  slot(s,file,500,208,1020,574,'6–8 segundos · sem áudio',scene);
 }

 s=slide('Modelo de domínio',30,TEAM[1],
  'Este é um recorte do domínio revisado no código. Usuario possui configurações. Build referencia modelos do catálogo, como Processador, que herda de Peca. BuildSalva guarda o estado em JSON e pode existir sem uma Build original. Ofertas concentram preço e disponibilidade; a referência à peça usa categoria e ID. O conteúdo JSON não cria relações SQL com cada componente.',
  'Fontes: backend/models/{usuario,build,build_salva,peca,processador,oferta,preco_oferta}.py. Diagrama docs/diagrama-classes.png revisado: preço, disponibilidade e data de preço são derivados das ofertas; não são apresentados como colunas físicas de Peca neste recorte. Todas as entidades do recorte herdam de ModeloBase, diretamente ou via Peca; a base e outros componentes foram omitidos para leitura. Usuario–Build e Usuario–BuildSalva: 1 para 0..*. Build original–BuildSalva: 0..1 em ambos os lados. Build–Processador: 0..* para 1. Peca é abstrata, e Oferta usa referência lógica tabela_peca+peca_id sem FK para uma tabela Peca. Limite de negócio de três configurações salvas por conta. Sem composição.');
 text(s,'Recorte revisado a partir das Models',80,161,1400,40,27,C.gray);
 cls(s,'Usuario','nome, email, budget\nbuscar_por_email()',80,241,360,169);
 cls(s,'Build','usuario_id, nome\nquantidade_ram\ncriar_gerada()',610,241,380,209);
 cls(s,'Peca «abstract»','fabricante, modelo\nconsumo_energia\nto_catalogo()',1160,241,360,209);
 cls(s,'BuildSalva','usuario_id\nbuild_original_id [0..1]\nestado: JSON\ncriar_limitada()',80,564,390,244);
 cls(s,'Processador','soquete, nucleo, thread',610,614,380,150);
 cls(s,'Oferta','tabela_peca, peca_id\nloja, preco, ativa\npreco_atualizado_em',1160,564,360,244);
 path(s,[[440,325],[610,325]]);text(s,'1',456,284,40,31,24);text(s,'0..*',542,284,65,31,24);
 path(s,[[260,410],[260,564]]);text(s,'1',280,432,50,31,24);text(s,'0..*',280,517,70,31,24);
 path(s,[[470,650],[530,650],[530,420],[610,420]]);text(s,'original\n0..1 / 0..1',544,480,215,68,22,C.gray);
 path(s,[[800,450],[800,614]]);text(s,'0..* builds',819,465,180,31,23);text(s,'1 processador',819,572,190,31,23);
 path(s,[[990,657],[1060,657],[1060,336],[1142,336]]);
 s.shapes.add({geometry:'custom',position:{left:1142,top:325,width:18,height:22},fill:C.black,line:{fill:C.blue,width:2},customPaths:[{width:18,height:22,commands:[{moveTo:{x:0,y:0}},{lineTo:{x:18,y:11}},{lineTo:{x:0,y:22}},{close:{}}]}]});
 text(s,'herança',1004,283,142,34,22,C.gray);
 path(s,[[990,733],[1160,733]],{dash:true});text(s,'1',1006,690,30,30,22);text(s,'0..*',1095,690,65,30,22);text(s,'referência\nlógica',1005,751,150,59,20,C.gray);
 text(s,'BuildSalva: componentes e quantidades ficam no JSON',80,814,1390,32,23,C.blue);

 s=slide('Recuperação de dados',25,TEAM[1],
  'A consulta do histórico começa com categoria e ID da peça. O Controller chama o Service, que procura a oferta ativa no Repository. Este consulta Oferta via SQLAlchemy e banco. O Service também lê o histórico diretamente na Model. O Controller devolve JSON.',
  'Fluxo real: GET /build/catalogo/<categoria>/<peca_id>/historico-precos → historico_precos_peca() → ConsultarHistoricoPrecosService.executar() → repositories.ofertas_kabum_repository.buscar_ativa() → Oferta.query → banco. O mesmo Service também chama HistoricoOferta.listar(oferta.id) diretamente, fora do Repository. Fontes: backend/controllers/build_controller.py; backend/services/peca_service/consultar_historico_precos_service.py; backend/repositories/ofertas_kabum_repository.py. O Controller é função de módulo, não uma classe BuildController. Respostas: 200; entrada inválida 400, peça ausente 404, falha SQL 503.');
 text(s,'GET /build/catalogo/{categoria}/{id}/historico-precos',80,163,1440,47,29,C.blue);
 box(s,'Frontend','Categoria e ID da peça\nRequisição HTTP',80,254,400,174);
 box(s,'Controller','historico_precos_peca()\nEncaminha a consulta',600,254,400,174);
 box(s,'Service','ConsultarHistorico-\nPrecosService.executar()',1120,254,400,174,{size:25});
 box(s,'Banco','Consulta SQL gerada\npor SQLAlchemy',80,566,400,174);
 box(s,'Model','Oferta.query\nMapeamento da entidade',600,566,400,174);
 box(s,'Repository','buscar_ativa(peca)\nFiltra a oferta da peça',1120,566,400,174);
 arrow(s,[[480,340],[600,340]]);arrow(s,[[1000,340],[1120,340]]);arrow(s,[[1320,428],[1320,566]]);arrow(s,[[1120,650],[1000,650]]);arrow(s,[[600,650],[480,650]]);
 text(s,'Retorno: oferta → histórico → JSON → frontend',80,773,1430,39,28,C.white);
 text(s,'HistoricoOferta.listar() é chamado diretamente pelo Service',80,812,1430,31,22,C.gray);

 s=slide('Entrada de dados',25,TEAM[1],
  'Na criação manual, o frontend envia o estado da configuração. criar_build_manual chama o Service, que valida o JSON e aplica o orçamento. BuildSalva verifica e-mail e limite da conta, persiste e confirma a transação. O Controller retorna 201. Entrada inválida retorna 400; limite, 409; falha de banco faz rollback. Neste fluxo, a gravação ainda não passa por Repository.',
  'Fluxo real: POST /build/manual → criar_build_manual() → CriarBuildManualService.executar() → validar_estado() → BuildSalva.criar_limitada() → db.session.add/commit. Sem Repository na escrita deste caso de uso. Não inserir uma etapa fictícia. Falhas: 400 ValueError, 403 e-mail não verificado via handler, 409 LimiteBuildsError via handler, 500 SQLAlchemyError com rollback. Fontes: backend/controllers/build_controller.py; backend/services/build_service/criar_build_manual_service.py; backend/services/validacoes_service/validar_estado_build_service.py; backend/models/build_salva.py. Adequação pendente à exigência de Repository neste fluxo de escrita.');
 text(s,'POST /build/manual',80,163,1440,47,29,C.blue);
 box(s,'Frontend','Estado da configuração\nCorpo JSON',80,254,400,174);
 box(s,'Controller','criar_build_manual()\nLê a entrada HTTP',600,254,400,174);
 box(s,'Service','CriarBuildManualService\nvalidar_estado()',1120,254,400,174,{size:25});
 box(s,'Banco','INSERT / COMMIT\nPersistência via ORM',80,566,400,174);
 box(s,'Model','BuildSalva.criar_limitada()\nVerificação e limite: 3',600,566,400,174,{size:24});
 arrow(s,[[480,340],[600,340]]);arrow(s,[[1000,340],[1120,340]]);arrow(s,[[1320,428],[1320,496],[800,496],[800,566]]);arrow(s,[[600,650],[480,650]]);
 text(s,'400  Entrada inválida\n409  Limite atingido\n500  Falha + rollback',1120,580,400,153,27,C.gray);
 text(s,'Retorno: 201 + JSON da configuração',80,773,1430,39,28,C.white);
 text(s,'A gravação deste caso de uso acessa a Model diretamente',80,812,1430,31,22,C.gray);

 s=slide('Arquitetura e organização',25,TEAM[2],
  'O frontend tem páginas, estilos e módulos de consumo da API. No backend, funções em Controllers recebem HTTP; Services executam as regras; Repositories concentram consultas específicas, como a oferta ativa. Models representam os dados e ainda executam parte do CRUD. Por isso, a estrutura existe, mas nem todos os fluxos usam Repository.',
  'Fontes: árvore real frontend/ e backend/; controllers/build_controller.py; services/peca_service/consultar_historico_precos_service.py; repositories/ofertas_kabum_repository.py; models/base.py. O README descreve Controllers como classes, mas o Controller de build atual contém funções de módulo. Não repetir essa descrição desatualizada. A escrita de BuildSalva e a leitura de HistoricoOferta continuam nas Models.');
 text(s,'frontend/',80,225,470,65,46,C.blue,{font:'Lexend',bold:true});
 text(s,'pages/\nstyles/\njs/api/',80,340,430,203,37);text(s,'Interface e requisições HTTP',80,655,470,89,28,C.gray);
 text(s,'backend/',635,225,885,65,46,C.blue,{font:'Lexend',bold:true});
 const dirs=[['controllers/','Entrada e resposta HTTP'],['services/','Casos de uso e validações'],['repositories/','Consultas específicas'],['models/','Entidades, ORM e parte do CRUD']];
 dirs.forEach(([d,b],i)=>{text(s,d,635,337+i*107,335,57,32,C.white,{font:'Lexend'});text(s,b,990,341+i*107,530,71,28,C.gray);});

 s=slide('Frontend e API separados',30,TEAM[2],
  'A interface está em boostio.com.br e a API em outro domínio, api.boostio.com.br. O navegador envia HTTP e recebe JSON. Nesta checagem, o health respondeu 200 com status ok e permitiu a origem do frontend. O vídeo de Network deve mostrar também uma ação de negócio, o status e a resposta, com cookies e tokens ocultos.',
  'Evidência real de 09/11/2026: GET https://api.boostio.com.br/health → HTTP 200, Content-Type application/json, corpo {"status":"ok"}; Access-Control-Allow-Origin: https://boostio.com.br e credenciais permitidas. GET do health não comprova sozinho o funcionamento de todos os endpoints de negócio. HTTPS do site também respondeu 200. Arquivos: referencias/api-health.json; compose.yaml; frontend/js/api/_shared/fetchComErro.js. Inserir gravação real de Network, sem abrir headers sensíveis.');
 text(s,'boostio.com.br',80,212,1430,57,42,C.blue,{font:'Lexend',bold:true});
 text(s,'Interface no navegador',80,281,565,45,29,C.gray);
 text(s,'api.boostio.com.br',80,388,565,55,39,C.white,{font:'Lexend'});
 text(s,'GET /health  →  200',80,485,565,48,31,C.blue,{bold:true});
 text(s,'{"status":"ok"}',80,558,565,55,36);
 text(s,'Resposta real · 09/11/2026',80,642,565,80,25,C.gray);
 slot(s,'12-rede-api.mp4',690,300,830,467,'8–12 segundos · durante a fala','Network: ação → status → JSON');

 s=slide('Demonstração funcional',110,TEAM[3],
  '00:00–00:35 — Aqui confirmamos as últimas respostas do formulário e enviamos a solicitação. A configuração retornada considera o objetivo, o orçamento e as peças informadas. [Mostrar o resultado real.]\n\n00:35–01:00 — Agora o editor aplica uma regra a componentes com dados conhecidos. [Apontar o motivo exibido.] O consumo é uma estimativa; verificações sem dados ficam pendentes.\n\n01:00–01:25 — Na comparação, estas duas builds diferem em [peça, preço ou consumo observado]. [Apontar a diferença real, sem decorar um valor inventado.]\n\n01:25–01:50 — Tornamos esta build pública e copiamos o link. Abrindo sem login, a configuração fica disponível para consulta, sem alterar a original. [Mostrar os controles de edição ausentes/bloqueados. Se couber, tornar privada e mostrar o bloqueio de acesso.]',
  'Vídeo ainda não fornecido; este slide contém uma área editável, sem gravação simulada. Vídeo final: 110 segundos, RF04 35s + RF13 25s + RF07 25s + RF08 25s. Pode cortar espera de rede preservando a execução e os resultados reais. Preferir MP4 H.264 1920×1080. No PowerPoint, inserir dentro da área e definir início automático, sem repetir; avanço manual ao término. Manter a duração total deste slide em 110s. Desativar áudio se o apresentador narrar. Gravar com conta de demonstração verificada e espaço livre (máximo 3 builds). Não usar cadastro/listagem/edição isolada como as quatro funções. FPS e integrações não homologadas ficam fora deste bloco.');
 slot(s,'13-demonstracao-1m50.mp4',224,169,1152,648,'1min50 · execução real do sistema','RF04 → RF13 → RF07 → RF08');

 s=slide('Persistência com ORM',17,TEAM[4],
  'O SQLAlchemy persiste as entidades pela sessão. Em SQLite temporário, conferimos criação, leitura, atualização e exclusão com o código real. A oferta 12 foi alterada e removida. São dados de demonstração, sem acessar a produção.',
  'Código literal de backend/models/base.py. Evidência executada em 09/11/2026: scripts/conferir-evidencia.py, com Flask e Models reais em SQLite em memória. Resultado: oferta 12 consultada por 189.90; atualizada para 194.90; após exclusão, buscar_ativa retorna oferta 11. Arquivo referencias/evidencia-orm-repository.json. Não é comprovação de MySQL em produção nem cotação atual. Nenhuma credencial, conta ou registro de produção foi usado. A evidência textual no slide é real; o vídeo opcional ainda não foi fornecido.');
 text(s,'ModeloBase',80,214,660,52,38,C.blue,{font:'Lexend',bold:true});
 text(s,'def salvar(self):\n    db.session.add(self)\n    db.session.commit()\n\ndef deletar(self):\n    db.session.delete(self)\n    db.session.commit()',80,302,710,333,30);
 text(s,'CRUD conferido em SQLite temporário',860,214,660,84,35,C.white,{font:'Lexend'});
 text(s,'Criar + ler    oferta 12 · 189,90\nAtualizar      oferta 12 · 194,90\nExcluir         próxima ativa: 11',860,361,660,212,31);
 text(s,'Dados de demonstração\nExecução real em 09/11/2026',860,653,660,92,26,C.gray);

 s=slide('Consultas na camada Repository',18,TEAM[4],
  'buscar_ativa filtra categoria, peça, loja e estado ativo, escolhendo o maior ID. Nos dados de demonstração, retornou a oferta 12 e excluiu a inativa e a de outra categoria. A consulta ORM fica no Repository.',
  'Código literal, apenas quebrado em linhas para leitura: backend/repositories/ofertas_kabum_repository.py:buscar_ativa. Não é SQL escrito manualmente. SQL compilado pelo ORM e resultados completos em referencias/evidencia-orm-repository.json. Entrada: processador id7; oferta11 ativa199.90, 12 ativa189.90, 13 inativa99.90, 14 categoriaSSD49.90. Retorno12; critério maior ID ativo. SQLite isolado, sem loja ou rede. O parâmetro opcional bloquear usa populate_existing/with_for_update; não dizer que o teste SQLite comprova lock MySQL.');
 text(s,'buscar_ativa(peca)',80,218,970,52,38,C.blue,{font:'Lexend',bold:true});
 text(s,'consulta = Oferta.query.filter_by(\n    tabela_peca=peca.__tablename__,\n    peca_id=peca.id,\n    loja=LOJA, ativa=True)\nconsulta = consulta.order_by(Oferta.id.desc())\nreturn (consulta.populate_existing().with_for_update()\n        if bloquear else consulta).first()',80,309,1045,335,27);
 text(s,'Entrada',1190,220,330,45,30,C.gray);text(s,'processador\nID 7',1190,282,330,104,34,C.white,{font:'Lexend'});
 text(s,'Resultado real',1190,453,330,45,30,C.gray);text(s,'Oferta 12\nativa · KaBuM',1190,516,330,113,33,C.white,{font:'Lexend'});
 text(s,'Critério: maior ID ativo para a peça e a loja',80,723,1430,45,31,C.blue);
 text(s,'Consulta ORM existente · dados de demonstração em SQLite',80,786,1430,35,24,C.gray);

 s=slide('Tecnologias e documentação',25,TEAM[4],
  'A API usa Python, Flask e SQLAlchemy; o frontend, HTML, CSS e JavaScript. MySQL persiste os dados; Redis apoia os limites de requisição; Docker separa os serviços. O README documenta vinte requisitos e seus escopos. A hospedagem foi verificada; IA funcional e consentimento exigem suas próprias evidências.',
  'Fontes: README.md; requirements.txt; compose.yaml; backend/config.py. MySQL8.4 e Redis7 definidos no Compose, imagens separadas para API/frontend, além de proxy. A integração de geração por IA existe; só reivindicar bônus funcional depois da gravação real de RF04. Hospedagem HTTP verificada em 09/11/2026; autenticação e demais funções de produção não foram homologadas neste trabalho. Não foi localizado registro persistido de consentimento no fluxo criarUsuario; checkbox não comprova bônus. FPS e integrações ainda não homologadas devem ser tratados como desenvolvimento. Não ler os vinte RF em voz alta.');
 text(s,'Python · Flask · SQLAlchemy',80,223,1430,58,41,C.white,{font:'Lexend',bold:true});
 text(s,'HTML · CSS · JavaScript',80,297,1430,58,41,C.blue,{font:'Lexend',bold:true});
 text(s,'MySQL',80,449,505,48,35);text(s,'Persistência',80,506,505,45,28,C.gray);
 text(s,'Redis',80,584,505,48,35);text(s,'Limites de requisição',80,641,505,45,28,C.gray);
 text(s,'Docker',80,719,505,48,35);text(s,'Serviços separados',80,776,505,45,28,C.gray);
 slot(s,'16-readme.mp4',780,394,740,416,'6–8 segundos · durante a fala','README: 20 requisitos e seus escopos');

 s=slide('',10,TEAM[4],
  'A BOOSTio ajuda a planejar o próximo computador com escolhas compatíveis com o uso e o orçamento. Vocês podem conhecer o projeto em boostio.com.br. Obrigado!',
  'Encerrar sem abrir novas funções. Tempo total planejado: 390 segundos, incluindo vídeo de 110 segundos. Margem até o limite de 7min: 30 segundos.');
 logo(s,80,75,420);text(s,'Planeje seu\npróximo computador',80,286,1420,204,78,C.white,{font:'Lexend',bold:true});
 text(s,'boostio.com.br',80,582,1420,84,59,C.blue,{font:'Lexend',bold:true});
 text(s,'Obrigado!',80,744,1420,55,36,C.white);
 await fs.writeFile(DIR+'/roteiros/notas-slides.json',JSON.stringify(notes,null,2));
 await fs.writeFile(DIR+'/midias/manifesto.json',JSON.stringify(media,null,2));
 return {slides:p.slides.items.length,tempoSegundos:notes.reduce((a,n)=>a+n.tempo,0),midiasAInserir:media.length};
}
