# Funcionalidades

O que a BOOSTio faz e as regras de cada área. Para rodar tarefas no servidor, veja [comandos.md](comandos.md); para publicar, [../deploy/README.md](../deploy/README.md).

## As 20 funcionalidades obrigatórias

As **20 funcionalidades obrigatórias do projeto**, na ordem dos requisitos
definidos para a entrega e a apresentação em vídeo, com o status e o escopo atual
de cada uma.

**Resumo do produto: 20 funcionalidades obrigatórias implementadas no escopo descrito.**

- ✅ **Implementado:** fluxo disponível no código do projeto.

Os status descrevem a implementação atual, não a homologação em produção.
As limitações de cada funcionalidade estão indicadas na última coluna. E-mail
depende do SMTP configurado; a geração inteligente depende da disponibilidade e
da cota da LLM.
Operações locais não são apresentadas como novos casos de uso de backend:
exportação JSON/CSV gera o download no navegador; comparação e prévia de melhorias
têm cálculos no JavaScript sobre builds carregadas da API. Aplicar melhorias,
importar e copiar modelos prontos utilizam os fluxos de criação ou atualização
de builds no backend para persistir a configuração na conta.

| Nº | Requisito | Status | Escopo atual |
| --- | --- | --- | --- |
| 01 | O sistema deve permitir ao usuário criar sua conta e fazer login | ✅ **Implementado** | Cadastro, autenticação, logout e sessão. Código de e-mail enviado ao iniciar a verificação e conferido ao completar seis dígitos; vínculo Google explícito no perfil, com confirmação de identidade. |
| 02 | O sistema deve permitir ao usuário cadastrar seu setup atual | ✅ **Implementado** | Definir ou remover uma build como computador atual. |
| 03 | O sistema deve permitir ao usuário pesquisar compatibilidade e peças | ✅ **Implementado** | Catálogo por categoria e diagnóstico durante a montagem, com as limitações do requisito 13. |
| 04 | O sistema deve permitir ao usuário montar seu setup atual através de formulário | ✅ **Implementado** | Geração por LLM com orçamento, peças próprias identificadas pelo catálogo, preferências opcionais de gabinete/cor, ventilação obrigatória (contando fans inclusas) e uma revisão automática de saídas inválidas antes de salvar. |
| 05 | O sistema deve permitir ao usuário salvar configurações de computadores feitas | ✅ **Implementado** | Builds persistidas na conta, inclusive incompletas, com salvamento automático e avisos de falha. |
| 06 | O sistema deve permitir ao usuário excluir configurações salvas no perfil | ✅ **Implementado** | Exclusão com verificação de proprietário e tranca. |
| 07 | O sistema deve permitir ao usuário comparar configurações salvas | ✅ **Implementado** | Duas ou três builds: preços, componentes, consumo e renderização no Blender. FPS é uma ampliação pendente, não uma condição da comparação atual. |
| 08 | O sistema deve permitir ao usuário compartilhar suas configurações por link | ✅ **Implementado** | Builds públicas podem ser vistas sem login, somente leitura. Testar exige sessão; salvar uma cópia privada exige também e-mail verificado e vaga na conta. |
| 09 | O sistema deve permitir ao usuário buscar melhorias do seu setup | ✅ **Implementado** | RAM: acrescentar ou substituir pentes conforme a placa-mãe. SSD/HD: expandir quantidades mantendo os atuais, respeitando conexões/baias conhecidas, ou substituir sem regressões verificáveis. Orçamento obrigatório para aplicar; CPU/GPU e outras categorias dependem de métricas confiáveis. |
| 10 | O sistema deve permitir ao usuário ver configurações prontas | ✅ **Implementado** | 16 modelos sem periféricos, referências revisadas no catálogo, filtro de budget e preço crescente. A cópia respeita e-mail verificado e limite da conta. |
| 11 | O sistema deve permitir ao usuário editar e modificar configurações salvas | ✅ **Implementado** | Alteração de componentes, nome, descrição e orçamento; desfazer/refazer até 25 alterações de peças nesta visita ao editor, por botões ou Ctrl/Cmd+Z e Ctrl/Cmd+Shift+Z. Campos de texto mantêm o desfazer nativo. |
| 12 | O sistema deve permitir ao usuário verificar o preço da peça direto pelo site, sem precisar consultar em diversas abas | ✅ **Implementado** | Preços cadastrados, data quando disponível e links das lojas. Antes da compra, o catálogo é reconsultado e diferenças/indisponibilidade são mostradas. Não inclui frete nem garante o valor no checkout. |
| 13 | O sistema deve permitir ao usuário ver todas as informações de compatibilidade e consumo de energia do setup que está montando | ✅ **Implementado** | Diagnóstico da build, consumo estimado e fichas técnicas conforme os dados cadastrados. Conflitos ficam em destaque; conferências e dicas são agrupadas por assunto, com detalhes recolhidos. Referências visuais de fans são identificadas como estimativas e não aprovam encaixes. Ampliar a cobertura de modelos permanece uma melhoria de catálogo. |
| 14 | O sistema deve permitir ao usuário adicionar ao setup periféricos, que muitas vezes não pensado anteriormente, acaba estourando o orçamento | ✅ **Implementado** | Inclusão e reaproveitamento com tetos separados para PC e periféricos. |
| 15 | O sistema deve permitir ao usuário registrar em seu perfil o seu budget, assim fica registrado o seu dinheiro disponível para comprar e futuras melhorias | ✅ **Implementado** | Valor e autorização usados no formulário e em novas montagens manuais, sem alterar builds existentes. |
| 16 | O sistema deve permitir ao usuário baixar a build em JSON e CSV para ter o arquivo local | ✅ **Implementado** | Exportação para guardar a configuração localmente. |
| 17 | O sistema deve permitir ao usuário alterar a visibilidade da build | ✅ **Implementado** | Alternância entre pública e privada. |
| 18 | O sistema deve permitir ao usuário duplicar a sua build | ✅ **Implementado** | Cópia independente, respeitando o limite da conta. |
| 19 | O sistema deve permitir ao usuário definir um nome e descrição para a build | ✅ **Implementado** | Identificação e edição dos detalhes da build. |
| 20 | O sistema deve permitir ao usuário importar builds por meio de arquivos CSV ou JSON | ✅ **Implementado** | Validação do arquivo e criação de uma configuração na conta. |

