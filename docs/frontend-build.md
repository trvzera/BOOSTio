# Editor de build e efeitos de scroll

Após a integração da `main` em 20/10/2026, as montagens da conta usam
`pages/builds-conta.js`, `/build/` e `/build/catalogo`; `builds.js` foi substituído.
O texto abaixo também documenta modos legados e etapas anteriores. O estado atual
dos requisitos está no README; a revisão de acessibilidade/performance está em
[qualidade-frontend.md](qualidade-frontend.md).

### Entrega acadêmica: Controllers em classes — 23/10/2026

- Sete classes por recurso, com métodos estáticos: Auth, Usuario, Build, Email,
  Benchmark, Saude e Peca. Blueprints, nomes de endpoint, URLs, autorização, CSRF
  e limites foram preservados. O blueprint antigo de peças continua não registrado
  no app; seu Service agora usa os nomes reais de Models e o contrato de catálogo.
- `GerarBuildService` coordena trava/fallback sem mudar modelo, número de tentativas
  ou cota. `SolicitarRecuperacaoSenhaService` localiza/valida a conta para recuperação,
  preservando resposta genérica contra enumeração. Services de verificação resolvem
  o usuário; Controllers não consultam as Models de usuário diretamente.
- CRUD básico de peças usa `salvar()`/`buscar_por_id()` das Models. SQL especial
  de saúde e migração de links fica em Repositories, sem duplicar CRUD. A migração
  não foi executada no banco real; somente testes em bancos temporários.
- 615 testes Python (+13 subtestes) e 521 Node aprovados. Incluem identidade das
  sete classes, contrato de 34 rotas declaradas, recuperação, limites, fallback
  único, OAuth, CSRF, persistência e compartilhamento. Nenhuma chamada real à LLM,
  SMTP, coleta de preços/imagens ou mudança no banco do usuário nesta adaptação.

### Revisão em seis etapas — 23/10/2026

6. **Mensagens acessíveis:** regiões persistentes `status`/`alert`, com contexto
   completo e sem foco programático. Resumos de total/saldo e salvamento esperam
   700 ms de pausa e apenas a revisão mais recente confirma o salvamento; falhas
   usam o canal urgente. O aviso visual não duplica a região de anúncio. Dentro
   de modais, as regiões ficam no diálogo ativo, não atrás dele. Fechar/sair
   cancela mensagens pendentes. Porcentagem de periféricos e budget das melhorias
   também usam pausa; frases decorativas da geração não são lidas a cada troca.
   Salvar permite nova tentativa após falha, sem exigir mudar o nome.

   Referência: [WCAG — mensagens de status](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).
   Validação desta etapa: 520 testes Node, 583 Python (+13 subtestes), 83 verificações
   Chrome/axe de formulário/editor/status/desfazer em três larguras e nova rodada
   de 97 verificações do modal de melhorias em cinco viewports. Falhas e gravações
   simuladas, catálogo somente leitura; sem chamadas reais a LLM, SMTP ou lojas.
   Axe e observação do DOM não substituem homologação manual com VoiceOver/NVDA.

5. **Expansão SSD/HD:** a prévia permite aumentar/diminuir as unidades novas do
   modelo escolhido, sem remover os discos atuais. Quantidades entram no custo
   combinado e na validação M.2/SATA/portas compartilhadas; baias de 2,5/3,5 pol.
   conhecidas também limitam a proposta. O botão de aumentar explica o limite.
   Dados ausentes continuam pendentes, não viram espaço garantido. Substituir é
   explícito e mantém os critérios de não regressão. 514 testes Node e 97
   verificações Chrome/axe em celular, tablet, desktop e paisagem, com catálogo
   somente leitura e aplicação simulada.

4. **Desfazer:** histórico de um nível em memória no editor para remoção,
   quantidades, upgrades confirmados e opções de peças/periféricos/rede. Restaura
   só os campos de montagem; nome/orçamento atuais são preservados. Uma configuração
   local diferente, ID diferente ou tranca impede aplicar o snapshot. Undo aguarda
   a fila anterior e salva a restauração pela mesma fila. Falha não é anunciada como
   sucesso. O histórico é limpo ao sair/recarregar e não oferece redo. Não substitui
   controle de versão concorrente no servidor. 512 Node e 51 verificações Chrome/axe,
   incluindo duas gravações simuladas sequenciais por remoção/desfazer.

   Complemento de ciclo de vida: `pagehide` limpa o histórico e desabilita Desfazer,
   inclusive se a página for preservada pelo cache de navegação. 521 testes Node
   e 54 verificações Chrome/axe, incluindo saída/restauração simulada e revalidação
   da sessão em três larguras. Nenhuma gravação real em conta ou banco.

3. **Compra revalidada:** abrir Comprar build ou comprar uma peça consulta de novo
   `/build/catalogo` com `no-store`, sem reutilizar a promessa em memória. O fluxo
   público reconsulta a rota pública e a visibilidade. Links só aparecem após
   resposta válida; falha mostra retry sem usar cotações antigas. O resumo compara
   centavos × quantidades, total anterior/atual e diferença, sem simular diferença
   completa para itens sem preço. Peças sem estoque confirmado/preço não liberam
   compra. Fechar cancela a consulta; nenhuma build é alterada. Dados são o último
   registro do catálogo, não scraping em tempo real. Modo demo é explicitamente
   demonstrativo. 508 testes Node e 21 verificações Chrome/axe do fluxo.

2. **Motivos de exclusão:** o catálogo separa busca/marca sem resultado de peças
   bloqueadas pelas regras da build. Um painel nativo mostra categorias de causa,
   contagens e até três exemplos por causa (DDR, slots, estoque, conexões, espaço,
   dados ausentes e outros conflitos). Quando não sobra opção, o painel começa
   aberto. As mensagens reais são escapadas e os filtros continuam obrigatórios.
   504 testes Node passaram; o filtro não aprova medidas desconhecidas.

