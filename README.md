<div align="center">
  <img src="./frontend/imgs/logoBOOSTio.gif" alt="BOOSTio" width="360" height="90">
  <h1>BOOSTio</h1>
  <p>Uma plataforma para planejar, montar e melhorar configurações de computadores.</p>
  <p><strong>Python · Flask · SQLAlchemy · JavaScript · HTML · CSS</strong></p>
  <p>
    <a href="#sobre-o-projeto">Sobre</a> ·
    <a href="#estado-atual">Estado atual</a> ·
    <a href="#funcionalidades">Funcionalidades</a> ·
    <a href="#o-que-falta">Pendências</a> ·
    <a href="#como-executar">Executar</a> ·
    <a href="#testes">Testes</a>
  </p>
</div>

---

## Sobre o projeto

A **BOOSTio** ajuda a escolher componentes de um computador de acordo com objetivo,
orçamento e peças que o usuário já possui. A proposta reúne montagem manual,
formulário inteligente, comparação de configurações, consulta de preços e expectativa
de desempenho em jogos.

Este é meu projeto de software anual e final do curso no **Colégio Cotemig**, em
desenvolvimento ativo. A [página Sobre nós](frontend/pages/sobre.html) apresenta a
proposta da plataforma.

> **EN:** BOOSTio is a PC-building platform developed as my annual final course
> project at Colégio Cotemig. Authentication and expected gaming performance are
> connected to the Flask backend, alongside account-based build management and budget.
> LLM generation and KaBuM price collection are implemented. Most stored prices come
> from KaBuM; other marketplaces are available through product search links.
> Complete compatibility, scheduled price monitoring and production validation are
> still in progress. Blender rendering performance is planned alongside gaming estimates.

## Estado atual

**A `main` já trouxe builds persistidas por conta.** Os fluxos antigos de rascunho
local continuam existindo; não equivalem ao salvamento no servidor.

- **Integrado ao backend:** autenticação, budget, catálogo das montagens da conta,
  criação/edição/exclusão/duplicação de builds, setup atual, visibilidade e link público.
  O editor salva alterações da build da conta pelo Python; comparação, importação e
  sugestões de melhorias utilizam essas configurações. Benchmark segue pela FPSHQ.
- **Implementado, dependente de configuração:** geração pelo formulário via LLM e
  coleta de preços da KaBuM por comandos. Chaves, cotas e rede precisam ser configuradas;
  esta revisão de interface não fez chamadas pagas de geração nem coleta real de preços.
- **A concluir:** compatibilidade física definitiva no Python, requisitos de jogos/RAM,
  monitoramento agendado dos preços da KaBuM, curadoria de modelos e validação completa dos
  fluxos da LLM e migração consentida das builds antigas do navegador.

**Limite por conta:** até três builds, conferido pelo Python para montagem manual,
geração, importação, cópia de modelo e duplicação. A escrita é serializada no banco
para duas criações simultâneas não ocuparem a mesma vaga. Configurações antigas
que já ultrapassaram o limite são preservadas; novas criações ficam bloqueadas.

### Catálogo e dados

O catálogo atual é carregado de
[`catalogo-demo.json`](frontend/data/catalogo-demo.json). O arquivo reúne as peças já
coletadas para o projeto; o nome do arquivo não significa que seja necessário
refazer a raspagem ou recriar o catálogo.

A montagem da conta usa `/build/catalogo`; modelos demonstrativos e fluxos legados
ainda usam o JSON. É necessário alinhar seus identificadores sem refazer a coleta.
**Catálogo existente e monitoramento de preços são coisas diferentes:**
ter uma peça cadastrada não confirma que seu preço e estoque estejam atualizados
no momento da consulta.

**A maioria dos preços cadastrados tem origem na KaBuM.** Quando o anúncio está
vinculado, o link leva à página do produto exato na KaBuM, usada para consultar sua
oferta. Pichau e Mercado Livre permanecem como alternativas de **busca pelo modelo**,
para o usuário pesquisar outras condições de compra; esses links não representam
preços coletados nem anúncios equivalentes já confirmados nessas lojas.
O preço exibido é o valor registrado na coleta, não uma garantia de cotação em tempo real.

