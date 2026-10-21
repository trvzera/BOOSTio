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
> connected to the Flask backend. Most build-management features currently use
> browser storage; account persistence, live offers and LLM integration are pending.

## Estado atual

**A interface já cobre boa parte do produto; a integração das builds com a conta
ainda está em desenvolvimento.** Uma função local não deve ser confundida com uma
função persistida e autorizada no servidor.

- **Integrado ao backend:** cadastro, login, logout, sessão, budget por conta e consulta de desempenho
  esperado pela FPSHQ. O fluxo de conta também possui login com Google, verificação
  de e-mail e recuperação de senha, conforme a configuração dos serviços.
- **Disponível no navegador:** editor manual, formulário, builds salvas localmente,
  comparação, sugestões de melhorias, configurações prontas, importação e
  exportação. Esses dados ainda não acompanham o usuário entre dispositivos.
- **A concluir:** persistência das builds e preferências por conta, autorização das
  operações, validações definitivas em Python, ofertas atualizadas e montagem pela LLM.

### Catálogo e dados

O catálogo atual é carregado de
[`catalogo-demo.json`](frontend/data/catalogo-demo.json). O arquivo reúne as peças já
coletadas para o projeto; o nome do arquivo não significa que seja necessário
refazer a raspagem ou recriar o catálogo.

A integração futura deve preservar esses dados e alinhar seus identificadores com
o banco. **Catálogo existente e monitoramento de preços são coisas diferentes:**
ter uma peça cadastrada não confirma que o preço, o estoque ou a oferta de cada loja
estejam atualizados. As referências de preço ainda não são cotações em tempo real.

## Funcionalidades

Os **20 requisitos do produto** estão preservados abaixo.

- **Conectado:** usa o backend no fluxo indicado.
- **Local:** funciona neste navegador, sem persistência na conta.
- **Parcial:** possui implementação, mas ainda depende das etapas descritas.

| Nº | Funcionalidade | Estado atual |
| --- | --- | --- |
| 1 | Criar conta e fazer login | **Conectado.** Cadastro, login, logout e sessão. |
| 2 | Cadastrar o setup atual | **Local.** Peças próprias e definição de uma build como setup atual; falta persistir na conta. |
| 3 | Pesquisar peças e compatibilidade | **Parcial.** Catálogo e validações no frontend; falta integrar a fonte ao backend e revalidar no servidor. |
| 4 | Montar o setup por formulário | **Parcial.** Objetivo, orçamento, peças existentes e conexão chegam ao editor; falta a sugestão pela LLM. |
| 5 | Salvar configurações | **Local.** Salvamento automático e até três builds; falta sincronização com a conta. |
| 6 | Excluir configurações salvas | **Local.** Exclusão das builds do navegador, respeitando a tranca. |
| 7 | Comparar configurações salvas | **Local.** Comparação de duas ou três builds; falta alimentar o desempenho com benchmarks equivalentes e integrar a conta. |
| 8 | Compartilhar configurações por link | **Parcial.** Link com cópia dos dados; faltam URL persistente, autorização e revogação pelo servidor. |
| 9 | Buscar melhorias do setup | **Parcial.** Prévia e aplicação local de trocas de CPU/GPU; faltam ganhos comprovados e dados de vendas. |
| 10 | Ver configurações prontas | **Local.** Filtros, detalhes e cópia editável; faltam curadoria no servidor e ofertas atualizadas. |
| 11 | Editar configurações salvas | **Local.** Componentes e detalhes editáveis no navegador. |
| 12 | Consultar preços das peças pelo site | **Parcial.** Preços cadastrados e links por loja; falta monitoramento atualizado de todas as ofertas. |
| 13 | Ver compatibilidade e consumo de energia | **Parcial.** Validações e consumo estimado; faltam revalidação em Python e encaixe físico completo do gabinete. |
| 14 | Incluir periféricos no setup e no orçamento | **Parcial.** Periféricos entram no total; rede tem planejamento próprio, mas cabos/adaptadores ainda precisam de produtos no catálogo. |
| 15 | Registrar budget no perfil | **Integrado.** Valor e autorização salvos na conta; preenche novas montagens sem alterar o orçamento das builds existentes. |
| 16 | Baixar a build em JSON e CSV | **Local.** Exportação versionada com componentes, quantidades, peças próprias e metadados. |
| 17 | Alterar a visibilidade da build | **Local.** Alternância pública/privada; falta controle de acesso efetivo no servidor. |
| 18 | Duplicar a build | **Local.** Cópia independente, privada e editável, respeitando a quota local. |
| 19 | Definir nome e descrição | **Local.** Edição e salvamento no navegador. |
| 20 | Importar builds em CSV ou JSON | **Local.** Validação, prévia e nova cópia dentro da quota; falta revalidar na integração com a conta. |