### Regras da plataforma

- **Acesso:** início, termos, contato, sobre, cadastro, login e recuperação de senha
  são públicos. Links de builds públicas também abrem sem login, em uma tela somente
  leitura. Formulário, editor, catálogo, perfil, builds prontas e laboratório exigem login.
- **Criação:** e-mail verificado e limite de **três builds por conta**, incluindo
  montagem manual, formulário, importação, cópia de modelo e duplicação.
- **Tranca:** uma build trancada não pode ser editada nem excluída antes de ser destrancada.
- **Compartilhamento:** o visitante não altera a build original nem acessa o budget
  ou os dados privados do proprietário. A autoria mostra somente o nome de exibição,
  sem e-mail ou ID da conta; contas desativadas aparecem como “Conta desativada”.
  Testar exige login; uma cópia é privada e independente.
  Tornar a original privada interrompe novas consultas e cópias pelo link público.
- **Desativação da conta:** bloqueia o acesso, encerra sessões e libera o e-mail
  para novo cadastro, preservando registros. A recuperação será assistida pela
  equipe; o procedimento de identificação e restauração ainda precisa ser definido.

### Como o orçamento é respeitado

Nas montagens para jogos, **AMD Ryzen é uma preferência de plataforma**, quando
houver uma combinação adequada no catálogo. Peças próprias, compatibilidade e
orçamento têm prioridade: a geração pode escolher Intel quando necessário, sem
reduzir a placa de vídeo apenas para manter a marca do processador. A preferência
não significa que todo Ryzen tenha desempenho superior a qualquer Intel.

O percentual para periféricos é um **teto, não uma meta de gasto**. O restante
define o limite do PC, incluindo acessórios de rede.

