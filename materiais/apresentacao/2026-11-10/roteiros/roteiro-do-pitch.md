# BOOSTio — roteiro de ensaio

Apresentação de terça-feira, 10/11/2026. Turma 3A2.

**Meta: 6min30. Limite: 7 minutos.** A demonstração ocupa 1min50 e já está incluída nos 6min30. Os slides 18, 19 e 20 são apoio e ficam ocultos na apresentação.

As falas abaixo são uma base de ensaio. Os intervalos são metas, não uma medição de apresentação já realizada. A divisão entre integrantes é uma sugestão.

## Funcionalidades do README escolhidas para o vídeo

Os quatro blocos da demonstração correspondem a quatro dos 20 requisitos obrigatórios do README. A ordem acompanha a experiência de quem monta um computador: receber uma sugestão, conferir as peças, comparar alternativas e melhorar a configuração.

1. **RF04 — Montar o setup através de formulário.** Mostrar as respostas do usuário e a configuração gerada. O resultado principal é a seleção de peças conforme objetivo e orçamento, não apenas a criação de um registro.
2. **RF13 — Ver informações de compatibilidade e consumo de energia.** Mostrar uma regra técnica aplicada às peças e o consumo estimado. O resultado principal é o diagnóstico; dados ausentes continuam identificados como não verificados.
3. **RF07 — Comparar configurações salvas.** Mostrar duas builds lado a lado e explicar uma diferença calculada de preço, componentes ou consumo. A comparação ajuda a decidir entre alternativas.
4. **RF09 — Buscar melhorias do setup.** Mostrar uma sugestão de expansão de RAM ou armazenamento dentro do valor informado, a diferença antes/depois e a aplicação da melhoria. O resultado principal é a recomendação validada, além da atualização da build.

Essas funções apresentam processamento e resultados além de cadastrar, listar, consultar, editar ou excluir registros isoladamente. **RF10 — Ver configurações prontas** permanece como o quinto caso de uso nos slides 3 a 7, mas não entra na contagem das quatro funções não CRUD do vídeo. As operações de salvar e editar podem aparecer como parte dos fluxos, sem serem contadas como funções extras.

## Arthur Ferreira Raymundo — 0:00 a 1:10

### Slide 1 — abertura, 20 segundos

“Somos a equipe Boostio, da turma 3A2: Arthur Ferreira Raymundo, Gustavo Azevedo Oliveira, Gustavo Lopes Horta, Giovanni de Castro Morais Trivellato e Kayky Luiz Ferreira de Paula da Silva. A Boostio ajuda quem quer montar ou melhorar seu computador a escolher as peças conforme o objetivo e o orçamento.”

### Slide 2 — problema e público, 10 segundos

“Quem monta o primeiro PC precisa saber quais peças combinam e onde investir. A Boostio atende estudantes, jogadores, criadores e profissionais que têm essas dúvidas.”

### Slides 3 a 7 — cinco casos de uso, 8 segundos por tela

3. **RF04 — Formulário:** “No formulário, o usuário informa seu objetivo, orçamento e peças próprias para receber uma sugestão de configuração.”
4. **RF13 — Compatibilidade e consumo:** “O diagnóstico cruza os dados das peças e mostra conflitos, consumo estimado e o que ainda precisa de conferência.”
5. **RF07 — Comparação:** “Na comparação, o usuário avalia duas ou três builds pelos componentes, preços e consumo estimado.”
6. **RF09 — Melhorias:** “A busca de melhorias mostra opções de RAM e armazenamento, com uma prévia do resultado antes de aplicar.”
7. **RF10 — Builds prontas:** “As builds prontas oferecem pontos de partida que o usuário filtra por objetivo e orçamento e depois personaliza.”

Os números dos requisitos são referências para preparar o material; não precisam ser lidos em voz alta.

Transição: “Agora, o Gustavo explica como esses dados se organizam.”

## Gustavo Azevedo Oliveira — 1:10 a 2:30

### Slide 8 — domínio, 30 segundos

“Usuario representa a conta e o orçamento. Build referencia os modelos do catálogo. Processador herda os atributos comuns de Peca, como fabricante e preço. BuildSalva guarda o estado em JSON, incluindo componentes e quantidades. Ela pode existir sem uma Build original. Uma conta pode possuir várias configurações na relação, mas a regra de negócio limita a três. O slide mostra um recorte das classes principais.”

### Slide 9 — recuperação de dados, 25 segundos

“Ao abrir uma build, o frontend envia uma requisição GET. O Controller chama o Service, que busca a configuração do proprietário e prepara o diagnóstico. A Model consulta o banco pelo ORM e a API devolve JSON. Hoje esse fluxo ainda acessa a Model diretamente. O Repository tracejado indica a adequação que falta para a rubrica.”