### Desempenho esperado em jogos

O botão **Testar build** está no editor e no menu dos cards. O frontend libera o
modal quando as peças obrigatórias estão preenchidas e não há erros de compatibilidade.

- O modal usa o backend autenticado, com jogo, resolução e qualidade gráfica.
- O Python consulta a FPSHQ, confirma os identificadores retornados e trata cache,
  limites, ausência de dados, falhas e timeout.
- São exibidos FPS médio e 1% low quando disponíveis. **Comparar ajustes** utiliza
  a matriz recebida, sem uma nova consulta ao trocar a qualidade da comparação.
- Modelos sem correspondência cadastrada não são substituídos por peças parecidas.

**Não é um benchmark executado na máquina nem uma aprovação dos requisitos do jogo.**
RAM e requisitos mínimos/recomendados ainda precisam de verificação separada. O
mapeamento de hardware permanece parcialmente no frontend; as builds ainda são locais.

O cache atualizado dura uma hora. Se a FPSHQ não responder, uma consulta anterior
da mesma combinação pode ser exibida por até 24 horas, com a data original indicada.
O cache fica em memória e é compartilhado apenas dentro do mesmo processo. Antes de
usar múltiplos workers, cache e limites precisarão de armazenamento compartilhado.
A fonte e a licença dos dados permanecem visíveis na interface.

### Budget da conta

O valor e a opção **Usar este budget nas novas configurações** são salvos no Python,
por usuário, e retornados em `/auth/me`. A alteração usa `PUT /usuarios/<id>/budget`,
com sessão e verificação de propriedade. São aceitos valores de R$ 0 até R$ 1.000.000,
com até dois decimais; deixar o campo vazio remove o valor. A autorização exige valor
positivo. O orçamento de cada build é independente e não há desconto automático.

O antigo budget local não é importado automaticamente para nenhuma conta. Entre e
salve o valor nas configurações para sincronizá-lo entre dispositivos. As builds e a
escolha de setup atual continuam locais.

### Compra e lojas

**Comprar build** existe apenas dentro do editor: reúne quantidades, links e preços
cadastrados por loja, sem checkout e sem abrir várias abas automaticamente.

A BOOSTio **não vende, entrega ou processa pagamentos** de peças e periféricos.
A compra e o atendimento acontecem no site da loja. Preço, estoque, frete, garantia
e devolução devem ser conferidos diretamente com o vendedor.

## O que falta

### 1. Integrar as builds à conta

- Revisar os modelos e contratos para rascunhos incompletos e múltiplos modelos de
  RAM, SSD, HD e fans, sem perder as seleções que o editor já permite.
- Criar operações de cadastro, listagem, atualização e exclusão de builds por usuário.
- Persistir setup atual, orçamento por build, descrição, visibilidade, tranca e planejamento de rede.
- Validar no servidor proprietário, quota, quantidades e ações permitidas pela tranca.
- Migrar dados locais com confirmação e manter o salvamento automático seguro.

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
- Finalizar monitoramento de ofertas, estoque e data de atualização por loja.
- Levar a identificação de hardware do benchmark para o backend e ampliar sua cobertura.
- Verificar requisitos dos jogos e RAM, distinguindo incompatibilidade, ausência de
  dados e falha do provedor.
- Alimentar comparações e melhorias com desempenho sob as mesmas condições; obter
  dados confiáveis para o critério **Mais vendida nas lojas**.
- Integrar a LLM usando IDs reais do catálogo e revalidar suas sugestões no Python.

### 4. Fechar compartilhamento e acesso

- Criar links persistentes, com autorização e revogação ao tornar uma build privada.
- Definir se visitantes poderão consultar builds públicas sem login.
- Exigir sessão nas operações privadas de montagem e gestão, preservando os fluxos
  públicos de conta, recuperação de senha, termos e sobre.
- Integrar a curadoria das builds prontas e completar os acessórios de rede no catálogo.

A consulta individual de desempenho já está integrada; as pendências acima não
significam que seja preciso refazê-la. O próximo passo recomendado é preparar os
modelos/contratos e a persistência das builds, em coordenação com o catálogo e preços.

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

Para baixar a foto principal dos anúncios cadastrados, execute uma vez (ou retome
após uma interrupção):

```bash
python -m flask --app app pecas-imagens
```

O comando ignora peças que já têm foto, verifica o código do anúncio e salva os
arquivos em `frontend/imgs/produtos`. Use `--limite 20` para um teste pequeno ou
`--categoria monitor` para uma categoria. A migração da coluna `imagem_url` roda
automaticamente na inicialização do backend.

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