Na **montagem inteligente**, é necessário reservar pelo menos **R$ 2.000 para
o PC**, depois de descontar os periféricos. Para incluir periféricos novos, a
reserva deve ser de pelo menos **R$ 500** e comportar o conjunto disponível no
catálogo, que pode custar mais. Por exemplo, R$ 2.500 com 20% atende aos mínimos
iniciais: R$ 2.000 para o PC e R$ 500 para periféricos. Isso não garante uma
configuração adequada a qualquer objetivo. O formulário e o Python conferem os
limites antes de chamar a IA; a regra não impõe gasto mínimo nem restringe o
orçamento da montagem manual.

> Com **R$ 5.000** e uma reserva de **20%**, o PC tem teto de **R$ 4.000** e os
> periféricos, de **R$ 1.000**. Se os periféricos custarem menos, a sobra fica com
> o usuário: não aumenta o teto do PC.

O Python confere os subtotais pelos preços e quantidades do catálogo antes de
salvar a sugestão. O **frete não está incluído**: é importante reservar parte do
orçamento para a entrega.

Se a geração falhar, a resposta distingue orçamento, reserva de periféricos,
catálogo, compatibilidade, aparência e saída incompleta da IA. Falhas de conexão,
cota ou disponibilidade do serviço recebem orientações próprias. No erro de
orçamento, o usuário pode **editar o valor e confirmar uma nova tentativa na
mesma tela**, mantendo as demais respostas e a porcentagem reservada. Também
pode revisar a etapa relacionada ou tentar sem preferência de cor/aparência.
Nenhum aumento é aplicado automaticamente ou altera o budget do perfil; uma
recusa da IA por cor não comprova indisponibilidade em todo o catálogo.

Para jogos, trabalho pesado e **Um pouco de tudo**, uma sugestão que use menos
de 75% do teto do PC pode passar pela revisão já disponível, quando houver
alternativas de CPU/GPU/RAM/SSD para avaliar dentro desse limite. Isso também
vale para orçamentos como R$ 8.000. O prompt orienta buscar uma configuração
equilibrada na faixa de 80% a 100% do teto do PC, sem transformar isso em gasto
mínimo nem usar preço como prova de desempenho. Peças próprias continuam com
custo zero, e a sobra dos periféricos não é transferida ao PC. Se a revisão
falhar ou a cota terminar, a primeira configuração válida é preservada.

Se o catálogo não tiver um cabo ou adaptador adequado à conexão solicitada,
a montagem do PC pode prosseguir **com a rede pendente**. O pedido de comprimento
e velocidade fica registrado, e a build informa que o acessório não foi incluído
no total. Um cabo curto não substitui automaticamente o comprimento necessário.

O formulário separa **tamanho do gabinete**, **estilo** e **cor**, com imagens de
exemplo sem preços ou ofertas e opções de “sem preferência”. Os tamanhos são
Mini, Mid e Full Tower; os estilos são sem vidro, vidro lateral, aquário
(frente/lateral) e panorâmico com três faces de vidro (frente/lateral/teto).
Ao escolher o tamanho, um exemplo mostra medidas externas, placas-mãe,
ventoinhas e radiador suportados. Esses dados são do modelo de referência,
não um padrão de todos os gabinetes daquele tamanho. São preferências flexíveis:
não autorizam exceder o orçamento nem ignorar medidas, ventilação ou estoque.
Na geração inteligente, a preferência de cor se aplica a **todas as peças e
periféricos novos**, incluindo gabinete, ventoinhas e resfriadores. A amostra de
produtos e os conjuntos de periféricos preservam opções da cor desejada sem
eliminar alternativas econômicas e padrões técnicos. O complemento automático
de fans também considera a cor, depois de verificar encaixe e orçamento.
Cor cadastrada tem prioridade; nomes com indicação de cor são referências
comerciais, não confirmação técnica da versão. RGB, switch, fotos e URLs não
comprovam a cor da carcaça. Peças próprias são preservadas; ausência da cor
preferida não impede usar uma alternativa adequada, sem exceder os tetos.
Variantes da mesma família e ficha podem ser ajustadas para a cor solicitada
após nova validação de orçamento e compatibilidade. Para o gabinete, a seleção
também considera o estilo disponível quando o porte escolhido não existir;
preferências não confirmadas ficam indicadas nas orientações da build.
Características ausentes não são inventadas. O editor também mostra a
capacidade total de SSDs/HDs em GB/TB; quando faltam dados, identifica o subtotal
como parcial. Monitores selecionados mostram a taxa de atualização em Hz e a
resolução cadastrada ao lado do título da categoria.