## Funcionalidades

Os **20 requisitos do produto** estão preservados abaixo.

- **Implementado:** código e integração do fluxo descrito disponíveis; pendências
  específicas continuam indicadas, sem significar homologação em produção.
- **Local:** funciona neste navegador, sem persistência na conta.
- **Parcial:** possui implementação, mas ainda depende das etapas descritas.

| Nº | Funcionalidade | Estado atual |
| --- | --- | --- |
| 1 | Criar conta e fazer login | **Implementado.** Cadastro, login, logout e sessão. |
| 2 | Cadastrar o setup atual | **Implementado.** Definir/remover setup atual na conta; peças próprias identificadas no editor. |
| 3 | Pesquisar peças e compatibilidade | **Parcial.** Catálogo da conta conectado; compatibilidade técnica ainda exige validação definitiva no Python. |
| 4 | Montar o setup por formulário | **Parcial.** Geração pela LLM implementada e salva na conta; validar chave/cotas, contexto completo e compatibilidade do resultado. |
| 5 | Salvar configurações | **Implementado.** Builds e rascunhos incompletos salvos na conta, com limite de três; falta migração consentida dos dados locais antigos. |
| 6 | Excluir configurações salvas | **Implementado.** Exclusão autenticada, com verificação de dono e tranca. |
| 7 | Comparar configurações salvas | **Parcial.** Comparador usa builds da conta; falta comparar desempenho medido nas mesmas condições. |
| 8 | Compartilhar configurações por link | **Implementado.** URL por ID e leitura pública condicionada à visibilidade; links legados continuam sendo cópias independentes. |
| 9 | Buscar melhorias do setup | **Parcial.** Trocas de CPU/GPU podem ser salvas na conta; faltam ganhos comprovados, ofertas atuais e dados de vendas. |
| 10 | Ver configurações prontas | **Parcial.** Vitrine e cópia para a conta; faltam curadoria no servidor, mapeamento completo e ofertas atualizadas. |
| 11 | Editar configurações salvas | **Implementado.** Editor salva componentes e detalhes na conta, respeitando a tranca. |
| 12 | Consultar preços das peças pelo site | **Implementado.** Consulta dos valores cadastrados, majoritariamente da KaBuM, com link do produto quando vinculado; outras lojas por busca. Agendamento e apresentação da origem/data ainda precisam de consolidação. |
| 13 | Ver compatibilidade e consumo de energia | **Parcial.** Validações e consumo estimado; faltam revalidação em Python e encaixe físico completo do gabinete. |
| 14 | Incluir periféricos no setup e no orçamento | **Parcial.** Reserva percentual opcional no formulário, validada na geração pelo Python; cabos/adaptadores ainda precisam de produtos no catálogo. |
| 15 | Registrar budget no perfil | **Implementado.** Valor/autorização persistidos e formulário preenchido; alinhar o valor inicial da criação manual da conta. |
| 16 | Baixar a build em JSON e CSV | **Implementado.** Arquivos gerados no navegador a partir das builds da conta; formato versionado. |
| 17 | Alterar a visibilidade da build | **Implementado.** Estado persistido e conferido na leitura pública pelo servidor. |
| 18 | Duplicar a build | **Implementado.** Cópia independente na conta, respeitando o limite de três. |
| 19 | Definir nome e descrição | **Implementado.** Edição e validação de limites no Python. |
| 20 | Importar builds em CSV ou JSON | **Implementado.** Prévia/validação no frontend e criação na conta com IDs e quantidades conferidos no servidor. |

### Desempenho esperado em jogos

O botão **Testar build** está no editor e no menu dos cards. O frontend libera o
modal quando as peças obrigatórias estão preenchidas e não há erros de compatibilidade.

- O modal usa o backend autenticado, com jogo, resolução e qualidade gráfica.
- O Python consulta a FPSHQ, confirma os identificadores retornados e trata cache,
  limites, ausência de dados, falhas e timeout.
- São exibidos FPS médio e 1% low quando disponíveis. **Comparar ajustes** utiliza
  a matriz recebida, sem uma nova consulta ao trocar a qualidade da comparação.