1. **Fichas técnicas:** seis fichas novas e um alias adicional, abrangendo oito
   anúncios de placas-mãe. Corrigidas MSI 940305 (DDR4) e ASRock 587807 (DDR5).
   Slots, máximos, conexões e dimensões foram complementados só quando confirmados.
   MSI B760 DDR5 não herda a ficha DDR4. Na H610M-S, SATA permanece desconhecido
   porque a própria página MSI diverge; na ASRock D5 abreviada, não foram herdadas
   medidas de outra revisão. Builds prontas Intel usam placas coerentes com a RAM.
   Nenhuma alteração em builds salvas, preço, estoque ou banco. 501 testes Node
   e 41 testes Python específicos passaram. Ainda faltam fichas de outros modelos;
   não declarar a compatibilidade física completa nem substituir ausência por palpite.

   Fontes: [MSI DDR4](https://www.msi.com/Motherboard/PRO-B760M-P-DDR4/Specification),
   [MSI DDR5](https://www.msi.com/Motherboard/PRO-B760M-P/Specification),
   [ASRock: anúncio exato](https://www.kabum.com.br/produto/587807/placa-mae-asrock-h610m-hdv-m-2-d5-intel-chipset-h610-ddr5-lga-1700-matx),
   [ASUS A520M-E](https://www.asus.com/motherboards-components/motherboards/prime/prime-a520m-e/techspec/),
   [ASUS B550M-A](https://www.asus.com/motherboards-components/motherboards/prime/prime-b550m-a/techspec/),
   [MSI H610M-S](https://www.msi.com/Motherboard/PRO-H610M-S-DDR4/Specification).

### Buscar melhorias: opções ocultas e expansão de discos — 23/10/2026

A listagem dependia de um budget válido antes de procurar peças. Além disso,
SSD/HD só substituíam a categoria inteira por uma unidade: capacidade total e
velocidades ausentes podiam zerar as opções. CPU/GPU e demais categorias já
instaladas continuam sem classificação quando não há métricas comparáveis; fans
e coolers em categorias vazias podiam aparecer apenas como adições.

- Sem budget válido, agora é possível consultar e preparar a prévia, com aviso
  de que a lista não está filtrada por preço. Aplicar permanece bloqueado até um
  valor válido; quando informado, o teto combinado das novas compras é respeitado.
- SSD e HD têm modos explícitos de adicionar (padrão) ou substituir. Adicionar
  preserva os volumes/quantidades atuais e permite mais uma unidade do mesmo
  modelo ou de outro, sem prometer aumento de velocidade. Não exige velocidades
  comparativas para uma expansão que não remove o disco atual. A substituição
  mantém os critérios anteriores de capacidade e velocidades sem regressão.
- O seletor compartilhado valida M.2/SATA, portas compartilhadas e quantidades;
  a avaliação final mantém regras físicas e demais conflitos. A compra conta
  apenas a unidade nova; o total da build inclui também as antigas. Mudar o modo
  descarta só a seleção daquela categoria, preservando outras trocas e o foco.
- Erros antigos `discos-m2`/`discos-sata` só saem da prévia após revalidação das
  respectivas conexões com dados conhecidos, ou quando a conexão deixa de ser
  usada. Limite desconhecido não limpa erro. Diagnósticos de outras peças ou
  regras desconhecidas permanecem; o servidor reavalia ao salvar.
- Estados sem opções mostram o motivo diretamente. RAM cheia orienta usar o
  modo de substituição; ausência de placa-mãe, DDR/capacidade máxima ou critérios
  comparativos não é escondida por uma mensagem genérica. Não inferir fichas ou
  liberar CPU/GPU por preço, nome, núcleos ou VRAM.

Validação: 493 testes Node e 94 verificações Chrome/axe em 320, 375, 768, 1440 px e
paisagem 844 × 390. Catálogo real somente leitura, builds de teste em memória e
callback de salvamento simulado. Incluídos ausência/erro de budget, expansão e
substituição, slots cheios, fontes, foco, cancelamento e falha ao salvar. Sem
gravação real, API externa, banco alterado, migração, LLM ou envio de e-mail.

### Comparativo: último campo sobreposto — 23/10/2026

O subgrid reservava nove linhas por card, mas havia dez itens: cabeçalho e nove
especificações. Por isso, “Compatibilidade” e “Desempenho em jogos” ocupavam a
mesma linha. O editor agora conta os campos ao renderizar os resultados e passa
`--compare-row-count` ao CSS, usado tanto nas linhas da grade quanto no espaço
ocupado por cada card. A contagem é refeita ao adicionar/remover uma build ou
trocar CPU/GPU. O fallback de layout sem subgrid foi preservado.

Validação: 474 testes Node e 194 verificações Chrome/axe (141 de layout e 53 da
comparação Blender). Layout testado com duas/três builds, descrições de tamanhos
diferentes e pendências abertas/fechadas em 320, 375, 768, 1024, 1440, 1920 px e
paisagem 844 × 390. Sem sobreposição, conteúdo fora dos cards, overflow horizontal
da página ou exceções JS. APIs simuladas; nenhuma gravação na conta/banco ou LLM.
O campo de jogos continua indicando indisponibilidade quando faltam benchmarks;
a correção é visual e não cria estimativas de FPS.

### Comparação Blender: identificação e erros de GPU — 23/10/2026

A identificação Blender estava dependente do pequeno registro de slugs de jogos
e de títulos abreviados. Na leitura real, apenas 44/100 CPUs e 12/100 GPUs eram
reconhecidas antes de consultar o Python. A RTX 5070 EAGLE OC SFF 12G, por exemplo,
era recusada pelo frontend mesmo com resultados públicos no Blender Open Data.

- `benchmark/hardware.js` agora identifica o modelo explícito em títulos
  comerciais completos, independentemente do registro FPS, sem remover sufixos
  Ti/SUPER/XT/XTX/GRE/F/KF/X3D. Repetição do mesmo identificador no título é
  permitida; múltiplos modelos diferentes, mobile/Max-Q, RX 580 2048SP e peças não
  reconhecidas não são convertidos para outro componente. Mantida a restrição
  anterior da referência RTX 3060 de 12 GB: não usar para 8 GB/capacidade ausente.
- A cobertura de identificação chegou a 99/100 CPUs e 93/100 GPUs nesta fotografia.
  Isso **não** significa que todos esses modelos têm resultados públicos. O
  backend ainda exige correspondência do nome devolvido pelo provedor; um 422
  não aciona fallback para outra peça. Nada é estimado ou salvo na build.
- A comparação preserva código/status/espera dos erros por build. O aviso geral
  diferencia falha total, parcial, sessão e versões/métodos incompatíveis, em vez
  de exibir sempre uma mensagem de pontuação como se a consulta tivesse funcionado.
- Uma resposta de pausa bloqueia novas consultas pelo intervalo informado,
  inclusive ao mudar CPU/GPU dentro do modal. Fechar limpa o timer e cancela a
  consulta. `aria-busy` identifica a atualização dos resultados. Cache do modal
  guarda apenas consultas bem-sucedidas; consulta cancelada não sobrescreve a nova.
- CPU e GPU continuam separadas. Classificação só com resultados de todas as
  builds na mesma versão/método. Resultados de métodos diferentes continuam
  visíveis, sem vencedora. A fonte pode agrupar fabricantes/capacidades de VRAM;
  são referências por componente, não medição do PC completo nem tempo garantido.

Validação: 472 testes Node, 582 Python (+13 subtestes) e 53 verificações Chrome/axe
do comparativo em 320/768/1440 px e paisagem 844 × 390, com APIs simuladas e
catálogo real somente leitura. Incluídos GPU 5070/5060 Ti de nomes comerciais,
erro 422, sessão 401, pausa 429, cache, resultado parcial, versões diferentes,
cancelamento/troca de tipo e fechamento. Sem exceções JS, overflow da página ou
gravações reais. As cinco consultas públicas reais pelo BlenderService responderam
com sucesso para Ryzen 5 5600, Core i3-12100F, Core Ultra 5 245KF, RTX 5070 e
RX 6750 XT. Não houve consumo de LLM, mudança no banco ou arquitetura Python.

Ainda pendentes: outros identificadores de hardware, ausência de dados no provedor
e seleção de uma versão/método comum quando os agregados mais recentes divergem.
Não classificar resultados incompatíveis apenas para preencher o destaque.

### Gabinetes: fans inclusas, capacidade e medidas — 23/10/2026

Seis variantes exatas receberam fichas de fabricante no manifesto compartilhado
`frontend/data/medidas-fisicas.json`. O complemento é aplicado na leitura por
`Peca.to_catalogo()`, pelo prompt da montagem e pelo catálogo demonstrativo JS.
Sem alteração do SQLite, migração, coleta de preços/imagens ou chamada LLM.
Reiniciar um backend já aberto permite reler o manifesto em cache.

- DeepCool MATREXX 55 V4 C, R-MATREXX55-BCADA4-G-4, produto 987488:
  quatro fans inclusas (três de 140 mm frontais e uma de 120 mm traseira), oito
  posições totais; 421 × 215 × 483 mm (C × L × A). Limites GPU/air/fonte:
  370/165/170 mm. Não equivale ao MATREXX 55 original.
- NZXT H5 Flow 2024 Black, CC-H52FB-01, produto 692553: duas fans de 120 mm
  inclusas, oito posições, 430 × 225 × 465 mm (C × L × A). Radiador frontal de
  até 360/280 mm, conforme base; 280 mm superior depende de RAM baixa e não é
  liberado automaticamente no topo. Site/manual divergem em GPU/air (410/425 e
  170/175 mm), por isso esses limites ficam não confirmados. Não aplicar ao H5
  antigo, RGB ou Elite. Fans de fábrica não são remanejadas automaticamente.
- MSI PRO SHIELD M100P, produto 1017873: uma fan traseira de 80 mm inclusa e
  apenas uma posição para 80 **ou** 90 mm; 312 × 166 × 354 mm (C × L × A).
  GPU/air/fonte: 275/140/160 mm. Não confundir com MAG FORGE M100R.
- AeroCool Cylon Black, 63858, produto 203445: uma fan de 120 mm inclusa,
  sete posições listadas (duas são do suporte de ventilação da GPU); dimensões
  externas 413 × 198 × 459 mm (C × L × A). GPU 346 mm com fan frontal;
  371 mm exige removê-la. Air 155 mm. Radiador frontal de 120 mm segundo o
  fabricante; não assumir 240 mm da descrição comercial nem folga para a fonte.
- Hayom GB1727 / GB.17.10.27, produto 938469: três fans frontais de 120 mm
  inclusas, oito posições, GPU até 290 mm. Tamanho externo informado como
  295 × 190 × 405 mm, sem atribuir eixos que a ficha não identifica.
- Hayom GB1787, produto 933255: três fans de 120 mm inclusas, cinco posições,
  GPU até 260 mm. Tamanho 265 × 280 × 285 mm, eixos não identificados. Sem
  posição de fábrica declarada, não inventar a distribuição das três fans.

Fontes e revisão de 23/10/2026 registradas em cada ficha:
[DeepCool](https://global.deepcool.com/products/Cases/MATREXX55-V4-C-ATX-Glass-Panel-Case/2024/18145.shtml),
[NZXT](https://support.nzxt.com/hc/en-us/articles/40225168535451-H5-Flow-2024-Specs),
[radiadores NZXT](https://support.nzxt.com/hc/en-us/articles/47060012674203-What-radiator-sizes-does-the-H5-Flow-2024-support),
[MSI](https://www.msi.com/PC-Case/PRO-SHIELD-M100P/Specification),
[AeroCool](https://aerocool.io/product/cylon/),
[Hayom GB1727](https://www.hayom.com.br/produtos/gabinete-gamer-c-3-fans-gb1727),
[Hayom GB1787](https://www.hayom.com.br/produtos/1271).

Os aliases exigem fabricante, modelo, código interno e produto KaBuM revisados;
nome parecido ou outro anúncio não herda especificações. Contagem inclui fábrica,
fans adicionais por kit e AIO, sem somar opções alternativas de 120/140 mm nem
aprovar espessuras/interferências desconhecidas. Dimensão externa não determina
quantas fans cabem: são necessárias as posições e medidas de fixação declaradas.
O catálogo agora mostra inclusas, capacidade total e diâmetros; o editor também
mostra inclusas/capacidade junto ao gabinete, além do contador de ventilação.

Fotografia somente leitura: 100 gabinetes, 53 com contagem inclusa cadastrada
(30 positivas, 23 zero, nem todas revisadas nesta rodada), 47 sem essa contagem,
9 com capacidade e 8 com posições detalhadas. Antes eram 3 com capacidade/posições.
O manifesto tem 31 variantes, aplicadas a 33 dos 1.535 cadastros. RF13 continua
parcial: esta rodada não certifica todos os gabinetes ou o encaixe completo.

Revisão pendente de variantes/anúncios, sem sobrescrita automática:
Corsair 2000D SEED-CASE-44/433279 (SKU branco e contagem divergente), Hayom
GB1796 SEED-CASE-24/732926 (kit do vendedor versus configuração de fábrica),
Lian Li SEED-CASE-29/582808 (EVO RGB, não O11 Dynamic comum; suportes condicionais),
MB520 SEED-CASE-12/171504 (gerações distintas), Rise Wave e HYTE Y70 Touch
Infinite (fichas completas da variante ainda necessárias).

Validação automatizada: 443 testes Node e 582 Python (+13 subtestes). Fixture
compartilhada verifica identidade, dados desconhecidos, kits, fans inclusas,
limite exato, excesso, tamanhos, AIO e propagação à API/prompt sem alterar modelos.
Os 16 modelos prontos não ganharam conflitos técnicos; mantém-se a pendência
anterior de estoque no modelo Intel. Validação Chrome/axe: 258 verificações de
fichas, editor, limites e catálogo em 320/768/1440 px e paisagem 844 × 390;
mais 57 da regressão de páginas/modelos. O seletor do roteiro de QA foi corrigido
de `.catalog-card` para `.product-card`; a rodada final dos cards passou.
APIs simuladas, catálogo real somente leitura; nenhum envio de e-mail ou consumo
de cota LLM. Sem erros JS, overflow horizontal ou violações axe nas telas testadas.

### Barrinha de compatibilidade ao lado do nome — 23/10/2026

O indicador circular de informação foi substituído pela barra vertical antes do
nome, nos cards de Minhas builds, no editor e na visualização pública. Usa azul
primário sem problemas, amarelo para pendências e vermelho para erros, mantendo
o diagnóstico existente. Não altera as regras nem o percentual de preenchimento.

A barra tem 3 px de largura visual e botão transparente de pelo menos 24 px de
largura, com nome acessível, foco visível, `aria-expanded` e `aria-controls`.
Hover, clique/toque e teclado continuam abrindo os detalhes; Escape fecha.
O painel se ajusta às bordas da tela, e o editor centraliza a barra no título.
Removidos os estilos antigos do círculo e o posicionamento à direita do nome.

Validação: 427 testes Node, 45 verificações de páginas/axe, 85 de interação e
36 de compartilhamento. Mais 47 verificações finais de alinhamento, área clicável,
hover, Escape e limites do painel em 320/1440 px; a rodada geral também cobriu
390/768 px. APIs simuladas, sem alteração do banco ou regras de compatibilidade.

### Preço nas lojas e RAM com slots ausentes — 23/10/2026

- O preço principal existia no catálogo, mas a API não enviava `ofertas`, que o
  card de cada loja consome. `Peca.to_catalogo()` agora monta a oferta KaBuM a partir
  da cotação já coletada: preço positivo/finito, data da coleta e link HTTPS do
  produto no domínio exato, sem credenciais/porta alternativa. Nenhuma consulta de
  preço acontece ao serializar. Não transfere esse preço para Pichau ou buscas.
- O preço inicial da seed, sem data de coleta, não é apresentado como oferta.
  Produto esgotado pode exibir o último preço, mas informa indisponibilidade e
  preserva a data antiga. A página lembra que o preço cadastrado não inclui frete.
- `slotsRam()` separa capacidade confirmada de política provisória. Ausência ou
  valor inválido usa limite de **dois pentes**, sem modificar a ficha/banco.
  Zero, um ou quatro slots explicitamente cadastrados continuam prevalecendo.
  Kits e modelos diferentes dividem o limite; o terceiro pente fica bloqueado.
- O editor informa que a contagem é provisória e orienta confirmar slots e
  capacidade no manual. Não foi atribuída capacidade máxima desconhecida nem
  aprovada compatibilidade completa por esse limite. Melhorias usam a mesma
  política de slots, mas ainda exigem DDR/capacidade máxima para uma proposta segura.
- Python mantém `ram-slots` como não verificado quando falta o dado real e avalia
  separadamente `ram-limite-provisorio`, identificado como política de montagem.
  A validação da geração rejeita excesso; o prompt instrui contar pentes próprios,
  novos e por kit dentro desse teto, sem inventar especificações.

Fotografia somente leitura: 35 das 100 placas-mãe sem slots; 1.435 das 1.535 peças
com cotação datada e link de produto KaBuM agora expõem a oferta correspondente.
Validação: 424 testes Node, 561 Python (+13 subtestes), 43 verificações Chrome de
preço/seleção/duplicação, 51 de páginas/modelos/axe e 92 de melhorias/RAM, incluindo
320/768/1440 px e paisagem 844 × 390. Banco real somente leitura; salvamentos de
interface simulados, sem migração, coleta externa, envio de e-mail ou chamadas LLM.

### Transição de valores e retorno à build — 23/10/2026

- `components/value-transition.js` anima apenas números alterados: entrada vertical
  de `0.45em`, blur de `4px` e duração de `360ms`. Aumento entra de baixo;
  diminuição inverte o sentido. Para ajustar o efeito, altere esses valores e a
  curva de easing nesse módulo. A aparência não interpola preços: o texto já
  contém o valor final correto, sem cópias para leitores de tela.
- Aplicado aos totais/consumo/quantidades do editor, saldo do orçamento, orçamento
  do formulário, preços/progresso/cota em Minhas builds e totais da prévia de
  melhorias. Não anima o primeiro carregamento nem valores iguais. Chaves
  `data-value-key` permitem comparar os números quando os cards são recriados.
- `atualizarValor` preserva o elemento ao digitar/arrastar, sem empilhar animações.
  `prefers-reduced-motion` desativa o efeito e cancela animações em andamento;
  navegadores sem Web Animations mostram a atualização diretamente. CSS compartilhado
  usa algarismos tabulares e não sobrescreve o layout próprio dos componentes.
- Links explícitos do catálogo/editor usam `data-back-destination`: o histórico
  só prevalece quando identifica a mesma página, build e categoria. Filtros e hash
  são preservados nesse contexto; início/outra build não substituem o destino.
  Retornos genéricos à página anterior mantêm o comportamento existente.
- Falhas no catálogo/peça mantêm o ID da build. Sem contexto, ou numa falha do
  próprio editor, o retorno é Minhas builds, nunca o editor sem ID que criaria
  outra configuração. Nenhuma mudança no backend, banco ou cálculos.

Validação: 418 testes Node aprovados, 77 verificações de interação no Chrome em
320/768/1440 px e paisagem 844 × 390, com movimento normal/reduzido; mais 63
verificações de páginas afetadas/axe e 92 de melhorias/RAM. APIs e gravações
simuladas; catálogo real somente leitura. Sem criações involuntárias ou erros JS.
As medições de contraste aguardam o fim dos efeitos de scroll já existentes.

### Navegação, verificação de e-mail e expansão técnica — 23/10/2026

- Footer: hover com cor primária e sublinhado suave apenas sobre o link, incluindo
  foco de teclado. `navigation-current.js` marca a página atual no footer, hamburger
  e perfil com `aria-current="page"`: azul fixo, sem fundo/underline/animação no hover
  ou recarregamento redundante no clique normal. Href e foco são preservados;
  ações como `?criar=1`, seções e atalhos de abrir link em outra aba continuam livres.
- Modal de verificação: título azul de 1,5 rem, fonte de corpo Poppins, endereço
  separado e seis dígitos (corrigido texto antigo de quatro). Fundo escuro mais
  legível e camada acima da navegação, sem transparência que revele os textos de
  trás. Mantidos colar código, reenvio, erros e foco/Escape; descrição associada ao diálogo.
- E-mail: fundo preto, card `#1c1c1e`, borda `#3a3a3c`, azul `#007bff` e textos
  branco/cinza da identidade. Código sem monoespaçada: Lexend com fallback Arial;
  corpo Poppins/Arial. Não baixa fontes externas nem exige que o cliente de e-mail
  suporte webfonts; aparência exata pode variar. Alternativa em texto e proteções
  de emissão/uso único/expiração permanecem; não houve envio real ou mudança no SMTP.
- O manifesto agora tem 25 variantes e complementa 27 dos 1.535 cadastros na
  leitura atual. A ampliação desta rodada cobre A520M-K/A520M-A PRO/B550M PRO-VDH
  WIFI, ASSASSIN IV/V4 Alpha/A12 240, RF120 avulsa, Fury KF432C16BB/8, NV2/NV3
  500 GB/1 TB, Ryzen 7 9800X3D e P650G PG5. Novos campos também chegam ao prompt
  quando relevantes. Nenhuma migração, coleta de preço/imagem ou chamada LLM.
- A ficha AMD do 9800X3D confirma Radeon integrada, ausência de cooler e TDP 120 W.
  TDP fica separado: não vira consumo elétrico medido nem altera silenciosamente
  o consumo estimado cadastrado. Perfis de RAM não equivalem a OC garantido.
- A fan RF120 desta ficha é uma unidade, com RGB 12 V de quatro pinos e PWM;
  não confundir com kit de cinco nem conectar RGB 12 V diretamente a ARGB 5 V.
  SSDs usam os valores da capacidade correta e distinguem M.2 2280 de 2230.
- O ASSASSIN IV tem lista oficial de exceções de placa-mãe. Python e JS bloqueiam
  os modelos exatos dessa lista, mesmo sem gabinete selecionado. Ausência na lista
  não certifica as demais combinações; nenhuma equivalência aproximada foi criada.

Revisão ainda necessária, sem sobrescrever dados ambíguos: SEED-RAM-03 está como
DDR5 no cadastro, mas aponta para anúncio do DDR4 KF432C16BB/16 (402907);
SEED-MB-07 aponta para PRO B760M-P DDR4 apesar do cadastro DDR5; SEED-MB-03 aponta
para B550M DS3H AC R2 com nome abreviado; SEED-MB-22 aponta para a variante D5.
Esses casos não receberam fichas de outra variante. Links não são prova de toda a
identidade técnica. Corrigir catálogo/modelo/anúncio exige revisão própria.

O usuário autorizou commit/push depois dos testes, incluindo o complemento da
rodada anterior. As mudanças locais de imagens/home/animação ficam fora do commit.

Validação desta rodada: 408 testes Node, 533 Python (+13 subtestes), 341 verificações
das fichas no Chrome, 78 do footer/menu/modal/e-mail, 36 de compartilhamento/modelos
e 63 de páginas afetadas/modelos em 320/768/1440 px, sem exceções/overflow/violações
axe nas telas auditadas. E-mail só renderizado em prévia local, sem envio SMTP real.

### Enriquecimento técnico reversível — 23/10/2026

Registro da rodada inicial, entregue **sem commit/push** naquele momento, sem
migração, coleta ou escrita no banco; a autorização posterior está no bloco acima.
O complemento compartilhado passou de cinco para onze variantes, consultadas em
fontes oficiais. Cada ficha nova registra `fonte`, `verificado_em` e o modelo oficial.

- TD500 Mesh V2 White: limites de GPU/cooler/fonte, sete slots, baias e posições
  alternativas de fans/radiadores; três fans de 120 mm de fábrica contam na ocupação.
- RTX 5070 EAGLE OC SFF 12G: comprimento/altura/espessura, barramento de 192 bits e
  conector de 16 pinos. Não foi inferida uma quantidade de slots a partir da espessura.
- Hyper 212 3DHP Black ARGB: altura real de 158 mm, demais eixos e lista de sockets.
- CX650 CP-9020278-BR: comprimento de 125 mm, sem aplicar a outras revisões da CX650.
  A ficha oficial brasileira estava indexada, mas o acesso direto retornou 404 na
  consulta; revalidar a disponibilidade desse endereço antes de ampliar a coleta.
- ASRock A620AM Pro RS: AM5/DDR5, quatro slots, limite anunciado de 256 GB,
  três M.2 para SSD PCIe/NVMe e duas portas SATA. O Key E para Wi-Fi não soma um SSD.
  Não foi inventada frequência máxima comum, pois as seções da ficha divergem em OC.
- MSI MAG CORELIQUID A13 240: radiador externo de 277 × 119,6 × 27,2 mm e duas
  fans de 120 × 120 × 25 mm; conjunto de 52,2 mm sem folgas adicionais presumidas.

As fontes oficiais completas ficam em `frontend/data/medidas-fisicas.json`. A
identidade tradicional continua exigindo categoria/fabricante/modelo/part number.
Entradas novas podem declarar `aliases_catalogo`: nomes e códigos internos exatos
mais ID de produto KaBuM revisado. Somente HTTPS no domínio exato, sem credenciais,
redirecionadores ou inferência pelo slug. Esse vínculo não consulta nem certifica
o anúncio em tempo real. Sem o vínculo esperado, não aplicar o complemento.

Validação: 403 testes Node e 529 Python (+13 subtestes), todos aprovados; 98
verificações Chrome/axe das seis fichas em 320/768/1440 px, sem exceções, overflow
ou violações nas telas verificadas. Catálogo real lido sem escrita: as seis fichas
foram aplicadas e os 16 modelos não apresentaram novos conflitos técnicos. Durante
a consulta, a PRO B760M-P ficou indisponível; isso é estoque, não falha de encaixe.
Outras 36 verificações Chrome de compartilhamento/cópia/cota e modelos prontos
também passaram, com APIs simuladas. A auditoria distingue estoque variável de
conflito técnico; não pressupõe que todas as ofertas estejam sempre disponíveis.

`Peca.to_catalogo()` expõe os campos sem atualizar o ORM. A montagem automática
recebe os mesmos dados revisados em `_campos_pecas`; não houve nova chamada LLM.
O demo usa a mesma identidade e medidas, copiando objetos aninhados. As telas
mostram variante, fonte/data e posições legíveis; baias/dimensões genéricas antigas
ficam ocultas quando há dados específicos revisados, sem apagar o registro original.

Limitações preservadas: CPU/BIOS/QVL, corrente/conectores, compartilhamentos não
documentados e folgas completas de radiador/RAM/GPU continuam não verificados.
O TD500 Mesh V2 aceita E-ATX com limites de dimensão, não todas as E-ATX; por isso
não recebe aprovação genérica. A recomendação de 55 mm no topo não virou limite
certificado do conjunto com fans. A ASRock H610M-HDV/M.2 cadastrada como DDR4 aponta
para anúncio D5: **não enriquecida**, precisa de revisão do catálogo/anúncio.

Para desfazer só esta experiência, remover as seis novas fichas do manifesto já
desativa os novos complementos após reiniciar o backend (manifesto em cache por
processo). Os dados originais seguem no banco. Para remover também a implementação,
reverter apenas os trechos desta rodada em `models/medidas_fisicas.py`,
`criar_build_service.py`, `hardware.js`, `catalogo.js`, README/documentação e remover
os novos `build/medidas-fisicas.js`, `tests/fichas-tecnicas.test.mjs`,
`tests/fixtures/fichas-tecnicas.json` e `test_fichas_tecnicas.py`. Não restaurar
globalmente o repositório: imagens, animação e alterações da home já eram locais.

### Expansão de RAM, verificação de e-mail e fans — 23/10/2026

- O modal de melhorias começa com RAM/SSD/HD, categorias com critérios comparáveis.
  CPU/GPU continuam disponíveis nos filtros, mas sem ranqueamento inventado.
  Preço zero não é tratado como uma melhoria gratuita.
- `build/melhorias-ram.js` planeja uma cópia sem gravar: acrescentar é o padrão e
  mantém as memórias atuais; substituir é uma escolha explícita que aceita vários
  modelos/quantidades. O modal oferece o mesmo modelo atual, controles de quantidade
  e preço apenas das novas compras. A aplicação continua exigindo confirmação.
- Placa-mãe atual identificada, DDR, slots e capacidade máxima são obrigatórios
  para a sugestão de RAM. Kits contam pentes × quantidade e GB por item × quantidade.
  Adição mantém frequência/DDR; outros modelos precisam de CAS comparável, sem piora
  relativa. Troca não pode reduzir capacidade/frequência ou sair de vários pentes
  para apenas um; quatro pentes podem virar dois com capacidade preservada.
- Dois pentes do mesmo modelo/capacidade são uma preferência, não certificação de
  dual channel: instalar conforme manual, considerar suporte CPU/placa-mãe e kits
  testados juntos. Misturas mantêm o aviso de estabilidade/XMP/EXPO. Referência:
  [orientação Intel](https://www.intel.com/content/www/us/en/gaming/resources/how-much-ram-gaming.html).
- Modelos/quantidades/preços são revalidados contra o catálogo em memória antes de confirmar; o callback
  existente salva uma única configuração. Erros de outras peças vindos do servidor
  não são descartados por uma expansão de RAM. O diagnóstico da seleção nova é parcial.
- E-mail de verificação: HTML responsivo e alternativa em texto, código de seis
  dígitos, nome escapado, prazo de cinco minutos, instruções para reenvio/segurança e
  identificação de mensagem automática. Sem imagens/fontes remotas, rastreamento ou
  anexos. Preservados limites, uso único, vínculo com o destinatário e SMTP/TLS.
- Não há garantia de caixa de entrada por mudar HTML. Em domínio próprio, configurar
  autenticação SPF/DKIM/DMARC e alinhamento no provedor/DNS, verificar reputação e os
  cabeçalhos de mensagens de teste. Não falsificar From nem adicionar autenticação
  inventada pelo Python. [Diretrizes oficiais Gmail](https://support.google.com/mail/answer/81126?hl=pt-BR).
- Geração: prompt e Python exigem ventilação, mesmo sem a capacidade documentada do
  gabinete. Fans incluídas no gabinete ou AIO contam quando confirmadas; fan própria
  é preservada sem recompra. Onde a capacidade é conhecida, continua sendo obrigatório
  completar as posições, sem excesso e sem transferir sobras de periféricos. A omissão
  usa a revisão automática limitada; não salva uma resposta inválida.

#### Como enriquecer os dados técnicos sem migrar o banco

1. Usar a ficha/manual oficial da variante exata e part number real, quando existir.
   Identificadores `SEED-*` são internos, não códigos oficiais para procurar no fabricante.
   Preços/imagens das coletas não provam que medidas e listas de suporte estão completas.
2. Normalizar unidade/eixo e guardar referência da fonte. Alimentar as fichas em
   `frontend/data/medidas-fisicas.json`, que o backend lê em
   `models/medidas_fisicas.py::completar_medidas`. `Peca.to_catalogo()` já inclui esse
   complemento na API. A seleção exige categoria, fabricante, modelo e part number;
   variantes parecidas não herdam a ficha. Não houve coleta nova nem alteração do banco.
3. Ampliar primeiro gabinetes/GPU/coolers mais usados: dimensões, posições alternativas
   de fans/radiadores, espessura do conjunto e interferências. Não deduzir eixos pelo
   nome comercial nem usar uma folga universal para AIO.
4. BIOS/lista de CPUs, QVL/perfis de RAM, conectores e compartilhamento de portas exigem
   dados de suporte próprios do fabricante, além das medidas. Automatização futura deve
   validar extração, fonte/data e revisão antes de publicar, sem usar LLM como prova.

### Formulário, modelos e compartilhamento — 23/10/2026

- `main` integrada por fast-forward até `d20fc97`, mantendo CSRF, limitação global
  de chamadas e bloqueio de geração por usuário. Sem migrações nem alterações no
  banco real. As alterações de imagens e animações locais foram preservadas.
- Homologação real do formulário pela rota `POST /build/` em SQLite temporário,
  com catálogo disponível e filtros de produção: estudos, R$ 6.000, gerada após
  uma revisão automática, HTTP 201 e total de R$ 2.956,80. Foram consumidas as três
  chamadas gratuitas autorizadas: duas no primeiro cenário e uma no segundo.
  O segundo cenário foi interrompido antes de uma quarta chamada pelo limite local
  do ensaio; não é evidência de limite ou erro do Gemini. Sem fallback pago ou builds
  nas contas reais. A validação adicional de rede foi testada offline depois disso.
- Rede do formulário valida objeto, tipo, booleano de posse e medidas positivas
  finitas. Cabo com comprimento confirmado menor que o solicitado provoca revisão,
  sem ampliar o orçamento. Especificação ausente não equivale a medida suficiente.
- Os 16 modelos foram revisados contra estoque/preços atuais, preservando
  plataformas, capacidades e ausência de periféricos. A página reconsulta vagas
  no foco/retorno, bloqueia cópia sem e-mail verificado ou com três builds e
  confirma novamente antes do POST. O servidor continua sendo a autoridade do limite.
- `GET /build/<s-id>/publica` é a exceção pública: consulta apenas build com
  visibilidade pública, envia `Cache-Control: no-store`, as peças selecionadas e
  diagnóstico parcial. Não expõe `usuario_id`, budget, setup atual, anotações de
  rede nem extras particulares. O JSON original não é modificado pela leitura.
- `build/publica.js` usa essa resposta em uma tela separada, sem inputs, ações de
  edição ou acesso ao catálogo privado completo. Descrição/nome são escapados;
  preços parciais e frete permanecem explícitos. O editor normal continua privado.
- `POST /build/<s-id>/copiar-publica` exige sessão, CSRF, e-mail verificado e vaga
  transacional. Revalida a visibilidade no momento da cópia e usa o serviço manual
  existente. A nova build é privada, destrancada, sem marca de setup atual nem
  dados pessoais da origem; o budget autorizado é o do destinatário.
- Retorno do login: `components/sessao-publica.js` aceita somente ID público e
  ação `testar`/`salvar`, guarda por até 15 minutos na sessão do navegador e consome
  uma única vez. Não aceita URLs externas. `auth.js` retoma no login/cadastro ou
  início (callback Google). Salvar ainda exige confirmação explícita; testar abre
  somente a escolha do teste, sem consultar um provedor automaticamente.
- Requisitos autenticados de uma build pública usam
  `/benchmark/requisitos-build?game=...&build_id=s-...&origem_publica=1`.
  A rota confere a visibilidade novamente; sem a flag continua exigindo proprietário.
  O cliente valida `ram.fonte: build_publica`; não é uma aprovação de CPU/GPU/FPS.
- RF07, RF09 e RF12 são concluídos no escopo acordado. Comparação de FPS, novos
  critérios de upgrade e confirmação do agendamento em produção continuam extensões.
  RF13 segue parcial: dados ausentes/BIOS/interferências não são certificados.

### Homologação de catálogo e capacidades — 22/10/2026

- `catalogo-auditar` é um comando de leitura, registrado junto dos comandos de
  peças existentes. Não prepara esquema, não consulta lojas e não atualiza dados.
  O resumo distingue estoque desconhecido, preço inválido/sem data, link de produto,
  imagem local existente, URL remota não consultada e ficha física revisada.
- `imagens-referencia.json` recupera 750 vínculos do histórico do projeto,
  conferidos contra o catálogo e arquivos existentes. Backend e frontend exigem
  part number, categoria, fabricante e modelo. O manifesto gerado por coleta tem
  prioridade no navegador; `imagem_url` tem prioridade no backend. Não sobrescrever
  a coleta nem deduzir imagem por IDs após recriar o banco.
- Novas fichas exatas em `medidas-fisicas.json`: [NR200](https://www.coolermaster.com/en-global/products/masterbox-nr200.html),
  [MAG A650BN](https://www.msi.com/Power-Supply/MAG-A650BN/Specification) e
  [RTX 5060 8G Shadow 2X OC](https://www.msi.com/Graphics-Card/GeForce-RTX-5060-8G-SHADOW-2X-OC/Specification).
  NR200 usa ITX/Mini DTX e SFX/SFX-L, não mATX/ATX; inclui fan traseira de 92 mm
  e uma superior de 120 mm. Limites se referem a GPU horizontal. Radiador na base
  consta como custom loop no fabricante, não como suporte AIO nesta curadoria.
  Observações ficam no diagnóstico e prompt. Revisões diferentes não herdam ficha.
- O prompt recebe pares de IDs por socket e a categoria de rede obrigatória ou
  proibida, calculados pelo servidor. A lista não certifica BIOS/DDR/encaixe.
  Três consultas reais autorizadas, isoladas e sem persistência: uma válida e duas
  rejeitadas. O catálogo do ensaio era ampliado; revisão automática de produção
  e prompt novo ainda não foram homologados novamente com cota real.
- Requisitos da build: além de RAM, `vram` e `armazenamento` usam somente modelos
  persistidos da própria conta. Campos mínimos estruturados vêm das fontes oficiais
  versionadas, não de extração do texto em tempo de requisição. Capacidade de VRAM
  não mede a GPU; armazenamento usa a maior unidade elegível, sem somar volumes
  ou supor espaço livre. Cyberpunk exige SSD. Falhas confirmadas compõem
  `impedimentosMinimos` e evitam consulta FPS na interface. Dados ausentes permanecem
  null; `escopo: parcial`, `fpsValidado: false` e `requisitosVerificados: false`
  são preservados. O laboratório manual continua limitado à capacidade de RAM.
- Não foram configurados scheduler/VPS, deploy, nova API paga ou migrações.

### Ventilação, water cooler e informações da build — 22/10/2026

- `substituirFansWaterCooler` é uma opção booleana explícita no estado JSON da
  build, validada no Python e mantida na conta, cópia, importação/exportação JSON/CSV
  e compartilhamento legado. Não cria coluna nem exige migração. Remover o water
  cooler no editor limpa a opção; selecionar um novo cooler não herda a troca.
- Sem essa opção: total = fans avulsas/por kit + inclusas do gabinete + fans do
  radiador. Com a opção: desconta as originais substituídas, sem remover o custo
  das fans compradas. A distribuição reserva fans selecionadas do tamanho do AIO
  e ocupa as posições do radiador uma vez. Tamanho incorreto ou quantidade
  insuficiente são erros; falta de especificação continua não verificada.
  Substituir só parte das fans e remover fans de fábrica do gabinete não são
  opções implementadas. Não pressupor push/pull ou posições extras disponíveis.
- O editor permite duplicar e misturar modelos de fans, sem exigir marca ou
  frequência iguais como na RAM. Orientações cobrem tamanho/furação, espessura,
  pressão estática, conectores/tensão/corrente/hub e parafusos do radiador.
  As instruções e comprimentos de parafusos devem seguir o fabricante, não uma
  medida genérica ([manual EK](https://www.ekwb.com/shop/EK-IM/EK-IM-3831109860205.pdf)).
- `encaixe_radiador()` / `encaixeRadiador()` comparam `comprimento_radiador_mm`,
  `largura_radiador_mm` e `espessura_radiador_mm + espessura_fan_mm` com
  `limites_radiador_mm` do gabinete: lista de posições, `tamanhos_mm`,
  `comprimento_mm`, `largura_mm`, `espessura_conjunto_mm`. Basta uma posição com
  medidas compatíveis para esse critério; isso não aprova a distribuição conjunta
  com GPU/RAM/tubos. Dados ausentes nunca viram zero. Não há regra "sete fans =
  gabinete mini" nem margem arbitrária de 3–5 cm. Tamanho nominal não é comprimento
  externo ([exemplo oficial Corsair](https://www.corsair.com/eu/en/p/cpu-coolers/cw-9060016-ww/hydro-series-h105-240mm-extreme-performance-liquid-cpu-cooler-cw-9060016-ww)).
- O prompt instrui preencher posições confirmadas dentro do teto do PC, descontar
  fans do gabinete/AIO, escolher unidades/kits com número exato e não planejar troca
  de fans originais automaticamente. O backend rejeita posições cadastradas vazias
  ou excesso e permite a revisão limitada já existente. Orçamento não é ampliado.
  Capacidade ausente continua parcial; não inventar fans para completar uma suposta
  capacidade. Se a combinação não existir ou não couber no orçamento, a geração
  pode exigir revisão/novo orçamento em vez de persistir uma saída inválida.
- Fans Reverse estão identificadas nos nomes da seed/demo: ROUND5 Nordwind
  Reverse Black, Rise Mode Magneto Pro Reverse e ASUS TUF Gaming TR120 Reverse.
  `Fan.to_catalogo()` informa `fluxo_ar: reverso` com
  `fonte_fluxo_ar: nome_comercial`; sem nome explícito, não presume fluxo normal.
  O banco SQLite local inspecionado não tinha tabela `fan`; não se executou seed.
  Não transformar identificação comercial em ficha certificada.
- Sentido de fluxo depende da orientação. Entrada frente/base/lateral e saída
  topo/traseira são sugestões quando o gabinete permitir; não são critérios de
  incompatibilidade. Reverse pode preservar o acabamento de uma entrada, sem
  tornar uma fan normal inadequada ([ASUS](https://press.asus.com/news/press-releases/asus-launches-tuf-gaming-tr120-argb-case-fans/),
  [Noctua](https://www.noctua.at/en/support/faqs/how-do-i-determine-my-fans-airflow-direction)).
- O botão `i` substitui a barra no editor e nos cards. Branco para informações sem
  pendência conhecida, amarelo para faltas/avisos/verificações pendentes e vermelho
  para erros. Hover, clique/toque e foco abrem; Escape/saída fecham. `aria-expanded`,
  `aria-controls` e `inert` acompanham o estado. O popover é contido na viewport e
  elevado sobre os cards, com rolagem própria para textos longos.
  Validação: 341 testes Node e 443 Python (+4 subtestes), sem chamadas a LLMs ou
  APIs pagas e sem iniciar `app.py` ou alterar o banco local.
  No Chrome, 85 verificações em 320/390/768/1440 px com API simulada cobriram
  persistência, duplicação, substituição, painel nos cards/editor, teclado e
  contenção horizontal/vertical na viewport, sem exceções JavaScript.

### Encaixe físico e capacidade de fans — 22/10/2026

- `services/build_service/encaixe_fisico.py` complementa o diagnóstico Python:
  comprimento/altura/espessura e slots da GPU, altura explícita do air cooler,
  formato/comprimento da fonte, baias dedicadas 2,5/3,5, radiador e fans.
  Somente campos explícitos e conhecidos podem aprovar ou reprovar uma regra.
- O frontend usa `hardware.js`/`fans.js` na filtragem do catálogo e na seleção,
  inclusive ao selecionar o gabinete depois das peças. O Python usa o catálogo
  da conta, nunca medidas enviadas pelo navegador/LLM, e rejeita conflitos na
  geração antes de persistir. Rascunhos manuais continuam podendo ser salvos com
  diagnóstico de erro; não são apresentados como montagens compatíveis.
- Quantidade física = fans por kit × kits + fans inclusas + fans do radiador.
  `posicoes_fans` descreve grupos com `nome`, `opcoes` (tamanho/quantidade),
  `fans_inclusas` (tamanho/quantidade) e `radiadores_mm`. As opções de um grupo
  são alternativas. A busca testa distribuições entre os grupos, reservando as
  fans de fábrica e o radiador, sem contar encaixes 120/140 duas vezes.
  Se a ficha só documenta alguns arranjos, `posicoes_fans_completas: false`
  mantém misturas não documentadas como desconhecidas, sem inventar conflito.
  Excesso confirmado por diâmetro ou capacidade total continua sendo rejeitado.
  O water cooler precisa de `tamanho_fan_mm` e `quantidade_fans` explícitos para
  verificar a distribuição; não se divide o tamanho nominal do radiador para inferi-los.
- O editor mostra total/capacidade e separa fans selecionadas, inclusas e do
  radiador. Posições livres são um limite superior: a disponibilidade real depende
  do tamanho e da distribuição. Não há remoção automática de fans de fábrica.
  Gabinete com fans inclusas já atende à presença de ventilação no progresso;
  não exige comprar fans adicionais somente para completar essa categoria.
- `frontend/data/medidas-fisicas.json` é uma fonte compartilhada por Python e
  catálogo demonstrativo, com categoria, fabricante, modelo, part numbers exatos e
  URL oficial. `models/medidas_fisicas.py` complementa `to_catalogo()` sem gravar
  na base nem exigir migração. Não aplica dados a modelos/revisões parecidos.
  Cobertura inicial revisada: [Q300L preto](https://www.coolermaster.com/en-global/products/masterbox-q300l.html)
  e [AK400 padrão](https://www.deepcool.com/products/Cooling/cpuaircoolers/AK400-Performance-CPU-Cooler/2021/15222.shtml).
  Os aliases SEED representam somente os modelos exatos identificados na seed local.
- Limites: faltam medidas de muitas GPUs/fontes/gabinetes, espessura/posição real
  do conjunto radiador+fans, folgas dos cabos, interferência frontal com GPU e
  RAM, baias compartilhadas, revisão/BIOS e conectores. `escopo: parcial` continua
  obrigatório. Não declarar encaixe completo com dimensões externas do gabinete.
- Fixtures comuns Python/JS cobrem limites exatos, kits, tamanhos misturados,
  posições alternativas, radiador, dados ausentes/numéricos e conflitos parciais.
  Validação: 324 testes Node, 419 Python (+4 subtestes) e 25 verificações Chrome
  com API simulada em 320/390/768/1440 px, sem transbordamento horizontal.

### Requisitos na build e integração da main — 22/10/2026

- Main integrada por fast-forward até `4d4f51d`: CSRF, limites, confirmação de
  identidade e revogação de sessões preservados. A inicialização atual prepara o
  banco explicitamente; iniciar o servidor não cria tabelas nem coleta preços.
- `GET /benchmark/requisitos-build?game=...&build_id=...` segue Blueprint → service,
  exige sessão e procura a configuração somente na própria conta. IDs inválidos,
  parâmetros repetidos e tentativas de enviar outra RAM/usuário são rejeitados.
  Ausência e build de outra conta recebem o mesmo 404.
- A RAM vem do estado salvo e do catálogo Python: capacidade por produto/kit ×
  quantidade. Quantidade de pentes é contada separadamente, sem dobrar novamente
  a capacidade dos kits. Memórias próprias, modelos removidos e quantidades
  inválidas deixam a capacidade total não verificada; o subtotal conhecido aparece
  sem reprovar ou aprovar a memória ainda não identificada.
- O modal oferece Verificar requisitos independentemente da FPSHQ e dos IDs de
  CPU/GPU aceitos pelo benchmark. Ver desempenho verifica primeiro a RAM salva;
  abaixo do mínimo, a interface não envia a consulta de FPS. Jogo sem curadoria
  informa ausência de ficha; uma estimativa continua identificada como parcial.
  Nenhum FPS é inventado, penalizado ou corrigido por capacidade de RAM.
- O botão Testar build do editor aguarda o salvamento pendente antes de abrir os testes.
  Trocar jogo limpa/cancela a verificação anterior; fechar/trocar tipo de teste
  aborta a consulta. Erro na FPSHQ preserva os requisitos já apresentados.
- Os resultados mantêm `escopo: parcial`, `requisitosVerificados: false` e
  `fpsValidado: false`. CPU/GPU, VRAM, recursos, SO e armazenamento não foram
  aprovados. A antiga rota `/benchmark/requisitos` permanece para o laboratório.
- Integração dos testes com a main: considerar token CSRF nas alterações de budget,
  remoção do GET global de usuários e manifesto de imagens inicialmente vazio;
  restaurados os rótulos acessíveis dos novos botões de confirmar identidade.
- Validação: 301 testes Node, 396 testes Python (+4 subtestes) e 53 verificações
  Chrome com API simulada em 320×800, 768×1024 e 1440×900. Inclui RAM abaixo do mínimo,
  kits/múltiplos modelos, propriedade, cancelamento, ausência de requisitos e
  indisponibilidade de FPS. Os testes usam SQLite temporário, sem LLM nem scraping.

#### Próxima etapa de compatibilidade física

A inspeção dos modelos Python confirma: `Gabinete` já possui limites de comprimento
da GPU e altura do cooler, formatos de placa-mãe, slots, baias e fans inclusas.
`PlacaVideo` ainda não possui `comprimento_mm`, `altura_mm` ou `espessura_mm`;
`AirCooler` possui somente `dimensoes` numérico legado, sem eixo explícito;
não é uma altura confiável para todos os modelos. O complemento técnico acima
fornece `altura_mm` apenas quando o modelo exato foi revisado.
`WaterCooler` informa o tamanho nominal do radiador, mas não sua espessura real;
faltam posições/encaixes compartilhados no gabinete. `Fonte` só informa formato
e potência; `PlacaMae` não possui quantidade de portas SATA no modelo atual.

Começar pelo comprimento real da GPU e altura real do air cooler, com unidades em mm,
fonte oficial e modelo/revisão exatos. Depois cadastrar GPU/PSU/baias, espaço de
conectores e posições/tamanhos de fans e radiadores, incluindo interferências.
As regras básicas já existem, mas dados ausentes permanecem não verificados.
Três fans de 120 mm não confirmam, sozinhas, espaço para um radiador de 360 mm.

### Busca de melhorias e responsividade — 21/10/2026

- **Dropdowns de peças:** cada categoria do modal usa `details/summary` animado,
  inicialmente recolhido, com contagem de opções e chevron Lottie. Uma seleção
  validada fecha somente seu dropdown e mantém modelo/preço no resumo. Reabrir
  permite substituir a escolha; confirmação final da build continua separada.
  Alterar orçamento ou outra categoria preserva os dropdowns abertos/fechados.
  Desmarcar uma categoria limpa sua seleção e estado; falhas não fecham o grupo.
  O fechamento devolve foco ao summary, mantendo teclado e área visível acessíveis.
  Validação: 292 testes Node e 161 verificações Chrome com API simulada em
  320×900, 768×1024, 1440×900 e 844×390, com/sem animações. Inclui substituição,
  remoção, orçamento insuficiente, rejeição de downgrade e salvamento confirmado.

- **Checkboxes:** o modal e o laboratório usam `iconeAnimado("checkbox")` e o
  controlador compartilhado. O input nativo continua acessível e ocupa todo o label;
  o Lottie fica com 1,5 rem. Ao marcar, traço em `--cor-p1` e preenchimento em
  `--cor-p6`, sem alterar o JSON ou as cores de outras áreas. Estado inicial,
  animação reversa e instância preservados nas atualizações. Sem Lottie ou com
  movimento reduzido, permanece o check estático com foco de teclado em azul primário.
  Validação: 289 testes Node e 90 verificações Chrome em 320/768/1440 px, com
  animação normal, movimento reduzido e CDN bloqueado; inclui o laboratório.

- **Filtro contra trocas inferiores:** `build/validar-melhoria.js` é compartilhado
  pelo modal real e pelo laboratório. A regra filtra as sugestões e é reexecutada
  ao selecionar/simular e imediatamente antes de confirmar, sem inferir desempenho
  pelo preço, nome, geração, GHz, núcleos, VRAM ou potência da fonte.
- RAM preserva capacidade total e número total de pentes, geração DDR, frequência
  e latência CAS relativa à frequência. SSD/HD preservam a capacidade total dos
  itens substituídos; SSD compara leitura/gravação e HD compara RPM/cache. Para
  modelos mistos, preserva o melhor valor informado de cada velocidade/latência,
  além da capacidade somada. Isto é um filtro das métricas disponíveis, não uma
  previsão de FPS, IOPS ou desempenho em qualquer carga.
- Peça própria sem identificação, quantidade inválida, medida ausente ou categoria
  sem critérios suficientes não é aprovada por suposição. O catálogo atual não
  fornece benchmarks comparáveis de CPU/GPU: essas substituições ficam bloqueadas,
  assim como as demais categorias sem critérios confiáveis. Uma GPU dedicada também
  não é presumida superior ao vídeo integrado. Adições em categorias vazias seguem
  as regras de orçamento/compatibilidade; repetir modelo atual não é upgrade.
- A montagem manual continua livre para escolher peças compatíveis. A política é
  da busca de melhorias no frontend, não uma autorização de segurança do servidor.
  Ainda falta definir e integrar dados de desempenho/qualidade por categoria e
  revalidá-los em um fluxo de melhorias no Python. Não são feitas consultas de
  benchmark em massa ou criados rankings fictícios.
- Validação do filtro: 287 testes Node, incluindo 57 casos do módulo e integração,
  e 43 verificações Chrome com API simulada em 320/768/1440 px. Seleção forjada de
  downgrade rejeitada, opções válidas salvas e mesma política no menu do card.

- `build/melhorias.js` separa as sugestões e a prévia em duas colunas no desktop.
  Até 900 px, usa abas **Escolher peças** e **Revisar trocas**, com contador,
  navegação pelas setas/Home/End e foco preservado após selecionar/remover peças.
- O seletor recolhível inclui todas as categorias, sem ocupar a tela inteira de
  início. Os cards mostram foto/alternativa neutra, modelo, preço e seleção. A ordem
  é explicitamente por preço, não uma promessa de ganho de desempenho.
- A revisão mostra todas as peças/quantidades antigas da categoria, a nova unidade
  ou kit, custo das compras e saldo do budget combinado. O comparativo do total
  fica recolhido. Dicas de conferência são azuis; avisos reais e erros têm tons próprios.
  RAM/discos/fans continuam substituindo a categoria por uma unidade/kit, como
  informado na interface; quantidades adicionais são ajustadas no editor.
- `build/melhorias.css` e `responsividades/r-melhorias.css` mantêm cabeçalho e
  confirmação visíveis e a rolagem dentro da área ativa. Celulares usam tela cheia,
  com safe areas; tablets, paisagem e monitores largos têm adaptações próprias.
  VisualViewport acompanha teclado/área visível. Texto grande ou altura extrema
  habilitam rolagem do diálogo, evitando conteúdo inalcançável. Observadores e
  listeners são removidos ao fechar. A posição não recebe transições de layout.
- O editor espera a conclusão do salvamento antes de fechar. Em caso de falha,
  restaura a base e mantém as escolhas para tentar novamente. Escape, fundo e
  fechamento ficam bloqueados durante o envio. Cancelar não altera a build. Após
  aplicar, o foco retorna ao novo botão do editor ou menu do card atualizado.
- A altura real do resumo do editor ajusta seu limite sticky, permitindo alcançar
  **Buscar melhorias** mesmo quando o conteúdo é maior que a viewport. O observer
  é reconectado no retorno pelo histórico com cache de página.
- Menus dos cards são preparados como popovers já na renderização. Antes, o menu
  invisível ainda podia ampliar a área rolável; a primeira abertura retirava essa
  área, provocava um salto na página e o listener de scroll fechava o próprio menu.
- Validação: 230 testes Node e 403 verificações Chrome com API simulada. Matriz:
  320×568, 360×640, 390×844, 430×932, 540×720, 768×1024, 1024×768, 1280×800,
  1440×900, 1920×1080, 2560×1440, 844×390 e 667×375; texto a 200%, resize,
  teclado, orçamento insuficiente, seleção múltipla, cancelamento, falha/repetição
  e salvamento lento. Abertura pelo menu testada em 320/768/1440 px. Sem executar
  backend, migrar banco, consumir LLM ou alterar a API de desempenho.

### Comparação, modelos e revisão da geração — 21/10/2026

- Minhas builds destaca a comparação em um bloco próprio, liberado com pelo menos
  duas builds. O estado vazio fica centralizado com borda pontilhada e atalhos para
  criar uma montagem ou explorar modelos. Cada card mostra preço mesmo com descrição;
  totais incompletos são parciais e falta de cotação não vira produto gratuito.
- O editor usa o nome da build como título e oferece edição pelo lápis Lottie,
  mantendo o campo de detalhes sincronizado, o título da aba e o salvamento da conta.
  Nome vazio e build trancada não podem ser salvos por esse controle.
- São 16 modelos sem periféricos. A vitrine usa ordem crescente de preços disponíveis,
  deixando modelos totalmente sem cotação ao final. Modelos incompletos continuam
  identificados como parciais; a ordem não transforma subtotal em cotação completa.
- `build/comparacao-renderizacao.js` reutiliza o cliente Python de Blender. A consulta
  é explícita, por CPU ou GPU, deduplica hardware repetido e mantém cache só no modal.
  Trocar o tipo, mudar as builds ou fechar a comparação cancela a consulta em curso.
  O destaque exige resultado de todas as builds e mesma versão/tipo/método; empate
  é preservado e ausência de modelo/dados não vira zero. As pontuações de CPU/GPU
  nunca são somadas nem apresentadas como teste do PC completo.
- `CriarBuildService` solicita uma revisão quando o retorno da LLM é inválido:
  JSON/formato, componentes obrigatórios (inclusive GPU quando necessária), IDs,
  quantidades, preços, estoque, rede, orçamento e conflitos técnicos conhecidos.
  A revisão recebe o diagnóstico e as regras originais e deve devolver a build inteira.
  Há no máximo uma correção, com rechecagem de quota antes dela e validação completa
  antes de persistir. O fallback de transporte já existente não abre outro ciclo de
  correção: são no máximo três chamadas na requisição combinada, sem novos provedores.
- `LLMService` valida a conclusão e estrutura do retorno conforme o
  [contrato do Gemini](https://ai.google.dev/api/generate-content), concatena partes
  textuais sem pensamentos e não transforma resposta truncada/vazia em build.
  Falha após a revisão retorna `502 / geracao-invalida`; timeout, indisponibilidade e
  cota têm códigos próprios. `Retry-After` só é repassado quando informado e válido.
  Não é possível garantir uma build válida com qualquer orçamento/catálogo.
- Ações do menu verificadas: benchmark, melhorias, definir/remover setup atual,
  trancar/destrancar, visibilidade, detalhes, duplicar, copiar link, JSON, CSV e excluir.
  Tranca bloqueia detalhes, visibilidade e exclusão; cópia respeita quota/e-mail.
  O link público é copiado, mas a regra atual do frontend ainda exige login para
  visualizá-lo. Não foi criada exceção à política de páginas privadas nesta rodada.
- Validação: 221 testes Node, 277 testes Python (+4 subtestes) e 77 verificações
  em Chrome, em 320/768/1440 px. LLM, transporte e consultas Blender simulados;
  bancos SQLite temporários para as rotas. Sem executar `app.py`, migrações,
  acessar o banco real, consumir a LLM real ou habilitar a HowManyFPS.

### Imagens, navegação e resumo do perfil — 21/10/2026

- O catálogo da conta preserva a imagem recebida da API. Quando ela está vazia,
  `build/imagens-produtos.js` consulta o manifesto local por `part_number` exato,
  sem associar fotos por semelhança de nome ou por IDs de outro banco. O catálogo
  demonstrativo reutiliza o mesmo carregamento. Os caminhos são resolvidos pelo
  módulo, tanto em `pages/` quanto no laboratório; fotos quebradas têm alternativa
  neutra, sem impedir a escolha da peça. Os 750 arquivos do manifesto foram conferidos.
- O hamburger volta a exibir setas Lottie à direita e inclui **Minhas builds** para
  usuários autenticados. O perfil mantém seus ícones, sem setas duplicadas.
- Configurações consulta `GET /build/` para mostrar a quantidade real de builds
  salvas. Falha de consulta aparece como indisponibilidade, nunca como zero fictício.
  O novo pill de budget mostra o valor salvo na conta e só muda depois da confirmação
  do salvamento; ausência, zero e falha são estados distintos. Retorno pelo histórico
  com cache de página revalida os dados.
- Checkbox Lottie do budget, ícone do título Perfil e ícones/textos do menu do perfil
  ficam centralizados verticalmente, incluindo textos quebrados no celular.
- Validação: 215 testes Node e 90 verificações em Chrome, em 320/768/1440 px,
  com catálogo/listagem/salvamento simulados, fotos locais reais, fotos ausentes ou
  quebradas, falhas de API, usuário visitante e animações. Sem iniciar `app.py`,
  consultar o banco real ou executar migrações.

### Budget manual e informação não verificada — 20/10/2026

- A criação manual omite `orcamento` quando deve usar o padrão da conta. O Python
  lê o budget do proprietário autenticado somente com `usar_budget=true` e valor
  positivo. `orcamento:null` explícito mantém a montagem sem teto; valores explícitos,
  importações, duplicações e builds existentes não são sobrescritos pela preferência.
- `AvaliarCompatibilidadeService` consulta as peças por IDs nos modelos atuais,
  sem nova coleta ou migração. As respostas de criação, edição, listagem e leitura
  incluem `compatibilidade`: `incompativel`, `nao_verificado` ou `sem_conflitos`.
  Cada regra também tem seu resultado; uma regra aprovada não aprova toda a montagem.
  O diagnóstico é calculado, não aceito do frontend nem armazenado no estado editável.
- O serviço identifica conflitos demonstráveis com os dados disponíveis (socket,
  DDR, pentes/slots/capacidade, formatos, conexões e potência), sem rejeitar rascunhos.
  Medida ausente/zero, peça própria não identificada, BIOS, QVL, conectores, baias,
  interferências e distribuição detalhada de fans/radiadores ficam não verificados.
  `dimensoes` ambíguo não vira altura do cooler; suporte genérico a water cooler
  não equivale a suporte a 360 mm. A validação completa e o bloqueio de geração
  tecnicamente inválida continuam pendentes; isto não homologa a saída da LLM.
- O editor mostra a avaliação no popover. Após salvar, atualiza somente o diagnóstico
  se os componentes ainda forem os mesmos da requisição, sem recriar os Lotties.
  Alterações locais sem retorno do Python não recebem aprovação automática.
- Como obter as especificações: usar a categoria/ID para carregar o registro e
  `Peca.to_catalogo()`. O contrato atual já fornece `soquete`, `socket`, DDR e alguns
  limites. Conferir os dados já coletados antes de cadastrar o que falta, mantendo
  nomes de campo, unidades (mm, W, GB) e referência técnica por modelo/part number.
  Para completar medidas, preferir manual/ficha do fabricante. Falta de informação
  permanece explícita; nunca inferir dimensões do nome ou do tamanho externo da caixa.
  Não foi executada atualização de catálogo, banco ou modelo nesta rodada.
- Controle de pausa removido da home e do menu. Vídeos decorativos não ficam em
  loop e reproduzem no máximo cinco segundos; movimento reduzido/economia de dados
  mantêm o poster. O loader não foi alterado.
- “Mais vendida” removida das sugestões e do laboratório; não há fonte de vendas
  confiável no escopo atual. Melhor preço continua disponível.
- FPSHQ: alguns probes retornaram HTTP 200, mas consultas seguintes (inclusive pelo
  serviço Python e por HTTP/1.1/2) expiraram sem corpo. Não foi validado nesta rodada
  um resultado normalizado real nem demonstrada recuperação estável. Sem trocar CPU,
  inventar FPS, relaxar TLS ou repetir automaticamente. Cache de reserva tem aviso
  visível e data; matriz aceita rótulo `4k` ou `4K` sem preencher presets ausentes.
  Validação: 176 testes JavaScript, 109 Python (+4 subtestes) e 91 checks de navegador
  com API simulada. Consultas públicas reais foram somente de leitura; nenhuma LLM
  paga, execução do `app.py` ou acesso ao banco real foi usado nesses testes.

### Atualização de criação, orçamento e menus — 20/10/2026

- Visitantes acessam apenas início, termos, sobre, contato, login/cadastro,
  recuperação de conta e erro. Páginas internas são marcadas com `data-private-page`,
  ficam ocultas/inertes até confirmar a sessão e redirecionam ao login também em
  caso de falha de rede. A guarda de UI não substitui `login_required` no Python:
  o Live Server continua servindo HTML estático, sem dados privados embutidos.
- `Testar build` primeiro permite escolher jogos/FPSHQ ou renderização/Blender.
  Trocar de modo ou fechar o modal cancela a consulta do painel anterior.
  `/benchmark/blender` exige login e consulta o JSON público oficial, com cache
  de uma hora e limites locais. Filtra o nome exato, tipo, versão e método;
  mostra mediana em amostras/min e número de resultados, nunca FPS ou tempo garantido.
  A fonte pode agregar variantes de VRAM sob um mesmo nome. A integração com
  Blender foi validada por consulta pública de CPU e por testes isolados. O prefixo
  Intel `12th Gen` e marcas `(R)/(TM)` são normalizados sem remover o sufixo do SKU;
  isso corrige a consulta de `i3-12100F`. Modelo realmente ausente continua sendo 422.
- Dez modelos sem periféricos cobrem estudos, produtividade, programação, jogos,
  criação e Blender. A vitrine usa os preços/IDs do catálogo da conta; o JSON local
  só ajuda a resolver referências já cadastradas. Não cria peças próprias fictícias
  quando falta um produto: permite copiar como base editável e sinaliza a pendência
  no editor. Cartões compactos não expandem peças; a consulta fica dentro da build.
  Preço zero/ausente é mostrado como preço a consultar, não como produto gratuito.
  Curadoria gerenciável
  no servidor e atualização contínua de preços continuam pendentes.

- `BuildSalva.criar_limitada` serializa a escrita por usuário no banco e limita a
  três builds. Criação manual, importação, modelos, duplicação e geração usam esse
  ponto; a LLM recebe uma checagem antecipada e outra ao persistir. Não se mantém
  lock durante a chamada externa. Resultado gerado e estado são salvos na mesma
  transação; montagens com peças próprias usam a mesma proteção ao persistir o estado.
  A quota responde `409 / codigo: limite-builds`, sem apagar dados antigos.
  O mesmo ponto exige e-mail verificado (`403 / codigo: email-nao-verificado`),
  inclusive em requisições diretas. O formulário verifica ambas as condições antes
  de liberar a página, com nova validação antes de gerar.
- O formulário usa tetos **Até**, slider de R$ 100 em R$ 100 e entrada com centavos.
  Agora tem cinco etapas: objetivo, orçamento, peças do PC, periféricos e conexão.
  A etapa de periféricos distingue não incluir, comprar todos ou reaproveitar alguns;
  os já possuídos exigem modelo e usam o checkbox Lottie compartilhado.
  A porcentagem de 1–99% define um **teto separado** para os periféricos; o restante
  é o teto do PC, incluindo acessórios de rede. `percentual_perifericos` vai no pedido
  e `percentualPerifericos` no estado. O Python filtra o catálogo por esses limites
  e valida os dois subtotais (preço real × quantidade) e a presença dos itens
  solicitados antes de salvar. A sobra permanece com o usuário: não passa de um teto
  ao outro. Não inventa produtos nem força gastar a reserva integralmente.
- O formulário envia `pecas_proprias`, rede e teto percentual para a geração pela LLM,
  que completa apenas as categorias ainda não possuídas. O resultado abre no editor
  pelo `build_id`; mantém os Lotties, controles e feedback de erro da interface.
  Webcam/microfone próprios são preservados em `pecasExtras`. Identificação completa
  dos modelos e compatibilidade definitiva das peças próprias continuam pendentes.
- Frases na espera mudam a cada quatro segundos, sem porcentagem ou etapas reais.
  Erro preserva respostas e permite repetir/revisar. A altura do formulário acompanha
  o conteúdo. Somente as listas longas de peças próprias/periféricos possuem rolagem
  interna; orçamento e rede continuam sem recorte interno.
- Diagnóstico de FPS no laboratório: `experimentos/benchmark-diagnostico.js` permite
  escolher o cliente direto JS ou o cliente Python, sem requisição ao trocar o modo.
  O direto omite cookies, não reutiliza cache local e registra HTTP, tempo, redirecionamento
  e falha de validação; `pagehide` cancela a consulta. Produção permanece no backend.
  Na verificação real de 21/10/2026, ambos deram timeout sem resposta HTTP: Chrome
  após 20 s e Python atual após cerca de 10 s. O 504 é o mapeamento da BOOSTio,
  não um status recebido do provedor; esse resultado não identifica uma causa global.
- `GET /benchmark/requisitos?game=...&ram_gb=...` segue Blueprint → service e exige
  sessão. Curadoria JSON dos cinco jogos com links oficiais e data de revisão, sem
  scraping em cada consulta nem dependência da FPSHQ. A prévia fica em `testes.html`.
  Verifica só capacidade de RAM informada; sempre retorna `escopo: parcial`,
  `requisitosVerificados: false` e `fpsValidado: false`. Recomendado ausente fica null;
  CPU/GPU, VRAM, sistema e espaço livre não são inferidos por nomes ou pontuações.
  Ainda falta vincular a avaliação ao hardware real da build e à interface de produção.
- `components/number-stepper.js` mantém inputs nativos com botões explícitos de
  aumentar/diminuir: orçamento de R$ 100 em R$ 100 sem perder centavos; porcentagem e
  rede seguem seus passos e limites. Os controles preservam Tab/Enter e não recriam
  os campos de rede durante a edição. Os Lotties de navegação são iniciados após
  renderizar cada etapa; Voltar usa a orientação inversa. Font Awesome não é necessário
  no formulário. Erros ocupam uma única célula do grid e ficam centralizados; revisar
  o orçamento restaura a disposição normal sem perder as respostas.
  Regressões em `frontend/tests/formulario-ui.test.mjs`; a interface foi conferida
  em celular, tablet, desktop e paisagem com respostas simuladas, sem iniciar o Flask
  nem acessar/migrar o banco real.
- Os menus da conta renderizam `iconeAnimado`, carregam os JSONs ao remover `inert`
  na abertura e usam Popover API quando disponível para escapar do recorte/glass
  do card. Menu fecha por Escape, clique externo, rolagem da página ou resize.
- FPSHQ: diagnóstico externo terminou em timeout após conexão/TLS. Falhas TLS/rede
  têm códigos próprios; timeout é 504 e indisponibilidade HTTP do provedor é 503.
  A pausa retorna `Retry-After` (também após falha de conexão), sem repetição automática.
  Cache válido continua disponível. Não foi demonstrada recuperação do provedor.
- O hamburger reúne Início, Criar build, Termos e Sobre, sem setas nem repetir
  Builds/Configurações/Sair do perfil. O controle de animações da home foi removido
  na atualização acima. A escolha de criação destaca o formulário à
  esquerda; montagem manual fica à direita.
- Busca de melhorias permite selecionar todas as categorias do catálogo. Os
  resultados e a prévia rolam em áreas próprias, mantendo ações do diálogo visíveis.
  O catálogo informa vídeo integrado no editor. Indicador de build incompleta usa
  amarelo, enquanto o preenchimento da barra de progresso permanece azul.
- Falhas de conexão ganham mensagem de internet indisponível quando confirmada
  por `navigator.onLine`; falha genérica de rede/servidor não é confundida com 5xx
  do provedor de benchmark. Modal de código e resultados Blender usam a tipografia
  e cores do site; checkbox de budget do perfil usa o Lottie compartilhado.

Validação desta rodada: 173 testes JavaScript, 86 testes Python (+ 4 subtestes)
e 184 verificações de navegador com respostas controladas. Incluem acesso/quota,
cinco etapas, posse de periféricos, copiar modelos, selecionar o benchmark e aplicar
SSD/fonte/monitor juntos. Conferência visual em celular, tablet, desktop e paisagem.
Nenhuma migração, execução do `app.py`, geração paga pela LLM ou atualização de preços.

Os trechos históricos abaixo sobre quota apenas local e ausência de CRUD não
descrevem os fluxos atuais da conta; consultar este bloco e o README.

Abra pelo Live Server:

- `frontend/pages/configuracao-build.html`: cria uma montagem vazia na conta, com sessão.
- `frontend/pages/configuracao-build.html?build_id=s-ID`: edita uma montagem da conta.
- `frontend/pages/configuracao-build.html?id=build-demo-1`: configuração de exemplo.
- `frontend/pages/pecas.html?categoria=processador`: catálogo por categoria.
- `frontend/pages/peca.html?id=SEED-CPU-02`: ficha técnica e lojas.
- `frontend/pages/configuracoes-prontas.html`: modelos demonstrativos e cópia editável.
- `frontend/pages/sobre.html`: apresentação da BOOSTio, proposta, ferramentas e estágio do projeto.
- `frontend/testes.html`: demonstração que usa o mesmo menu hamburger das demais páginas.

O catálogo JSON existente reúne as 750 peças já coletadas para o projeto e continua
nos modelos/fluxos legados. A montagem da conta busca o catálogo do backend. Essa
integração não equivale a monitoramento atualizado das ofertas das três lojas.
Quando a seed mudar, o JSON não se atualiza sozinho.

## Como funciona o blur no scroll

`frontend/js/components/scroll-reveal.js` usa um IntersectionObserver.
Quando 12% do elemento passa a ser visível, ele recebe `is-visible`.
O `rootMargin: "60px 0px -32px 0px"` ajusta a área em que a entrada é detectada.
A classe é retirada ao sair, portanto a animação pode repetir.

O CSS em `frontend/styles/componentes/scroll-reveal.css` controla:

- `--reveal-distance: 42px`: deslocamento vertical inicial.
- `--reveal-blur: 6px`: desfoque inicial.
- `--reveal-scale: 0.985`: escala inicial.
- `--reveal-duration: 0.75s`: duração de opacidade e blur.
- `--reveal-move-duration: 0.9s`: duração do movimento.

Para animar um novo elemento, adicione `data-reveal` ao HTML.
Para atrasar sua entrada, use `data-reveal-delay="80ms"`.
Os cards de serviço usam 0, 80 e 160 ms.
Para revelar só uma vez, dentro do callback mantenha a classe e chame
`observer.unobserve(target)` quando `isIntersecting` for verdadeiro.

É uma animação disparada pela visibilidade; o blur não varia continuamente
com a velocidade do scroll. As opções de movimento reduzido do sistema são respeitadas.
Os conteúdos continuam visíveis se o JavaScript ou o observer não estiverem disponíveis.
Na home, o reveal é aplicado ao card inteiro para manter texto e fundo juntos.
O footer e os cards/sections das demais páginas recebem o mesmo reveal automaticamente
após o loading. Um MutationObserver registra também cards criados pelo JavaScript,
sem duplicar observers; a área principal da home continua sem blur inicial.

## Estado local e pontos de integração

`js/build/catalogo.js` centraliza o carregamento do catálogo e as informações das lojas.
A futura API pode substituir `carregarCatalogo()`, mantendo o mesmo formato:
id estável, categoria, imagem, preço, consumo e campos técnicos da peça.
O campo `imagem` já é suportado; ausências exibem um placeholder.

`js/build/estado.js` guarda os rascunhos e a lista demonstrativa de builds no localStorage.
Salvar no perfil nesta versão significa salvar neste navegador. Não há gravação na conta
do Flask nem sincronização entre dispositivos. Dados do formulário entram como peças
próprias sem preço; o usuário precisa selecionar o modelo para a validação técnica.
`js/build/autosalvar.js` grava cada alteração válida na lista local, inclusive seleções
do catálogo e da ficha da peça. Abrir o editor sem editar não cria uma build salva.
Nome vazio ou quota completa preservam somente o rascunho e exibem a pendência;
build trancada não pode ser sobrescrita. O botão **Salvar build e voltar** continua
disponível para concluir e retornar à lista, sem ser necessário para persistir cada edição.

Links compartilhados carregam a configuração por IDs de catálogo e quantidades, e abrem
uma cópia. A visibilidade e a tranca são controles locais de interface, não autorização
do servidor. Links já enviados não podem ser revogados por esse protótipo.

RAM é uma lista em `componentes.memoria_ram`; o formato antigo com um objeto é migrado
automaticamente. Cada entrada tem `id` e `quantidade` de kits. Todos os módulos de todos
os kits contam nos slots e na capacidade máxima da placa-mãe. Novos modelos precisam
ter o mesmo DDR e frequência; misturar marcas/modelos gera aviso de estabilidade.
Duplicação e remoção são individuais. SSD, HD e fan também são listas de modelos e
quantidades; objetos antigos são migrados sem perder os dados. Para trocar outras peças,
remova a atual primeiro. A duplicação soma preço, consumo e capacidade; diminuir libera
conexões sem remover os demais modelos. Rascunhos, JSON e links preservam quantidades.

`js/build/compatibilidade.js` verifica socket, DDR, slots, capacidade, formato do gabinete,
altura do air cooler, comprimento da GPU, radiadores, diâmetro/quantidade de fans,
slots M.2, portas SATA compartilhadas por HD/SSD e potência da fonte.
Dados genéricos como “Intel/AMD” produzem dica para conferir o socket no fabricante.
BIOS, conectores, disposição dos encaixes e disponibilidade não são plenamente validados.
Medidas ausentes produzem dicas azuis, nunca um encaixe confirmado. Novas unidades de discos
exigem uma placa identificada com limite conhecido; não se presume que uma placa tenha
quatro portas SATA. Trocar a placa ou o gabinete também revalida as peças já selecionadas.
O consumo exclui monitor e periféricos externos e é apenas uma estimativa da seed.
Não há potência recomendada. Fonte abaixo do consumo é erro; igual ao consumo gera aviso
de ausência de margem. Fans são obrigatórias. Air cooler e water cooler ficam em uma categoria;
cooler separado é obrigatório somente quando o processador não inclui cooler.
Periféricos são opcionais e podem ser ativados pelo checkbox do editor.
O checkbox mantém o mesmo elemento e a mesma instância Lottie durante a atualização
dos cards, permitindo concluir a animação nos dois sentidos.
SSD e HD aparecem juntos em **SSD / HD**, um grupo obrigatório: basta um dos dois.
As peças continuam armazenadas como `ssd` e `hd`, preservando rascunhos existentes.
O contador de armazenamento mostra unidades de SSD/HD e conexões M.2/SATA ocupadas.
Placa de vídeo é obrigatória quando o processador selecionado não tem vídeo integrado;
enquanto faltar, o status da build permanece incompleto.
O catálogo é filtrado automaticamente pelas verificações quando a build já possui peças.
O botão da página de produto também revalida a seleção antes de adicionar.

### Campos técnicos para a futura API

Em `js/build/hardware.js`, campos numéricos nulos são desconhecidos, não zero.

- Placa-mãe: `quantidade_slots_m2`, `quantidade_portas_sata`,
  `quantidade_slots_m2_sata` e `portas_sata_desativadas_por_m2_sata`.
- GPU: `comprimento_mm`, `altura_mm`, `espessura_mm`, `slots_ocupados`;
  air cooler: `altura_mm`. O campo legado `dimensoes` não vira altura automaticamente.
- Gabinete: `tamanho_max_gpu_mm`, `tamanho_max_cooler_mm`,
  `radiadores_suportados_mm: [120, 240, 360]`, `tamanhos_fan_suportados_mm: [120, 140]`,
  `quantidade_max_fans` e `fans_inclusos`.
- Water cooler: `tamanho_radiador_mm`, `quantidade_fans`, `tamanho_fan_mm`; fan: `tamanho_mm`, `quantidade`
  (unidades físicas por kit, multiplicadas pela quantidade de kits na build).

Esses arrays são exemplos de contrato, não medidas de um gabinete real. Radiador de
360 mm precisa estar listado nos tamanhos suportados. Três fans de 120 mm continuam
três unidades de 120 mm, não uma fan de 360 mm. A contagem considera as fans inclusas
e as do radiador como instaladas; modelos com distribuição não informada precisam
de conferência para encaixes compartilhados. Não existe um seletor de posição física ainda.
Muitos modelos ainda não possuem essas medidas. O complemento versionado acima
adiciona encaixes apenas aos modelos revisados, sem generalizar os limites.

#### Pendência: encaixe físico completo do gabinete

`validarEncaixe()` já compara no frontend comprimento da GPU, altura do air cooler,
tamanho nominal de radiador e tamanho/quantidade de fans, e a avaliação confere o
formato da placa-mãe. Isso não equivale à confirmação de uma montagem física completa.
A integração atual também revalida no Python. Falta ampliar dados confiáveis e
interferências com medidas do modelo/revisão corretos.

O gabinete precisa informar limites internos por configuração e posição: GPU com e
sem radiador frontal; altura/espessura da GPU e espaço dos conectores; radiador +
fans no topo/frente e suas interferências com placa-mãe/RAM; altura do air cooler;
formato/comprimento da fonte e baias de discos. Fans e radiadores podem disputar as
mesmas posições, e fans inclusas podem ser removidas ou substituídas; a configuração
instalada deve ser explícita antes de confirmar o encaixe. Dimensões externas do
gabinete e o tamanho nominal de um radiador, isoladamente, não bastam.

Retornar distinção entre encaixe confirmado com os dados conhecidos, incompatível
e não verificado por falta de dados. Não inferir medidas pelo nome comercial nem
transformar dado ausente em confirmação. Essa checagem é independente do benchmark
de jogos e deve ser refeita ao trocar o gabinete ou qualquer peça que afete o espaço.

O complemento exclusivo do catálogo demonstrativo usa as fichas de
[ASUS PRIME A520M-K](https://www.asus.com/motherboards-components/motherboards/prime/prime-a520m-k/techspec/),
[GIGABYTE B550M DS3H rev. 1.0/1.1/1.2/1.3](https://www.gigabyte.com/Motherboard/B550M-DS3H-rev-10-11-12-13/sp)
e [MSI PRO B760M-P](https://us.msi.com/Motherboard/PRO-B760M-P/Specification).
Esses três modelos têm quatro portas SATA; as quantidades M.2 são respectivamente
uma, duas e duas. Na MSI, M.2 SATA desativa SATA5. Os links de lojas da seed podem
apontar para outras variantes; este complemento usa o nome/modelo da demonstração,
não o anúncio, e não deve ser aplicado a outras revisões sem conferência.

Nenhum arquivo Python foi alterado. O backend atual **não** executa estas validações
nem o limite de três builds; o modelo possui quantidades, mas não há rotas de builds
registradas em `app.py`. O front continua com catálogo demonstrativo e localStorage.
Ao integrar, o servidor deve revalidar estoque, compatibilidade, medidas, quantidades,
tranca, visibilidade, propriedade da build e quota. O modelo atual também só armazena
um ID por categoria; vários modelos de RAM/SSD/HD/fan precisam de um contrato adequado.

KaBuM usa os links já existentes. Pichau abre buscas, claramente rotuladas,
até haver ofertas diretas cadastradas. Não são inventados preços de cada loja.
Ofertas reais são independentes do preço demonstrativo da seed:

```json
{
  "ofertas": [
    {"loja": "kabum", "preco": 1200, "url": "https://www.kabum.com.br/produto/ID", "atualizadoEm": "2026-09-28T12:00:00Z"},
    {"loja": "pichau", "preco": 1190, "url": "https://www.pichau.com.br/produto"}
  ]
}
```

Esses valores são apenas exemplos do contrato, não cotações. Sem o campo `ofertas`,
cada loja exibe “Preço ainda não cadastrado”. Os arquivos locais em `frontend/svgs` são:
`kabum-logo.svg` e `pichau.png`. As marcas ficam em escala de cinza;
se uma imagem falhar, o nome da loja continua visível.

## Sistema visual e transições

`styles/utilitarios/tipografia.css` foi restaurado integralmente do commit
[`789d641`](https://github.com/trvzera/BOOSTio/commit/789d6418e1a5118890e4f5675204e4cdaac3219d),
confirmado como o último commit de `main`. Também foram restauradas as regras
tipográficas responsivas e removidas as sobrescritas globais de pesos e entrelinhas.
As classes `font-1-*` usam Lexend e `font-2-*` usam Poppins. Os tokens dos componentes
novos ficam em `ui-system.css` e não substituem essa escala nas páginas existentes.
`cores.css` define
`--status-success`, `--status-warning` e `--status-error`; status também têm rótulos textuais.
Botões compartilham formato capsule, altura mínima, hover discreto e foco visível.
`componentes/ui-system.css` concilia os estilos antigos de cada página com esses tokens.

`js/components/ui.js` inicializa ícones via o controlador Lottie existente,
reproduz no hover/foco e reverte na saída. Plus, login rotacionado 90°, trash e cart
têm alternativas estáticas. Checkbox, hamburger e chevron refletem o estado do controle.
Na seleção de desempenho, `gamepad.json` identifica Jogos e `microchip.json`, Blender.
Na escolha de montagem, `handsparkle.json` identifica o formulário inteligente e
`normalhand.json`, a montagem manual. Os quatro usam o mesmo hover/foco com retorno,
sem loop/autoplay, preservam os rótulos dos controles e têm SVG estático para
movimento reduzido ou falha de carregamento. Selecionar um tipo não consulta a API.
O `arrow.json` original aponta na diagonal: a rotação de 45° aponta para a direita,
225° para a esquerda, 0° mantém a diagonal externa e −45° aponta para cima.
Ícones de elementos removidos são destruídos; falhas nas animações não bloqueiam os controles.
O ícone de Configurações (`user.json`) tem enquadramento próprio no renderer SVG
(`viewBoxSize`), pois a composição original 1000×1000 inclui margem vazia. Isso mantém
o tamanho visual dos demais ícones sem aumentar a linha do menu nem cortar o giro
da engrenagem. Hover e foco usam a cor primária; movimento reduzido ou falha no
carregamento preservam um símbolo estático de usuário com engrenagem. Não aplicar
`scale` no SVG: o transform inline gerado pelo Lottie pode sobrescrevê-lo.
O mesmo módulo adiciona logos sociais e tooltips a botões desabilitados, inclusive
em conteúdo dinâmico. Defina `data-disabled-reason` para informar um motivo contextual;
uma âncora focável permite ler a explicação pelo teclado sem habilitar a ação.

`componentes/feedback.css` padroniza a família Poppins nas mensagens de erro,
avisos, retornos de importação, perfil, catálogo, geração e benchmarks. Mantém a
escala de tamanhos das páginas e Lexend nos títulos, sem aplicar fontes a ícones.
As mensagens quebram IDs/textos longos; importação e falhas na lista de builds
identificam o estado por `data-tone`. IDs desconhecidos continuam bloqueados pela
validação local de arquivos: formatar o aviso não substitui peças nem altera o catálogo.
As fontes locais declaradas em `tipografia.css` são verificadas por testes de caminho
e cabeçalho WOFF2, além de carregamento e fonte efetivamente renderizada no Chrome.

O total da montagem e da build compartilhada exibe **Frete não incluído**, com
orientação para reservar parte do orçamento e conferir a entrega por CEP/loja.
O aviso também aparece em Comprar build. É informativo: não altera compatibilidade,
não inventa uma cotação, não soma frete ao preço das peças nem desconta uma reserva
automaticamente. Cálculo real de entrega depende das lojas e do endereço de destino.

`js/pages/loading.js` usa `sessionStorage["boostio:visita-iniciada"]`, não a conta.
Primeira visita da aba/sessão e toda entrada na home usam vídeo. A home sempre mantém 1×.
As demais páginas mostram um loading curto (linha animada sobre preto), espera mínima
de 320 ms e fade de 600 ms. O fluxo editor → catálogo → peça usa espera de 320 ms e
fade de 460 ms; com catálogo pronto, 160 ms e 360 ms. Links internos e botões desse fluxo
têm também fade preto de saída de 260 ms, sem afetar links externos ou âncoras da mesma página.
Retornos pelo histórico/bfcache reapresentam a transição curta; o fluxo de componentes
reabre o documento para ler o rascunho atualizado. Retornar à home recarrega o loading
completo. A tela curta nunca depende de o vídeo estar disponível.
O formulário tem espera mínima de 800 ms e fade de 700 ms, inclusive nas visitas seguintes.
A primeira visita continua usando o vídeo; movimento reduzido ignora a espera artificial.
Nesse fluxo, um vídeo inicial pode acelerar para 2.2× quando os dados já estiverem prontos;
as outras páginas não alteram sua velocidade.
Configurações aguardam a requisição inicial de perfil; catálogo/editor aguardam o JSON.
O vídeo não simula porcentagem de rede: a mudança de velocidade depende de tarefas reais.
Há limites de espera para evitar tela presa e suporte a movimento reduzido.
Para novas tarefas iniciais, use `acompanharCarregamento(promise)` de `page-loading.js`.
Ao salvar a build, a interface redireciona a `builds.html`, ainda com persistência local.

Depois da retirada do loading, `js/components/page-entry.js` anima os primeiros textos
visíveis, sem exigir scroll, **exceto na home**, onde essa entrada foi desativada.
O efeito durante a rolagem das outras seções da home continua independente.
Em `styles/componentes/page-entry.css`, altere o blur de
8px, a distância de 18px e a duração de 0.7s. A animação respeita movimento reduzido.
O overlay perde a captura de cliques ao começar o fade e é removido também por timeout,
sem depender exclusivamente de `transitionend`.

## Navegação e interatividade

`pages/sobre.html` substitui a antiga página de desenvolvedores. Apresenta a proposta
da BOOSTio, ferramentas de planejamento, origem do projeto e limites atuais, sem
perfis individuais ou promessas de integrações já concluídas. Os footers apontam para
**Conheça a BOOSTio**; a página usa navegação, loading, fontes, glass e reveal compartilhados.
`paginas/sobre.css` e `responsividades/r-sobre.css` cuidam do layout específico.

`js/header.js` renderiza a logo de 100px no topo esquerdo e o perfil no topo direito.
O perfil permanece disponível antes e depois do login; os seus links não usam setas.
O botão usa `profile.json` no tamanho original de 60px. Hover e foco abrem o dropdown;
clicar fixa o menu aberto. Uma ponte entre botão e painel evita fechar durante o movimento
do cursor, e Escape, clique fora ou um segundo clique fecham o menu.
O hamburger flutuante fica oculto até a autenticação. Em `testes.html`, o atributo
`data-menu-preview` permite verificar o hamburger mesmo sem login.
Os painéis usam glass, itens compactos, `inert` quando fechados, Escape e clique fora
para fechar. Abrir um painel fecha o outro. Navegações usam páginas; na home o menu
inclui também Sobre, Como funciona e Começar montagem, ligados às respectivas sections.
O editor tem um botão direto para voltar a Minhas builds, sem depender do histórico.
Minhas builds e Builds prontas compartilham um seletor de páginas com `aria-current`;
o comparador aparece apenas em Minhas builds. Os cards não têm ação de compra.
Em Minhas builds, **Criar build** abre um modal para escolher entre montagem manual
e formulário inteligente. A escolha fecha o modal antes da transição compartilhada.
O botão fica bloqueado quando a quota local de três builds está completa.

Nos cards de builds, o progresso permanece azul e a linha inferior exibe apenas
privacidade e data. Builds trancadas mostram um cadeado ao lado do nome e não
podem ser editadas nem deletadas até serem destrancadas.
A barra à esquerda do título fica azul sem pendências, amarela com aviso/incompletude
e vermelha com erro. Hover, foco ou toque mostram a lista de pendências; Escape fecha.
O editor usa o mesmo indicador. Criar, duplicar e importar ficam bloqueados na quota
completa, inclusive com uma explicação acessível. Importar lê JSON e CSV da BOOSTio,
valida o arquivo e abre uma prévia antes de criar uma cópia privada e destrancada.
O salvamento ainda é local, sem integração com o servidor.

### Recursos de planejamento e arquivos

`js/build/rede.js` mantém conexão, posse, velocidade e comprimento do cabo na quarta
etapa do formulário, sem campo de preço. `custoPrevisto` de arquivos v1 é aceito,
normalizado para `null` e nunca somado. Na build, **Incluir rede** mostra a categoria
**Wi-Fi / Rede** com adicionar/remover igual às outras peças. Os componentes usam
`cabo_rede` e `adaptador_wifi`; `incluirRede` e as respostas do formulário sobrevivem
à edição, duplicação, links e JSON/CSV. O catálogo demonstrativo ainda não possui
esses produtos e mostra um estado vazio explícito, sem inventar preço ou modelo.
Somente o preço de produtos cadastrados entra no total. Rede é opcional e não muda
a conclusão ou o consumo estimado do PC; conferir interfaces/roteador continua necessário.

O dropdown **Nome, descrição e orçamento** usa `components/animated-details.js`
para animar as duas direções e respeita movimento reduzido. Os Lotties `circledot`,
`magnifying` e `magic` usam o controlador compartilhado com hover/foco e reversão.
Na build definida como setup atual, circledot inicia no último frame e inverte
hover/saída; `aria-checked` informa o estado, atualizado ao escolher outra build.
O botão da principal mostra **Remover como setup atual** e desmarca a preferência,
sem excluir a build. As demais mostram **Definir como setup atual**, com ícone normal.
O menu de três pontos abre para baixo, ajustando a rolagem ao abrir se faltar espaço,
sem cobrir os controles flutuantes; sua lista tem rolagem própria e glass mais forte.

`js/build/planejamento.js` mantém o ID de setup atual neste navegador, mas recebe o
budget da conta apenas em memória. `js/conta/perfil.js` consulta `/auth/me` sem cache,
compartilha solicitações simultâneas e descarta respostas antigas após logout ou
salvamento. Formulário e editor aguardam essa consulta antes de aplicar a preferência;
sem sessão/conexão não reaproveitam o budget legado do localStorage.

`js/pages/budget-perfil.js` carrega valor e autorização e envia `PUT /usuarios/<id>/budget`
por `js/api/usuario/atualizarBudgetUsuario.js`. A interface só confirma após resposta
do servidor, permite tentar novamente em caso de falha e desativa consentimento sem
valor positivo. O Python valida sessão, dono, intervalo e centavos, seguindo
controller → service → modelo. O valor não aparece na listagem geral de usuários.

O formulário preenche o range quando a preferência está ativa; `build.orcamento`
permite ajustar o limite sem alterar o perfil. Rascunhos, builds já existentes e
orçamento escolhido no formulário prevalecem sobre a preferência. As builds e o
setup atual ainda não são sincronizados entre contas/dispositivos.

No SQLite existente, executar em `backend/`: `python -m flask --app app migrar-budget`.
`migrations/budget_usuario.py` cria backup e adiciona somente colunas ausentes em uma
transação, incluindo `login_google` para bancos antigos; nunca recria usuários.
Instalações novas recebem os campos por `db.create_all()`.

`js/build/arquivos.js` exporta JSON e CSV versionados (`boostio-build`, versão 1).
O CSV inclui metadados e uma linha por modelo com categoria, ID ou peça própria,
quantidade e nome. Arquivos têm limite de 1 MiB; a importação valida estrutura,
quantidades e IDs, sem confiar em preços/consumo enviados no arquivo. Gera novo UUID,
preserva planejamento e nunca reutiliza a visibilidade pública ou tranca da origem.

`js/build/comparacao.js` abre o comparador da lista real de builds locais.
`js/build/melhorias.js` monta uma prévia de trocas das categorias do catálogo dentro de um
budget combinado e somente altera a build após confirmação. Rankings de desempenho e de vendas aguardam
dados externos. `js/build/modelos.js` mantém exemplos versionados para a vitrine.

`js/build/acoes-build.js` compartilha os modais de compra e benchmark e o aviso sobre
lojas terceiras. O benchmark abre apenas com 100% das peças e sem erros; permite
escolher jogo, resolução e preset e consulta FPS pelo backend para modelos mapeados.
Comprar build, somente no editor, lista as lojas
e quantidades de cada peça, sem checkout nem abertura automática de múltiplas abas.

### Consulta de FPS — backend e interface compartilhada

Contrato atual conferido no [OpenAPI](https://fpshq.com/openapi.json), na
[documentação pública](https://fpshq.com/pt/api/) e em chamadas reais em 19/10/2026.
A rota é `GET /api/public/v1/fps`, com `game`, `gpu`, `cpu`, `res` e `preset`.
Não usar o contrato antigo `/api/v1/`. Os presets são `low`, `medium`, `high`, `ultra`;
resoluções: `1080p`, `1440p`, `4k`. Retorna `fps`, `low1`, `source` (`measured`/`model`),
`basis` (`measured`/`aggregate`/`model`), `confidence` e matriz 3×4.
Ausências e intervalos nulos não são zero. `verdict` tem base 1080p High, não se aplica
automaticamente à seleção do usuário. A origem de cada célula da matriz não é individualizada.

`GET /api/public/v1/games?q=<texto>` busca de 2 a 60 caracteres e retorna até dez jogos.
Foram encontrados Valorant, Counter-Strike 2 (`cs2`), Fortnite, Cyberpunk 2077 e Forza
Horizon 5, entre outros. Encontrar no catálogo não garante FPS para toda combinação.
Os cinco jogos padrão do laboratório, nesta ordem, são Valorant, Counter-Strike 2,
Fortnite, Cyberpunk 2077 e Red Dead Redemption 2. O último foi confirmado por consulta
direta a `/fps` com `game=red-dead-redemption-2`, apesar de a busca pelo nome completo
ter retornado lista vazia. Outros jogos continuam acessíveis pela busca.
Não há catálogo REST de CPUs listado neste OpenAPI; mapear componentes exatos sem
inventar slugs nem usar uma GPU dedicada como substituta de vídeo integrado.

O laboratório `testes.html` carrega `js/pages/test-benchmark.js`, que inicializa
`js/benchmark/interface.js` com a combinação fixa Ryzen 5 5600 + RTX 3060. O mesmo
controlador é usado pelo modal real de `js/build/acoes-build.js`, com as peças da build.
Ambos chamam `js/api/benchmark/consultarBenchmark.js` → `fetchComErro`, com cookies de
sessão. O cliente direto antigo em `js/experimentos/fpshq.js` não é carregado por essas
interfaces. Nada é consultado automaticamente ao abrir a página ou o modal.
Nas verificações houve respostas lentas/timeouts intermitentes; o cliente encerra a
espera após 20 segundos, sem retentativa automática nem FPS fictício. A resposta real
também foi recebida por fetch no navegador; isso não garante disponibilidade contínua.
Chamada real de Valorant, 1080p/High: 288 FPS, 1% low 261, source/basis `measured`.
São valores retornados naquele momento pelo provedor, não medidos pela BOOSTio e
não fixados como resultados no código. A combinação com CPU inexistente retornou 404.

O provedor declara uso gratuito sem chave, CORS e CC BY 4.0 com atribuição, além de
60 consultas/minuto e 10 mil/dia por IP. Antes de produção, centralizar cache e limites
no backend, validar cobertura/precisão e integrar as builds da conta. RAM, consumo
instantâneo e rede não são parâmetros desse endpoint; os avisos distinguem latência
de FPS. O recurso se chama **Desempenho esperado** e não promete medição ou precisão.
O modal agora consulta o Flask autenticado, que acessa a FPSHQ. As rotas e os serviços
novos estão documentados abaixo; não há alteração de modelos ou migração de banco.
No laboratório, a prévia da montagem fica recolhida e a área principal mostra apenas
hardware de referência, jogo, resolução e qualidade. A busca apresenta resultados
para seleção explícita, sem escolher automaticamente o primeiro. O aviso começa
oculto e aparece após selecionar o jogo ou receber seu resultado; detalhes de RAM,
rede e demais limitações ficam em uma seção expansível, sem remover as ressalvas.
`js/benchmark/view.js` monta a visualização compacta: **Comparar ajustes** fica visível e
permite alternar a qualidade e ver as três resoluções da matriz já recebida, sem
requisitar a API nem substituir os FPS do resultado principal. **Sobre os dados**
reúne origem, definição de 1% low e data. Cotas operacionais ficam apenas nesta
documentação, não no texto do resultado. Fonte e licença continuam visíveis.

O seletor **Interface de teste** alterna **Cards** (métricas lado a lado), **Painel**
(ajustes à esquerda e resultado em destaque à direita no desktop) e **Compacto**
(controles em uma faixa e métricas em linhas). As três variantes usam o mesmo DOM,
cliente e resposta: mudar o visual preserva jogo, ajustes, comparação aberta e dados,
sem consumir outra consulta. Em telas menores, o painel passa a uma coluna.
O seletor de variantes continua exclusivo do laboratório. O modal real usa Cards,
com métricas menores, controles mais curtos e sem repetição de avisos operacionais.

Os menus expansíveis usam `js/components/animated-details.js`: o JS mede a altura
natural e anima abertura/fechamento com Web Animations, mantendo `aria-expanded`.
Em `styles/componentes/benchmark.css`, `.fpshq-disclosure` configura `--details-duration`
(número em milissegundos, padrão do laboratório: `320`) e `--details-easing`.
O CSS também cuida da seta, cores e recorte durante a transição. Movimento reduzido
ou ausência de suporte desativa a animação sem impedir a navegação. Menus inseridos
com o resultado são inicializados após renderizar; seleção da busca fecha o menu
pelo mesmo controlador para não deixar animações pendentes reabrirem o conteúdo.

#### Rotas Flask e serviços

`backend/controllers/benchmark_controller.py` registra o Blueprint `/benchmark`,
conectado em `app.py`, com `@login_required` e erro 401 em JSON. Não aceita URL externa,
ID de usuário fornecido pelo cliente, parâmetros desconhecidos ou repetidos.

- `GET /benchmark/fps?game=valorant&cpu=ryzen-5-5600&gpu=rtx-3060&res=1080p&preset=high`
  → `ConsultarBenchmarkService.executar(dados, current_user.id)`.
- `GET /benchmark/jogos?q=Valorant`
  → `BuscarJogosBenchmarkService.executar(dados, current_user.id)`.

Os serviços ficam em `services/benchmark_service/`, seguindo o padrão existente.
`FpshqService` faz GET apenas no host fixo do provedor, sem redirecionamentos, com
timeout de conexão/leitura de 4/15 segundos. Respostas de FPS só são aceitas quando
CPU, GPU, jogo, resolução e preset correspondem ao pedido; números ausentes não
viram zero. O veredito 1080p High do provedor não é reutilizado.

O JSON de sucesso é `{"resultado": ...}`, com `consulta`, `jogo`, `fps`, `low1`,
`intervalo`, `origem`, `base`, `confianca`, `matriz`, `url`, `consultadoEm` (epoch em ms),
`cache`, `ramAvaliada: false` e `requisitosVerificados: false`. A busca retorna
`resultado.jogos` com até dez pares `slug`/`name`. Erros usam `erro`, `codigo`, `espera`
e, no 429, `Retry-After`; validação 400, ausência 404/422, falha 502/503 e timeout 504.
O frontend não consulta o provedor como fallback e cancela a espera ao fechar o modal.

Cache LRU de até 256 consultas válidas por uma hora, compartilhado entre usuários do
mesmo processo e sem armazenar builds ou dados de perfil. Lock impede consultas
idênticas simultâneas duplicadas. Limites preventivos: 10 consultas externas/minuto
por usuário, 45/minuto e 9 mil/24h por processo; cache não consome outra chamada externa.
429 externo bloqueia novas chamadas pelo intervalo informado, preservando leituras
do cache. Nenhuma retentativa automática. Antes de escalar para múltiplos processos,
usar cache/contador distribuído; esses limites em memória não são globais entre workers.

`js/benchmark/hardware.js` mantém correspondências explícitas de modelos e VRAM;
modelos não registrados, variantes desconhecidas e vídeo integrado mostram motivo e
não são substituídos. A identificação final ainda depende da confirmação do provedor.
Ampliar esse registro ao integrar os IDs definitivos do catálogo, sem deduzir variantes.

Verificação real pela rota Flask autenticada, sem criar usuário no banco: Valorant,
Ryzen 5 5600 + RTX 3060, 1080p/Alta → HTTP 200, 288 FPS/261 de 1% low; segunda consulta
HTTP 200 com `cache: true`. São os valores retornados no teste, não dados fixos da UI.
As verificações automatizadas de falhas e interface usam respostas controladas.
Nesta rodada: 54 testes Python, 133 testes JavaScript e 66 verificações de navegador
sem falhas (320, 390, 768 e 1440 px), incluindo dots apenas por estado, modal real,
comparação visível, foco de retorno, sessão expirada, ausência de dados e 429/rede.

### RAM, peças antigas e requisitos mínimos — investigação, ainda sem integração

Em 19/10/2026 foram conferidos o [OpenAPI REST](https://fpshq.com/openapi.json),
o `tools/list` do [MCP público da FPSHQ](https://fpshq.com/en/api/ai/) e consultas reais.
O REST `/fps` não recebe RAM; seu `/canrun` usa GPU/renderer e devolve a referência
1080p High, sem ser uma checagem completa de CPU, RAM e requisitos técnicos.
Não confundir esse endpoint com a ferramenta MCP `can_run`, que aceita `game`, `gpu`,
`cpu` e `ram_gb` (capacidade inteira de 1 a 512 GB). Ela retorna requisitos e avaliação
da capacidade, não ajusta frequência, latência, canais ou memória efetivamente livre.
`game_requirements` retorna mínimos/recomendados, origem (`steam`/`manual`/`estimate`)
e situação de lançamento. Esse caminho foi pesquisado, não adicionado ao cliente do site.

Resultados observados em Cyberpunk 2077, usando Ryzen 5 5600:

- REST `/fps`, GT 1030 reconhecida (`geforce-gt-1030`), 1080p High: HTTP 200,
  `fps=8`, intervalo `[7,12]`, `low1=6`, `source=model`, `confidence=low` e
  `verdict.key=no`. A GPU abaixo dos mínimos não causou erro HTTP; houve previsão.
- REST `/fps`, slug `gt-710`: HTTP 404 com `error=gpu_not_found`. A busca “GT 710”
  retornou lista vazia. Isso é ausência de modelo nesse acesso ao catálogo, não prova
  de que a peça não roda nenhum jogo nem de que outro slug/variante inexiste.
- MCP `can_run`, GTX 750 Ti, 4 GB RAM: previsão de 11 FPS em 1080p High,
  intervalo `[9,16]`, `verdict=no`, presets para 30/60 FPS nulos e
  `ram.meets_minimum=false`. Nenhum desses números é uma medição da BOOSTio.
- MCP `can_run`, RTX 3060, comparando 4 GB com 16 GB RAM: em ambos retornou
  70 FPS em 1080p High e veredito `ok`/“Roda bem”. Com 4 GB, os campos de RAM
  indicaram `meets_minimum=false` e `meets_recommended=false`; com 16 GB, ambos
  foram `true`. A matriz de FPS foi igual: não usar o veredito isolado como aprovação.
- MCP `game_requirements` informou mínimo 12 GB e recomendado 16 GB RAM, GPU mínima
  GTX 1060 6 GB/RX 580 8 GB e 70 GB de armazenamento. Marcou `requirements_source=manual`
  e `basis=official`. Os valores principais foram conferidos com a
  [publicação da CD Projekt](https://www.cyberpunk.net/en/news/48271/update-to-pc-system-requirements),
  que também especifica SSD. O campo `storage_gb` sozinho não carrega esse detalhe.

Tratamento planejado: validar mínimos/recomendados antes de aprovar o resultado como
expectativa do PC completo; um mínimo conhecido não atendido deve prevalecer sobre
“Roda bem”. Abaixo do mínimo não equivale necessariamente a impossibilidade de iniciar;
mostrar requisito, limitação e ausência de garantia, sem inventar FPS=0. Se houver
recurso técnico obrigatório comprovadamente incompatível, informar o impedimento.
Ausência de dados/modelo e indisponibilidade/429 são estados diferentes de desempenho
baixo. `verdict=no` é um limiar de FPS em 1080p High, não uma validação de DirectX,
instruções, SO ou inicialização. A conclusão de montagem continua separada disso.

A RAM pode alterar o desempenho dependendo do jogo e configuração, como mostram os
[testes da Kingston](https://www.kingston.com/unitedkingdom/en/blog/gaming/overclocking-ram-more-fps).
Não criar correção percentual universal. Número de pentes não confirma canais ativos;
perfil anunciado não garante a taxa em uso. Memória ocupada pelo SO/outros programas
e uso por vídeo integrado também precisam de ressalva, sem supor detecção pelo navegador.

Priorizar requisitos oficiais com fonte/data e validar um adaptador de leitura da
própria FPSHQ antes de contratar outro serviço. Não inferir “atende” de descrições
genéricas nem tratar requisito estimado como oficial. A API documentada do
[System Requirements Lab](https://docs.systemrequirementslab.com/api/api-quickstart-guide.html)
usa credenciais/token e consulta análises de testes de usuários; não foi comprovada
uma API anônima gratuita equivalente para builds hipotéticas. Nenhum fallback foi
habilitado. Implementação e cenários de teste estão em `pendencias-produto.md`.

### Criação e controles compartilhados

Em Minhas builds, **Criar build** abre uma escolha entre montagem manual e formulário
inteligente, sem criar build antes da escolha e respeitando a quota. A LLM ainda não
está conectada. `navigation-controls.css` e `ui.js` padronizam voltar e fechar sem
alterar os destinos ou a lógica de histórico. Os menus dos cards usam Popover API
quando disponível, evitando o backdrop root do próprio card, com blur de 36px e
fallback. A exigência de sessão para os recursos de montagem está apenas registrada
em `pendencias-produto.md`, não implementada nesta etapa.
O botão de três pontos dos cards usa `dots.json` por `iconeAnimado("dots")`, com
hover/foco e reversão na saída. O HTML de fallback usa o mesmo marcador; movimento
reduzido ou falha no carregamento mantém um SVG estático de três pontos e o aria-label.

A [API da UL](https://support.benchmarks.ul.com/support/solutions/articles/44002238427-api-documentation)
é alternativa contratada e exige chave/segredo e assinatura; qualquer integração dela
deve passar pelo backend, sem expor credenciais no JavaScript.

Os controles `data-page-back` usam `js/components/navigation-back.js` para retornar
à entrada anterior do navegador, com a URL completa da build/categoria. O texto e a
descrição da seta acompanham o destino real. A Navigation API identifica o histórico;
nos navegadores sem ela, usa-se `document.referrer`. Acesso direto e origem externa
usam o `href` original como destino alternativo dentro do site. O formulário distingue
esse retorno do botão **Etapa anterior**, que só muda a pergunta atual.

`js/components/navigation-config.js` contém os links e a política de sessão. Visitantes
veem Entrar e Criar conta no perfil; usuários autenticados veem Builds, Configurações
e Sair. O hamburger contém Início, Montar build, Minhas builds, Builds prontas e Perfil.
A página de login não redireciona visitantes para ela mesma. Falhas de
consulta da sessão mantêm o menu de visitante disponível.

O tooltip não reescreve textos idênticos, e seu MutationObserver ignora as próprias
mutações e os frames Lottie. Isso evita o ciclo que congelava cliques. No cadastro,
validação, checkbox e envio inicializam independentemente do carregamento do Lottie.

## Responsividade

`styles/responsividades/r-site.css` centraliza espaçamentos, logo/footer,
autenticação, modais e áreas seguras do dispositivo. `--page-gutter` controla
as margens laterais e `--page-top` reserva espaço para a logo.
Os arquivos `r-*.css` mantêm os ajustes próprios de cada página.
Eles são importados **depois** de `ui-system.css`, para os estilos gerais não
sobrescreverem os breakpoints. O protótipo `testes.html` mantém seus ajustes locais.

O menu flutuante é usado em todas as larguras. Editor e formulário passam para uma coluna
quando falta espaço; catálogo, builds e a página Sobre nós reduzem suas grades.
Login e cadastro têm altura livre, e os modais são limitados pela altura visível
com rolagem interna. Campos no mobile usam pelo menos 16px, sem reduzir a tela
inteira com `scale()`. O detalhamento de compatibilidade abre no fluxo no mobile.

No formulário, opções, orçamento e rede crescem com o conteúdo sem scroll interno;
quando necessário, a página rola normalmente, sem espremer ou esconder os campos.
Botões de navegação permanecem ao final da etapa. O resumo expandido do editor
deixa de ser fixo para não prender os controles abaixo da tela. Menus dos cards de
build abrem para baixo e limitam sua altura ao espaço disponível; a
posição é recalculada ao rolar ou redimensionar. Botões bloqueados mantêm a largura
mobile mesmo com o wrapper de tooltip, e prévias de importação quebram nomes longos.

Testes: `node --test frontend/tests/*.test.mjs` (lógica de montagem, arquivos,
planejamento, acessibilidade e regressões).
Ao alterar layouts, confira 320, 390, 600, 768, 1024 e 1440px, landscape e os
estados abertos (menus, modais, senha e modelos de peças).

## Próximo passo no backend

Nenhuma arquitetura foi alterada. Apenas a chamada de atualização de preços em
`app.py` foi comentada, conforme solicitado.

Antes da integração:

1. A rota `peca_bp` precisa ser registrada; o service atual referencia classes antigas
   como `MemoriaRam` e `Armazenamento`, enquanto os modelos usam `MemoriaRAM`, `SSD` e `HD`.
2. Definir o JSON de catálogo com IDs reais, imagens e ofertas separadas por loja.
3. Revisar `Build.to_dict()`: a segunda definição atual sobrescreve a versão que inclui peças.
4. Implementar as operações de build com dono, visibilidade e tranca verificados no servidor.
5. Revalidar compatibilidade e quantidades no Python antes de persistir.

## Glass e verificação

`styles/componentes/glass.css` aplica a base de glass aos cards de serviços, builds,
configurações e novos componentes. A página Sobre nós usa os mesmos cards compartilhados. Ajuste `--glass-background`
para a transparência e `--glass-blur` para o desfoque do fundo.

Testes da lógica: `node --test frontend/tests/build.test.mjs`.