O uso escolhido no formulário explica **quais peças terão prioridade**. As páginas
do catálogo e da peça também apresentam uma descrição simples da função de cada
componente, mantendo as informações técnicas para quem quiser conferir os detalhes.

Avisos distinguem falta de conexão, demora e erro respondido pelo servidor.
Se a resposta de uma criação ou alteração se perder, orientamos conferir o
resultado antes de repetir. Falhar ao verificar a sessão não significa sair da
conta: é possível tentar novamente, mantendo o conteúdo privado bloqueado até a confirmação.

## Builds prontas

16 pontos de partida para **estudos, home office, programação, jogos,
criação de conteúdo, modelagem no Blender e máquinas virtuais**, com plataformas
AM4, AM5 e Intel e diferentes níveis de investimento.

Os modelos não incluem monitor, teclado, mouse, headset ou outros periféricos.
Os totais e o filtro de orçamento usam os preços disponíveis no catálogo da conta.
Modelos sem todas as cotações ou com peças indisponíveis não aparecem como opções
dentro de um budget informado. A disponibilidade pode mudar após a revisão.

A cópia é uma base editável: peças ausentes ou indisponíveis são sinalizadas no
editor; não são substituídas por produtos parecidos nem registradas como peças
que o usuário já possui. Totais sem todas as cotações são parciais.

## Peças e preços

A maioria dos preços cadastrados vem da **KaBuM**. Quando existe vínculo com o
anúncio, o link leva ao produto exato. A **Pichau** é uma alternativa de busca
pelo modelo, sem garantia de oferta equivalente ou de preço confirmado.

Cada peça mostra **no máximo um anúncio por loja: o mais barato**. O preço de referência da
peça é o menor entre as ofertas exibidas de todas as lojas, desconsiderando as esgotadas quando
há alguma disponível. O preço das ofertas do Mercado Livre e da Shopee é reconsultado uma vez
por dia (`marketplaces-precos-atualizar`) e cada coleta alimenta o histórico.

O **histórico de preços** da peça tem um filtro por loja. A visão padrão, "Todas as lojas", mostra
o menor preço de cada dia entre as lojas; as demais mostram só a KaBuM, o Mercado Livre ou a Shopee.

Preço cadastrado não significa cotação em tempo real. Estoque, frete e condições
de compra devem ser conferidos na loja. A ficha da peça distingue dados da conta
de exemplos demonstrativos e informa a última atualização do preço quando cadastrada.

As fotos da API têm prioridade. Quando faltam, há **750 vínculos locais de referência**
por part number, categoria, fabricante e modelo exatos, sem depender do ID numérico
do banco. Peças sem correspondência ou com foto quebrada mantêm uma alternativa neutra;
isso não significa cobertura de imagens para todo o catálogo.

> A BOOSTio **não vende, entrega ou processa pagamentos** dos produtos. Os links
> direcionam a lojas de terceiros, responsáveis pela venda e pelo atendimento.

## Navegação e animações

O menu oferece **Reduzir animações**: desativa entradas durante a rolagem e
mantém imagens estáticas no lugar dos vídeos. Os **Lotties dos ícones e controles
continuam funcionando**, inclusive o toggle e os checkboxes. A preferência fica salva no
navegador; sem uma escolha, o site acompanha a preferência de movimento do
sistema. Os vídeos decorativos pausam fora da tela e retomam ao voltar.