### Slide 10 — entrada de dados, 25 segundos

“Na entrada, o frontend envia o estado em JSON. O Controller recebe e o Service valida a configuração e as regras. BuildSalva verifica o e-mail e o limite da conta, grava e confirma a transação. A resposta volta ao navegador. Também precisamos extrair essa persistência para um Repository para completar o fluxo exigido.”

**Antes da apresentação:** os slides 9 e 10 refletem o código observado em 08/11. Se a equipe adequar os Repositories, revisar os diagramas e substituir essas falas por uma explicação da implementação resultante. Não apresentar o tracejado como código já existente.

Transição: “O Gustavo Lopes mostra a organização e a comunicação com o frontend.”

## Gustavo Lopes Horta — 2:30 a 3:25

### Slide 11 — arquitetura, 25 segundos

“O frontend reúne páginas HTML, estilos e módulos JavaScript. No backend, Controllers recebem as requisições, Services executam os casos de uso e Models representam as entidades SQLAlchemy. Os Repositories atuais atendem operações específicas. O CRUD de builds ainda permanece nas Models, como indicado nos fluxos anteriores.”

### Slide 12 — frontend e API, 30 segundos

“O frontend consome a API por requisições HTTP. Este módulo chama a rota da build e recebe JSON. A base da API fica configurada separadamente, e as chamadas enviam a sessão. Na evidência do Network, mostramos a requisição, o status e a resposta do servidor real.”

**Preparar esta evidência:** abrir uma ação no sistema real, capturar a requisição e a resposta JSON, deixando claro qual processo serve o frontend e qual serve a API. O frontend local usa a porta 5000 como API por padrão, mas essa porta pode estar ocupada no Mac. Não alterar a configuração sem conferir o ambiente.

Transição: “O Giovanni vai mostrar quatro funções funcionando.”

## Giovanni de Castro Morais Trivellato — 3:25 a 5:15

### Slide 13 — vídeo ou sistema real, 1min50

#### 0:00 a 0:35 — RF04: montagem pelo formulário

- **Ação na gravação:** começar com o formulário quase preenchido. Mostrar o objetivo e o orçamento, confirmar as respostas e enviar o pedido de geração.
- **Resultado a mostrar:** a configuração realmente retornada, com as peças selecionadas e o total. Conferir os tetos de PC e periféricos, se houver reserva separada.
- **Fala sugerida:** “Informo para que vou usar o computador e quanto posso gastar. A montagem inteligente escolhe as peças, e o backend confere as regras e o orçamento antes de salvar.”

#### 0:35 a 1:00 — RF13: compatibilidade e consumo

- **Ação na gravação:** abrir o diagnóstico da build e conferir uma regra com dados conhecidos, como o padrão de RAM aceito pela placa-mãe ou a quantidade de slots. Mostrar como essa regra orienta as opções disponíveis na montagem.
- **Resultado a mostrar:** a verificação e seu motivo, junto do consumo estimado em watts. Se houver um conflito real no cenário de ensaio, mostrar o aviso e sua correção; não forçar uma seleção que a interface bloqueia.
- **Fala sugerida:** “O sistema cruza as informações das peças para verificar se podem trabalhar juntas e estima o consumo de energia. Quando falta algum dado do fabricante, ele indica o que ainda precisa de conferência.”

Trocar ou consultar uma peça isoladamente não é o resultado principal deste bloco. Mostrar a avaliação automática, sem apresentar consumo como medição real nem afirmar que uma build está totalmente compatível quando existem verificações pendentes.

#### 1:00 a 1:25 — RF07: comparação de configurações

- **Ação na gravação:** abrir “Minhas builds”, clicar em comparar e exibir duas configurações já preparadas.
- **Resultado a mostrar:** apontar os totais e uma diferença concreta de componentes ou consumo. Explicar o que muda entre as opções; menor preço ou menor consumo não comprova maior desempenho.
- **Fala sugerida:** “Posso comparar duas configurações lado a lado. Aqui vejo o que muda nas peças, no preço e no consumo estimado para decidir qual atende melhor ao que preciso.”

A comparação básica calcula os dados no navegador a partir de builds carregadas da API. Ela já atende a este requisito sem depender de FPS ou de uma consulta ao Blender; esses testes não são necessários para este vídeo.

#### 1:25 a 1:50 — RF09: buscar e aplicar uma melhoria