- Modelos sem correspondência cadastrada não são substituídos por peças parecidas.
- Falhas de conexão/TLS, timeout e indisponibilidade do provedor têm códigos próprios
  e uma pausa com `Retry-After`; resultados válidos em cache continuam acessíveis.
  Não há repetição automática nem FPS inventado como alternativa a uma falha.

Na consulta externa de 20/10/2026, a conexão/TLS foi concluída, mas não houve resposta
HTTP dentro de 25 segundos. O tratamento foi testado; isso **não comprova que a
disponibilidade da FPSHQ foi restabelecida**. Documentação: [API pública FPSHQ](https://fpshq.com/pt/api/).

**Não é um benchmark executado na máquina nem uma aprovação dos requisitos do jogo.**
RAM e requisitos mínimos/recomendados ainda precisam de verificação separada. O
mapeamento de hardware permanece parcialmente no frontend; as builds da conta já são persistidas.

O cache dura uma hora, fica em memória e é compartilhado apenas dentro do mesmo
processo. Antes de usar múltiplos workers, cache e limites precisarão de armazenamento
compartilhado. A fonte e a licença dos dados permanecem visíveis na interface.

### Desempenho em renderização — planejado

O escopo de desempenho fica em **jogos com FPSHQ** e **renderização com Blender Open
Data**. A integração com o Blender ainda não foi implementada. Deve apresentar
resultados comparáveis por CPU/GPU, versão do Blender e método de renderização,
sem converter a pontuação em tempo garantido para qualquer projeto. Benchmarks de
editores de vídeo e imagem ficam fora do escopo atual.

### Budget da conta

O valor e a opção **Usar este budget nas novas configurações** são salvos no Python,
por usuário, e retornados em `/auth/me`. A alteração usa `PUT /usuarios/<id>/budget`,
com sessão e verificação de propriedade. São aceitos valores de R$ 0 até R$ 1.000.000,
com até dois decimais; deixar o campo vazio remove o valor. A autorização exige valor
positivo. O orçamento de cada build é independente e não há desconto automático.

O antigo budget local não é importado automaticamente para nenhuma conta. Entre e
salve o valor nas configurações para sincronizá-lo entre dispositivos. As builds e a
escolha de setup atual da conta são persistidas; os modos legados continuam locais.

No formulário, os atalhos indicam **Até R$ 3.000 / 5.000 / 8.000**. O slider varia
de R$ 100 em R$ 100, com campo para digitar um valor exato, incluindo centavos.
A opção de reservar orçamento para monitor, teclado, mouse e headset aceita de 1%
a 99% do **mesmo total**. Por exemplo: R$ 5.000 com 20% reserva R$ 1.000 para
periféricos e R$ 4.000 para o PC; a geração rejeita resultados que excedam qualquer
parcela. Sem a opção, o total fica para o PC. Catálogo insuficiente gera orientação,
não componentes inventados. A reserva também é preservada no estado da build.

Durante a geração, frases rotativas tornam a espera mais clara. Elas não representam
etapas ou progresso real informado pela LLM. Falhas permitem tentar novamente ou
revisar o orçamento sem perder as respostas.

### Compra e lojas

**Comprar build** existe apenas dentro do editor: reúne quantidades, links e preços
cadastrados, sem checkout e sem abrir várias abas automaticamente. A referência de
preço vem majoritariamente da KaBuM; os links de busca nos outros marketplaces são
opções para o usuário pesquisar, não uma comparação automática de cotações.

A BOOSTio **não vende, entrega ou processa pagamentos** de peças e periféricos.
A compra e o atendimento acontecem no site da loja. Preço, estoque, frete, garantia
e devolução devem ser conferidos diretamente com o vendedor.

## O que falta

### 1. Consolidar a integração das builds

- Cobrir o CRUD já implementado com testes de propriedade, tranca, visibilidade,
  múltiplos componentes e conflitos de salvamento. Quota e criação concorrente já têm testes.
- Validar os casos-limite de orçamento e planejamento de rede, sem confiar nos dados do cliente.
- Migrar dados locais com confirmação, alinhar IDs e manter o salvamento automático seguro.
- Aplicar o budget autorizado do perfil na criação manual, hoje iniciada com orçamento vazio.
- Completar identificação das peças próprias e suporte a categorias ainda ausentes
  no banco (como webcam/microfone); o formulário já encaminha os tipos suportados e rede ao editor.

### 2. Completar compatibilidade e encaixe físico

- Revalidar no Python as regras já existentes no frontend.
- Conferir limites internos do gabinete: GPU, altura do air cooler, formato da
  placa-mãe, fonte e baias de discos.
- Verificar radiador + fans por posição, incluindo interferências com GPU e RAM,
  encaixes compartilhados e fans inclusas que serão mantidas ou substituídas.
- Completar apenas medidas ausentes, preservando os dados coletados. **Medida
  desconhecida não confirma encaixe e não deve ser tratada como zero.**

### 3. Completar dados e integrações

- Alinhar catálogo JSON, banco e identificadores das peças, incluindo arquivos importados.
- Consolidar o agendamento da coleta da KaBuM, estoque e data da última atualização.
- Apresentar a origem do preço na interface, corrigir rótulos antigos de preço
  demonstrativo nos fluxos da conta e distinguir anúncio exato de busca em outra loja.
  Não reproduzir o preço da KaBuM como se fosse uma cotação de Pichau ou Mercado Livre.
- Levar a identificação de hardware do benchmark para o backend e ampliar sua cobertura.
- Validar novamente a consulta real à FPSHQ com o backend operacional, distinguindo
  falha local de inicialização, sessão e indisponibilidade externa.
- Integrar dados do Blender Open Data para desempenho em renderização, com
  correspondência de componentes e agrupamento de resultados comparáveis.
- Verificar requisitos dos jogos e RAM, distinguindo incompatibilidade, ausência de
  dados e falha do provedor.
- Alimentar comparações e melhorias com desempenho sob as mesmas condições; obter
  dados confiáveis para o critério **Mais vendida nas lojas**.
- Validar a geração pela LLM já implementada e ampliar contexto, tratamento de falhas
  e revalidação técnica das sugestões no Python.

### 4. Fechar compartilhamento e acesso

- Testar os links persistentes e a revogação já implementados, incluindo cópias legadas e cache.
- Definir se visitantes poderão consultar builds públicas sem login.
- Exigir sessão nas operações privadas de montagem e gestão, preservando os fluxos
  públicos de conta, recuperação de senha, termos e sobre.
- Integrar a curadoria das builds prontas e completar os acessórios de rede no catálogo.

A consulta individual de desempenho e o CRUD da conta já estão implementados; as
pendências acima são de consolidação, não de reescrever essas integrações.

### 5. Refinar a experiência de montagem

- Completar imagens das peças, preservando a identificação quando não houver foto.
- Priorizar dois pentes de RAM quando orçamento, kits e slots permitirem.
- Perguntar a preferência entre custo-benefício e desempenho, mantendo o orçamento.
- Orientar quem começa do zero a considerar todos os itens necessários e informar
  também os periféricos que já possui.
- Completar testes de ponta a ponta de formulário → geração → editor → conta,
  incluindo falhas, nova tentativa e salvamentos concorrentes.

## Como executar

### Backend

Na raiz do repositório, crie e ative um ambiente virtual Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows, ative com `.venv\Scripts\activate` em vez de `source`.

Configure um `.env` local, que não deve ser versionado. Exemplo mínimo de desenvolvimento:

```dotenv
APP_ENV=desenvolvimento
SECRET_KEY=substitua-por-uma-chave-local-segura
URL_DATABASE=sqlite:///../database/banco.db
FRONTEND_URL=http://127.0.0.1:5500/frontend
```

Os fluxos de e-mail usam `MAIL_USERNAME` e `MAIL_PASSWORD`; login com Google usa
`GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`. Configure esses valores apenas no ambiente,
sem publicar credenciais. As opções estão em [`backend/configs.py`](backend/configs.py).

Para **SQLite já existente**, pare o servidor e execute uma vez antes de iniciar:

```bash
cd backend
python -m flask --app app migrar-budget
```

O comando cria um backup `.antes-budget-*.db` ao lado do banco, adiciona apenas as
colunas ausentes e não altera os cadastros. Também cobre bancos antigos sem
`login_google`. Pode ser repetido sem duplicar campos ou apagar budgets. Os backups
contêm dados privados: ficam ignorados pelo Git e devem ser protegidos como o banco.
Em uma instalação nova, `app.py` já cria as colunas; não execute a migração antes de
existir uma tabela de usuários.

Com o ambiente virtual ativo, inicie a partir de `backend/`:

```bash
python app.py
```

O backend atende em `http://127.0.0.1:5000`. Ao iniciar por `app.py`, ele cria as
tabelas ausentes e executa o cadastro inicial das peças. **A atualização automática
de preços permanece pausada.**

Para repor os links conhecidos em um banco já populado e consultar preços reais:

```bash
python -m flask --app app pecas-restaurar-links
python -m flask --app app precos-atualizar
```

O primeiro comando preserva links já cadastrados. O segundo pode ser executado
diariamente; registra preço e estoque apenas quando a loja fornece uma oferta
válida. Peças sem cotação continuam fora das sugestões de builds.

### Frontend

Sirva a raiz do projeto com o **Live Server** do VS Code, na porta `5500`:

- Início: `http://127.0.0.1:5500/frontend/pages/index.html`.
- Laboratório: `http://127.0.0.1:5500/frontend/testes.html`.

Use o mesmo host `127.0.0.1` durante o teste para manter o fluxo de sessão consistente.
O frontend usa HTML, CSS e JavaScript com ES Modules, sem etapa de build. A URL do
backend fica em [`frontend/js/config.js`](frontend/js/config.js).

## Testes

Os testes verificam regras de montagem, arquivos de build, estados da interface e
serviços do backend. Não são benchmarks executados no computador do usuário.

**Frontend — na raiz, com Node.js instalado:**

```bash
node --test frontend/tests/*.test.mjs
```

**Backend — com o ambiente virtual ativado:**

```bash
python -m pip install pytest pytest-mock
cd backend
python -m pytest
```

Os cenários automatizados de benchmark usam respostas controladas para não depender
da disponibilidade do provedor nem consumir suas cotas durante a execução dos testes.
Os testes de budget usam SQLite temporário e verificam autorização, centavos,
separação entre contas, remoção, persistência entre sessões e migração com backup.
Os de criação verificam quota em todos os caminhos, disputa pela última vaga,
preservação de contas acima do limite, reserva de periféricos e persistência atômica
da geração com respostas simuladas, sem chamar uma LLM paga.

A revisão de qualidade cobre as 16 telas, incluindo teclado, modais, metadados,
movimento reduzido e testes de regressão. Consulte os resultados e limites da
[auditoria local de Lighthouse](docs/qualidade-frontend.md). Páginas privadas usam
`noindex` intencional: pontuação SEO não deve prevalecer sobre essa política.

## Organização do projeto

- [`backend/controllers/`](backend/controllers/): rotas HTTP e autenticação das operações.
- [`backend/services/`](backend/services/): regras de negócio e integrações externas.
- [`backend/models/`](backend/models/): modelos e acesso aos dados com SQLAlchemy.
- [`frontend/pages/`](frontend/pages/): páginas da plataforma.
- [`frontend/js/`](frontend/js/): interface, estado das builds e clientes HTTP.
- [`frontend/styles/`](frontend/styles/): identidade visual, componentes e responsividade.
- [`frontend/data/`](frontend/data/): catálogo JSON usado atualmente pelo frontend.
- [`frontend/tests/`](frontend/tests/) e [`backend/tests/`](backend/tests/): testes automatizados.
- [`docs/frontend-build.md`](docs/frontend-build.md): contratos e decisões técnicas do editor.

O backend segue **controllers → services → models**; integrações externas são
encapsuladas em serviços. O frontend usa JavaScript vanilla, Lexend para títulos,
Poppins para textos e Lottie para animações de interface.

As pendências detalhadas ficam também em `docs/pendencias-produto.md`, mantido
localmente e ignorado pelo Git. Ao concluir uma etapa, atualizar este README e esse
controle sem marcar uma implementação local como integração concluída.