A configuração de produção publica URLs como `/builds`, `/formulario` e
`/sobre`, mantendo os links antigos e os parâmetros de compartilhamento.

## Desempenho esperado

Ao selecionar **Testar build**, o usuário escolhe entre **Jogos · FPS** e
**Blender · Renderização**. As consultas passam pela API Python da BOOSTio e
exigem uma sessão autenticada.

### Jogos · FPSHQ

A integração permite escolher jogo, resolução e qualidade
gráfica, com **FPS médio** e **1% low** quando disponíveis. Falhas e ausência de
dados não geram FPS inventados.

A FPSHQ é um serviço externo e pode ficar indisponível ou lento. Nesse caso o Python informa a indisponibilidade, aplica uma pausa e só devolve cache validado antes, com aviso de desatualização. HTML ou resposta inválida nunca vira FPS.

Nas builds salvas, **Verificar requisitos** usa o catálogo Python para comparar RAM,
VRAM dedicada e capacidade/tipo de armazenamento quando há um mínimo oficial
estruturado. Funciona independentemente da FPSHQ e interrompe a consulta na interface
quando identifica capacidade abaixo do mínimo. Dados próprios não identificados
permanecem desconhecidos. Não soma VRAM de placas ou discos separados, nem afirma
quanto espaço livre existe. Equivalência de CPU/GPU, sistema e demais recursos
continuam pendentes: capacidades suficientes não aprovam o computador completo.

### Blender · Renderização

Dados públicos de CPU ou GPU, com **mediana em amostras por minuto**, versão do
Blender, método de renderização e quantidade de resultados. O retorno é validado pelo serviço Python, sem garantia de disponibilidade permanente. Falhas distinguem ausência de resultados, conexão, tempo esgotado e
recusa da fonte, com uma referência para diagnóstico.

A comparação de builds consulta esses dados ao clicar em **Comparar renderização**.
CPU e GPU são analisadas separadamente; só há classificação quando todas as builds
exibidas têm resultados da mesma versão do Blender e do mesmo método de renderização.
O reconhecimento do Blender é independente dos slugs da API de FPS: nomes
comerciais como EAGLE, DUAL e SHADOW não impedem identificar o chip explícito.
Sufixos e variantes são preservados; modelos não identificados ou sem resultados
públicos são informados por build, sem substituir a peça nem inventar pontuação.

### Limites da estimativa

Essas consultas **não executam um benchmark no computador do usuário**. RAM,
VRAM, drivers, temperatura, energia, cena e programas em segundo plano podem
influenciar o desempenho real. Pontuações de CPU e GPU no Blender não são somadas
e não representam um tempo garantido de renderização.