- **Ação na gravação:** abrir “Buscar melhorias” em uma build de ensaio, informar quanto deseja investir e escolher uma expansão válida de RAM ou SSD/HD.
- **Resultado a mostrar:** a capacidade antes/depois, o custo da expansão e o respeito aos slots ou conexões conhecidos. Clicar em “Aplicar trocas” e confirmar o resultado salvo no editor; conferir a persistência ao reabrir a build antes de finalizar a gravação.
- **Fala sugerida:** “Para melhorar o computador que já tenho, informo um valor e consulto opções compatíveis. Nesta sugestão, aumento a capacidade mantendo as peças atuais e vejo o custo antes de aplicar.”

Escolher no ensaio uma expansão que o catálogo realmente permita. Não prometer ganho de FPS ao aumentar RAM ou armazenamento nem apresentar CPU/GPU como recomendações já disponíveis nesta busca.

### Preparação da gravação

- Usar uma conta de demonstração com e-mail verificado, duas builds salvas e uma vaga livre para a geração do primeiro bloco. Não projetar dados pessoais, senhas ou códigos de verificação.
- Separar duas builds com diferenças visíveis e dados de preço conhecidos. Reservar uma delas com espaço para a expansão de RAM ou armazenamento do último bloco.
- Ensaiar a geração, a regra de compatibilidade e a expansão com o catálogo atual antes de gravar. Este roteiro define a demonstração; não comprova que esses cenários já foram homologados.
- Exibir uma legenda curta no início de cada trecho: “RF04 · Montagem inteligente”, “RF13 · Compatibilidade e consumo”, “RF07 · Comparar builds” e “RF09 · Buscar melhorias”.
- Gravar a ação e o resultado das quatro funções. Usar os 35 + 25 + 25 + 25 segundos como metas de edição; o vídeo final deve ter 1min50 e nunca ultrapassar dois minutos.

**Melhor formato para controlar o tempo:** vídeo de uma execução real, narrado pelo integrante. Cortar esperas e deslocamentos de mouse, mantendo visíveis a ação e o resultado. Não montar um vídeo com respostas falsas ou apenas screenshots. O vídeo ainda precisa ser gravado pela equipe.

**Contingência:** manter uma gravação real já conferida dos quatro blocos, especialmente da geração por IA, para não depender da internet durante a apresentação. Se algum cenário falhar no ensaio, ajustar ou corrigir esse cenário antes de gravar. Não substituir uma função por listagem de builds prontas, cadastro, exclusão ou cópia isolada. FPS e Blender não entram na lista escolhida para este vídeo.

## Kayky Luiz Ferreira de Paula da Silva — 5:15 a 6:30

### Slide 14 — ORM, 17 segundos

“As Models usam SQLAlchemy. A classe base adiciona ou remove a instância da sessão e confirma a transação. Para comprovar o CRUD, usamos registros controlados e observamos a gravação e a leitura no banco.”

Preparar a evidência real em banco temporário. A frase sobre comprovação só deve ser usada depois que essa evidência existir.

### Slide 15 — SQL no Repository, 18 segundos

“SaudeRepository executa SELECT 1 para verificar a conexão. É um exemplo real de SQL nessa camada. A consulta de negócio de uma build ainda precisa ser extraída para Repository e validada com um resultado conhecido para atender melhor à rubrica.”

### Slide 16 — tecnologias e README, 30 segundos

“Usamos Python, Flask e SQLAlchemy na API e HTML, CSS e JavaScript no frontend. O README lista as 20 funcionalidades implementadas, com escopo e limitações. Os bônus só entram com evidência de execução: IA funcionando, frontend e API publicados e a decisão de consentimento registrada.”

Abrir o README brevemente, já na seção de funcionalidades. Não ler os 20 itens em voz alta. Só afirmar um bônus específico após a confirmação correspondente.

### Slide 17 — encerramento, 10 segundos

“A Boostio ajuda você a escolher as peças do seu próximo computador conforme o que precisa. Menos dúvidas, mais desempenho. Obrigado.”

## Ensaio

- Primeiro ensaio: cronometrar o conjunto, sem interromper para corrigir detalhes.
- Segundo ensaio: ajustar as transições e usar o vídeo com o tempo definitivo.
- Usar os 30 segundos de margem para trocas de apresentador e abertura do README, sem ampliar a demo acima de dois minutos.
- Levar a apresentação e o vídeo disponíveis localmente. Fechar notificações e abas pessoais antes de projetar.

## Origem das telas

Os slides de casos de uso mostram HTML, CSS e JavaScript reais do frontend, renderizados localmente com respostas de API simuladas e catálogo demonstrativo versionado. Eles apresentam a interface e o objetivo de cada caso. Não comprovam persistência, execução da LLM ou funcionamento em produção.