Fontes: [FPSHQ](https://fpshq.com/pt/api/) e
[Blender Open Data](https://opendata.blender.org/about/).

### Laboratório de testes

No laboratório (`testes.html`), é possível comparar uma consulta FPS pelo Python
com uma consulta direta pelo JavaScript, sem cache local neste último caminho.
O diagnóstico informa tempo, HTTP recebido e falhas de transporte/validação.
Quando disponíveis, distingue o HTTP da BOOSTio do status e formato recebidos
da FPSHQ e informa se a tentativa apenas encontrou a pausa após uma falha anterior;
não troca automaticamente de caminho nem altera a montagem real.

Os **requisitos dos cinco jogos padrão** usam fontes oficiais revisadas em 21/10/2026
e consulta autenticada pelo Python. O modal usa a RAM da build salva e do catálogo;
o laboratório mantém uma prévia com capacidade informada manualmente.
O laboratório compara RAM informada; a build salva também verifica as capacidades
adicionais descritas acima. Não inventamos requisitos recomendados ausentes nem
ajustamos FPS por uma fórmula. Equivalência de CPU/GPU, sistema, espaço livre e
demais exigências continuam sem validação completa.


## Administração

Dashboard em `/admin` (`frontend/pages/admin.html`), só para contas com o papel de administrador. Hoje tem
uma seção, **Pendências**; novas seções entram em `frontend/js/admin/secoes.js` (id, rótulo e função que a
inicia) com um bloco `data-admin-secao` correspondente no HTML.

### Quem é administrador

A coluna `usuario.administrador` (falsa por padrão). Não existe rota pública para alterá-la: só pelo terminal
do servidor, e a conta precisa estar ativa e com e-mail verificado. Promover ou remover encerra as sessões
dessa conta (ela entra de novo e passa a ver o novo papel).

```sh
# Na VPS, a partir do checkout do projeto
docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app usuario-promover-admin --email pessoa@exemplo.com
# também: usuario-remover-admin --email ...   e   usuario-listar-admins
```

Banco existente precisa da coluna antes (faça backup):

```sh
python -m flask --app app usuarios-admin-preparar            # simula
python -m flask --app app usuarios-admin-preparar --aplicar  # adiciona usuario.administrador
```

`banco-preparar` (SQLite) já aplica isso. No MySQL, rode `usuarios-admin-preparar --aplicar` na janela de
atualização, antes de subir o código novo: sem a coluna, o login quebra.

### Como a proteção funciona

- O link "Administração" aparece no menu do perfil só para administradores (`/auth/me` devolve `administrador`).
- A página começa oculta e só aparece depois de confirmado o papel. Quem não é administrador vê "página não encontrada" (404), sem flash do painel nem título de administração. Visitante sem login vai para o login.
- **O que protege de verdade é o servidor:** toda rota `/admin/*` usa `@login_required` e `@apenas_administrador`
  (401 sem login, 403 sem o papel) e as ações de escrita exigem o token CSRF como no resto do site.

### Pendências

Lista os anúncios de `produto_pendente` (por padrão `em_revisao`), com filtros de situação, loja e categoria.

| Rota | O que faz |
| --- | --- |
| `GET /admin/pendencias` | Lista com `status`, `loja`, `categoria`, `limite` e `depois_id` (cursor). |
| `GET /admin/pendencias/<id>` | Detalhe com os candidatos (peça, pontuação, conflitos e o que falta comprovar). |
| `POST /admin/pendencias/<id>/aceitar` | `{"peca": "categoria:id"}`: cria a oferta e o vínculo. |
| `POST /admin/pendencias/<id>/candidatos/descartar` | `{"peca": "categoria:id"}`: tira só aquela peça da lista de candidatas (fica registrado e um novo matching não a recoloca). |
| `GET /admin/pendencias/ids-para-ia` | Ids de todas as pendências abertas do filtro (`status`, `loja`, `categoria`) que a IA consegue analisar. |
| `POST /admin/pendencias/enviar-ia` | `{"ids": [1, 2], "decidir": false, "refazer": true}`: a IA analisa até 20 pendências por pedido, numa só requisição (sempre refaz); com `decidir: true` também aceita ou rejeita as de alta confiança. |
| `POST /admin/pendencias/<id>/rejeitar` | `{"motivo": "..."}` (opcional, até 200 caracteres). |

Regras do aceite:

- Só vale para uma das peças candidatas daquela pendência, sem conflito, aprovada e da mesma categoria.
- Usa o mesmo caminho de gravação da busca automática: trava da coleta, peça inalterada desde a análise e
  anúncio que não pertence a outra peça. Só a decisão automática de "confirmada" é dispensada, porque quem
  decidiu foi uma pessoa; o `administrador_id` e a data ficam em `evidencias.revisao_manual`.
- **Shopee e Mercado Livre podem ser aceitos pelo painel.** No Mercado Livre o servidor reconsulta o
  catálogo e o anúncio na API da loja (poucas requisições, antes da transação) e confere que continua
  disponível como oferta nova do mesmo vendedor. Depois grava o vínculo do catálogo com a peça (critério
  `revisao_manual`), a oferta e o histórico, e fecha a pendência, tudo numa transação. Catálogo já ligado a
  outra peça, peça que mudou desde a análise ou anúncio que saiu do ar recusam o aceite. Se o Mercado Livre
  não responder, o painel recebe 502 e nada é gravado.
- Pendência já aceita ou rejeitada não é reaberta (nem pelas buscas seguintes).

### Sugestão da IA nas pendências

Para não analisar tudo à mão, a IA pode recomendar a peça de cada pendência aberta:

```bash
cd backend
python -m flask --app app admin-pendencias-sugerir --limite 20            # só conta o que analisaria
python -m flask --app app admin-pendencias-sugerir --limite 20 --aplicar  # chama a IA e grava
```

- Por padrão a IA **só sugere**. Com `--decidir` (ou o botão "Deixar a IA decidir" no painel) ela também
  **aceita** quando indica uma peça e **rejeita** quando conclui que nenhuma serve, em ambos os casos só com
  confiança de pelo menos 90 (`--confianca-minima`, de 50 a 100). Abaixo disso a pendência fica para uma pessoa.
  O aceite usa o mesmo caminho seguro do painel (reconsulta o anúncio e valida a peça); se ele falhar, a
  pendência continua aberta. A decisão fica registrada com `origem: "ia"`. **Rejeição não pode ser desfeita.**
- Sem `--decidir`, nada é aceito ou rejeitado pela IA: a recomendação (peça, confiança de 0 a 100,
  justificativa curta, modelo e versão do prompt) fica em `evidencias.sugestao_ia` da pendência.
- Entram só pendências que têm candidata aprovada e sem conflito. A resposta é validada: a peça indicada
  precisa ser uma das candidatas e a confiança, um inteiro de 0 a 100; caso contrário conta como falha.
- Pendência já analisada, com as mesmas candidatas e o mesmo anúncio, não gasta IA de novo (`--refazer` força).
- O texto do anúncio vai como dado, com instrução de ignorar ordens contidas nele; mesmo assim, o painel
  continua sendo quem aceita, e o aceite reconsulta o anúncio e valida a peça.
- Usa `GEMINI_API_KEY`; o modelo pode ser trocado com `IA_ANALISE_MODELO`. Não consome a cota diária de
  gerações dos usuários.
- No painel aparece a etiqueta "IA sugere (92%)" na pendência e a marca "Sugerida pela IA" na candidata,
  com a justificativa. `--loja` e `--categoria` filtram o lote.

No painel, cada pendência tem uma caixa de seleção, e há "Selecionar todas" e o botão **Enviar para a IA (n)**.
O painel envia em grupos de 20 (uma requisição à IA por grupo) e mostra o andamento; ao final recarrega a lista com as etiquetas da IA.

#### Requisições à IA

O plano gratuito do Gemini limita as requisições por minuto, então as pendências vão **juntas**: até 20 por
requisição (`IA_ANALISE_LOTE`, padrão 20). A resposta traz uma entrada por pendência e cada uma é validada
separadamente: item ausente ou inválido fica sem sugestão e não estraga os demais. Se a resposta inteira
falhar (JSON cortado, por exemplo), o lote é dividido ao meio e reenviado. Para reduzir o risco de uma
resposta longa demais, mantenha o lote em torno de 20.

#### Enviar tudo de uma vez

A caixa **Selecionar todas** marca todas as pendências abertas do filtro atual (não só as da página), e
**Selecionar 20** marca as 20 primeiras da lista. Ao clicar em **Enviar para a IA**, o envio roda
como um processo: lotes de 20, uma requisição à IA por lote, mostrando o andamento. Quem falhar (limite de
requisições, instabilidade, resposta inválida) espera 15s, depois 45s e 90s e é reenviado; se ainda assim
falhar, é contado como falha e o processo segue com o próximo lote. O botão **Parar** interrompe depois do
lote atual. Pendências que já têm sugestão atual não gastam IA de novo, então um envio interrompido pode ser
retomado selecionando todas e enviando de novo. A caixa **Deixar a IA decidir** vale para qualquer seleção. O processo roda
com a aba aberta; para rodar sem o navegador, use o comando (ele também espera e repete em caso de limite):

```bash
python -m flask --app app admin-pendencias-sugerir --limite 500 --decidir --aplicar
```
